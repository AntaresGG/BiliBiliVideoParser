# BiliLens Method

Use this reference when transforming extracted Bilibili content into an outline, summary, research brief, or full analysis.

## Five Layers

Apply the five layers in order. Do not produce a later layer when its required evidence is missing.

1. **源｜Source** — Identify the exact video, part, acquisition method, language, timestamp coverage, authentication state, and extraction gaps.
2. **轴｜Timeline** — Reconstruct the video's progression into timestamped topics. Preserve the speaker's sequence rather than imposing a generic article structure.
3. **论｜Claims** — Extract key claims, supporting evidence, examples, numbers, named entities, qualifications, and counterarguments. Attach timestamps.
4. **场｜Reception** — Use danmaku or comments to locate audience attention, confusion, agreement, and disagreement. Treat reception as audience reaction, never as proof.
5. **见｜Insight** — Synthesize the thesis, implications, uncertainties, contradictions, follow-up questions, and—in research mode—validation or invalidation conditions.

The signature output order is therefore: **来源卡 → 时间轴 → 论据链 → 互动场 → 洞察层**.

## Evidence Labels

Label material internally or visibly when ambiguity matters:

- `VIDEO`: directly stated or shown in the acquired video content;
- `METADATA`: title, description, tags, uploader, publication time, or live statistics;
- `AUDIENCE`: danmaku or comments;
- `EXTERNAL`: separately researched supporting source;
- `INFERENCE`: Codex synthesis not explicitly stated in the video.

Never merge `AUDIENCE`, `EXTERNAL`, or `INFERENCE` into the speaker's claims.

## Analysis Contract

Add the following optional `analysis` object to the normalized extraction JSON before rendering files:

```json
{
  "executive_summary": "One concise thesis",
  "outline": [
    {"time_range": "00:00-03:20", "title": "Topic", "text": "What develops here"}
  ],
  "claims": [
    {
      "timestamp": "05:12",
      "claim": "Speaker's claim",
      "evidence": ["Supporting number or example"],
      "evidence_label": "VIDEO",
      "confidence": "high"
    }
  ],
  "audience_reception": [
    {"timestamp": "08:30", "text": "Observed reaction pattern", "evidence_label": "AUDIENCE"}
  ],
  "insights": ["Codex synthesis labeled as inference"],
  "uncertainties": ["Missing evidence, ambiguity, or ASR risk"]
}
```

Use `null` or omit a field when evidence is unavailable. Do not use placeholder claims.

## Quality Gate

Before presenting analysis, verify:

- each important claim has a timestamp or an explicit reason why timing is unavailable;
- numerical claims preserve units, dates, comparison bases, and uncertainty;
- the summary does not exceed what the transcript supports;
- ASR corrections do not silently alter meaning;
- danmaku hotspots are interpreted only after checking the corresponding video segment;
- external verification is cited separately and never attributed to the video.
