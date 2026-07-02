# Sensor Data Standards

## Purpose

Define how NIROS stores and interprets sensor information.

## Principles

1. Raw data and interpreted data must be separate.
2. Sensor source must be recorded.
3. Confidence must be explicit.
4. Missing data is acceptable.
5. Sensor signals are contextual, not diagnostic.

## Minimum schema

```json
{
  "source": "apple_watch|garmin|oura|polar|phone|manual|unknown",
  "timestamp_start": "ISO-8601",
  "timestamp_end": "ISO-8601",
  "signal_type": "hr|hrv|respiration|sleep|movement|eda|temperature",
  "raw_value": null,
  "unit": null,
  "quality": "low|medium|high",
  "interpretation": "string",
  "clinical_use_allowed": false
}
```

## MVP rule

The first MVP should support optional manual entry and one wearable integration later.
