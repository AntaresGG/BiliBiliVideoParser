---
name: bilibili-video-parser
description: Parse and understand Bilibili videos with a Bilibili-native, evidence-aware workflow covering metadata, multi-part selection, official or AI subtitles, local ASR fallback, timestamped outlines, claim-evidence mapping, danmaku reception signals, summaries, and research synthesis. Use when the user provides a Bilibili URL, short link, BV/av/ep/ss identifier, or asks what a B站 video says, argues, teaches, or implies. Return analysis in chat by default; create Markdown, TXT, JSON, SRT, or standalone HTML only when explicitly requested.
---

# Bilibili Video Parser

## Product Principle

Turn a Bilibili video into a traceable content model, then into useful understanding. Optimize for content fidelity and Bilibili-specific context—not video downloading or decorative reports.

Use the signature **BiliLens** sequence: **来源卡 → 时间轴 → 论据链 → 互动场 → 洞察层**. Read `references/bililens-method.md` before producing `outline`, `summary`, `research`, or `full` analysis.

Never infer unavailable content from a title, description, comments, or general knowledge. Keep the speaker's claims, audience reaction, external facts, and Codex inference separate.

## Parameters

Infer parameters from natural language; do not require exact syntax.

```yaml
video: <Bilibili URL, short link, BV, av, ep, or ss ID>  # required
page: <linked/default part>                               # optional, 1-based
content_mode: summary                                    # metadata | transcript | cleaned_transcript | outline | summary | research | full
output_formats: []                                       # markdown | txt | json | srt | html
language: zh-CN
timestamps: true
detail: standard                                         # concise | standard | detailed
include_audience: false                                  # add danmaku reception signals
output_dir: <user path or current directory>             # only for requested files
theme: null                                              # HTML only
```

- Treat “导出 Markdown 和 TXT” as `output_formats: [markdown, txt]`.
- Return results in chat when `output_formats` is empty.
- Ask only when part selection, authentication, or output location would materially change the result.

## Workflow

### 1. Acquire A Normalized Source

Use the bundled extractor first:

```powershell
uv run --python 3.12 scripts/bilibili_extract.py "<VIDEO>" --out "<TEMP>\source.json"
```

Add `--page <N>`, `--subtitle-language <CODE>`, or `--include-danmaku` only when relevant. The extractor:

- resolves BV, av, `b23.tv`, ep, ss, full URLs, and linked `?p=` parts;
- records live metadata and engagement statistics with `fetched_at`;
- selects the requested part explicitly;
- prefers human subtitles over AI subtitles;
- downloads and normalizes accessible subtitle bodies;
- retries transient API/risk-control failures;
- optionally samples danmaku and detects 30-second attention hotspots;
- emits schema `1.0` JSON without leaking credentials.

Run `scripts/bilibili_extract.py --self-check` when endpoints may have drifted or extraction behaves unexpectedly.

### 2. Handle Authentication Deliberately

Anonymous extraction is the default. If subtitles are login-gated:

1. Explain that authentication may expose the user's local Bilibili session.
2. Ask before accessing browser cookies or environment credentials.
3. Prefer an already-installed `bilibili-cli` (`bili video ... --subtitle-timeline --json`) for browser-cookie or QR-login workflows.
4. Use bundled extraction with `--use-env-cookie` only when the user has deliberately configured `BILI_SESSDATA` and related variables.
5. Never print, persist, or request raw cookie values in chat.

Do not install `bilibili-cli` or another downloader unless it is necessary for the request. If installed, use `uv tool install "bilibili-cli[audio]"`.

### 3. Fall Back To Local ASR

When subtitle text is unavailable and content analysis is required:

1. Prefer `bili audio <VIDEO> --no-split -o <TEMP>` when `bilibili-cli[audio]` is available.
2. Otherwise use current `yt-dlp` with Bilibili Referer/User-Agent to download audio only.
3. Transcribe locally with `scripts/transcribe_faster_whisper.py` and merge into the normalized model:

```powershell
uv run --with faster-whisper --python 3.12 scripts/transcribe_faster_whisper.py "<AUDIO>" --model-json "<TEMP>\source.json" --model-out "<TEMP>\content.json"
```

Use a temporary workspace. Remove downloaded audio and intermediate files after delivery. State ASR risks for names, numbers, tickers, jargon, accents, and overlapping speech.

### 4. Apply BiliLens

Read `references/bililens-method.md`, then derive only the requested depth:

- `metadata`: 来源卡 and extraction status only.
- `transcript`: timestamped source text with minimal correction.
- `cleaned_transcript`: punctuation, paragraphs, and obvious corrections without semantic rewriting.
- `outline`: 来源卡 + timestamped 内容轴.
- `summary`: add thesis, key points, and representative evidence.
- `research`: add 论据链, implications, contradictions, uncertainties, and validation conditions.
- `full`: add transcript plus all BiliLens layers; include 互动场 only when audience data was acquired.

For finance or investment content, attribute forecasts to the speaker, preserve time horizons and conditions, separate facts from opinions, and add a brief non-advice disclaimer.

### 5. Render Requested Files

Populate the normalized model's optional `analysis` object, then render all requested formats from that single model:

```powershell
uv run --python 3.12 scripts/render_outputs.py "<TEMP>\content.json" --formats "markdown,txt" --out-dir "<OUTPUT_DIR>"
```

- `markdown`: structured BiliLens report with source and timestamps.
- `txt`: clean UTF-8 reading copy.
- `json`: normalized source plus analysis for downstream reuse.
- `srt`: timestamped transcript; fail clearly when timing is unavailable.
- `html`: standalone responsive reading report; generate only when requested.

Use one lowercase basename across parallel outputs. For QuantVista-themed investment HTML, also read `references/quantvista-report-style.md`. Do not add dashboards, API hooks, or interactions unless the user requests them.

## Quality Gate

Before delivery:

- confirm the canonical video and selected part;
- report content source as human subtitle, AI subtitle, ASR, or unavailable;
- ensure important claims trace to timestamps or labeled metadata/external sources;
- inspect the underlying segment before interpreting a danmaku hotspot;
- keep missing values missing rather than estimating them;
- validate requested files and ensure no unrequested outputs or temporary media remain.

## Defaults

- Use Chinese for analysis and reports; use English for logs and code output.
- Include timezone for converted timestamps and `fetched_at` for live statistics.
- Prefer a concise evidence chain over exhaustive recap.
- Treat HTML and all file generation as optional delivery layers.
