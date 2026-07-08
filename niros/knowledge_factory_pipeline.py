"""Knowledge Factory Pipeline — orchestration for the Knowledge Factory MVP."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

from niros.ctpc import CanonicalTherapeuticPattern
from niros.ctpc_compiler import CTPCCompiler
from niros.human_review_workflow import HumanReviewRecord, HumanReviewWorkflow
from niros.knowledge_domain import KNOWLEDGE_DOMAIN_PSYCHOTHERAPY_TLE
from niros.knowledge_workspace import (
    DEFAULT_KNOWLEDGE_ROOT,
    KnowledgeWorkspacePaths,
    ensure_knowledge_workspace,
)
from niros.openai_semantic_extraction_adapter import (
    ChatCompletionClient,
    OpenAISemanticExtractionAdapter,
    SemanticExtractionResult,
)
from niros.pdf_importer import PDFImporter
from niros.raw_source import RawSourceCorpus
from niros.therapeutic_extraction import TherapeuticFunctionExtraction


@dataclass(frozen=True)
class KnowledgeFactoryPipelineResult:
    raw_source_corpus: RawSourceCorpus
    therapeutic_function_extraction: TherapeuticFunctionExtraction
    human_review_record: HumanReviewRecord
    canonical_therapeutic_pattern: CanonicalTherapeuticPattern


@dataclass
class KnowledgeFactoryPipeline:
    """Orchestrate PDF import, extraction, review, and CTPC compilation."""

    pdf_importer: PDFImporter
    extraction_adapter: OpenAISemanticExtractionAdapter
    review_workflow: HumanReviewWorkflow
    ctpc_compiler: CTPCCompiler

    @classmethod
    def from_workspace_root(
        cls,
        workspace_root: str = DEFAULT_KNOWLEDGE_ROOT,
        *,
        extraction_client: ChatCompletionClient | None = None,
        paths: KnowledgeWorkspacePaths | None = None,
        timestamp_fn: Callable[[], str] | None = None,
    ) -> KnowledgeFactoryPipeline:
        """Build a pipeline using the default Knowledge Factory workspace."""
        resolved_paths = paths or ensure_knowledge_workspace(workspace_root)
        return cls(
            pdf_importer=PDFImporter(),
            extraction_adapter=OpenAISemanticExtractionAdapter(client=extraction_client),
            review_workflow=HumanReviewWorkflow(
                paths=resolved_paths,
                timestamp_fn=timestamp_fn,
            ),
            ctpc_compiler=CTPCCompiler(paths=resolved_paths),
        )

    def import_pdf(
        self,
        pdf_path: str | Path,
        source_id: str,
        source_title: str,
        source_family: str | None = None,
        metadata: dict[str, Any] | None = None,
        *,
        language: str | None = None,
        source_type: str | None = None,
    ) -> RawSourceCorpus:
        """Import a PDF into a raw source corpus."""
        kwargs: dict[str, Any] = {}
        if language is not None:
            kwargs["language"] = language
        if source_type is not None:
            kwargs["source_type"] = source_type
        return self.pdf_importer.import_pdf(
            pdf_path,
            source_id,
            source_title,
            source_family=source_family,
            metadata=metadata,
            **kwargs,
        )

    def extract_from_corpus_gated(
        self,
        corpus: RawSourceCorpus,
        segment_id: str,
    ) -> SemanticExtractionResult:
        """Build a prompt and extract with a therapeutic relevance decision."""
        return self.extraction_adapter.extract_from_corpus_gated(corpus, segment_id)

    def extract_from_corpus(
        self,
        corpus: RawSourceCorpus,
        segment_id: str,
    ) -> TherapeuticFunctionExtraction:
        """Build a prompt and extract therapeutic mechanisms for one segment."""
        return self.extraction_adapter.extract_from_corpus(corpus, segment_id)

    def create_pending_review(
        self,
        extraction: TherapeuticFunctionExtraction,
        *,
        knowledge_domain: str | None = None,
    ) -> HumanReviewRecord:
        """Create a pending human review for one extraction proposal."""
        from niros.knowledge_domain import KNOWLEDGE_DOMAIN_UNKNOWN

        resolved_domain = (
            KNOWLEDGE_DOMAIN_UNKNOWN if knowledge_domain is None else knowledge_domain
        )
        return self.review_workflow.create_pending_review(
            extraction,
            knowledge_domain=resolved_domain,
        )

    def create_pending_consolidated_review(
        self,
        candidate: Any,
        *,
        knowledge_domain: str | None = None,
        therapeutic_relevance: dict[str, Any] | None = None,
    ) -> HumanReviewRecord:
        """Create a pending human review for one consolidated candidate pattern."""
        from niros.knowledge_domain import KNOWLEDGE_DOMAIN_UNKNOWN

        resolved_domain = (
            KNOWLEDGE_DOMAIN_UNKNOWN if knowledge_domain is None else knowledge_domain
        )
        return self.review_workflow.create_pending_consolidated_review(
            candidate,
            knowledge_domain=resolved_domain,
            therapeutic_relevance=therapeutic_relevance,
        )

    def approve_review(
        self,
        review_id: str,
        *,
        reviewer_id: str = "",
        reviewer_notes: str = "",
    ) -> HumanReviewRecord:
        """Approve one pending or changes-requested review."""
        return self.review_workflow.approve(
            review_id,
            reviewer_id=reviewer_id,
            reviewer_notes=reviewer_notes,
        )

    def compile_approved_review(
        self,
        review_record: HumanReviewRecord,
    ) -> CanonicalTherapeuticPattern:
        """Compile one approved review into a CTPC pattern artifact."""
        return self.ctpc_compiler.compile_review(review_record)

    def run_from_pdf(
        self,
        pdf_path: str | Path,
        source_id: str,
        source_title: str,
        *,
        segment_id: str | None = None,
        source_family: str | None = None,
        metadata: dict[str, Any] | None = None,
        language: str | None = None,
        source_type: str | None = None,
        reviewer_id: str = "",
        reviewer_notes: str = "",
        knowledge_domain: str = KNOWLEDGE_DOMAIN_PSYCHOTHERAPY_TLE,
    ) -> KnowledgeFactoryPipelineResult:
        """Run the full Knowledge Factory pipeline for one PDF segment."""
        corpus = self.import_pdf(
            pdf_path,
            source_id,
            source_title,
            source_family=source_family,
            metadata=metadata,
            language=language,
            source_type=source_type,
        )
        if not corpus.segments:
            raise ValueError("RawSourceCorpus contains no segments.")

        resolved_segment_id = segment_id or corpus.segments[0].segment_id
        extraction = self.extract_from_corpus(corpus, resolved_segment_id)
        pending_review = self.create_pending_review(
            extraction,
            knowledge_domain=knowledge_domain,
        )
        approved_review = self.approve_review(
            pending_review.review_id,
            reviewer_id=reviewer_id,
            reviewer_notes=reviewer_notes,
        )
        pattern = self.compile_approved_review(approved_review)
        return KnowledgeFactoryPipelineResult(
            raw_source_corpus=corpus,
            therapeutic_function_extraction=extraction,
            human_review_record=approved_review,
            canonical_therapeutic_pattern=pattern,
        )
