"""Render one normalized Bilibili content model into requested file formats.

Example:
    python render_outputs.py source.json --formats markdown,txt,json --out-dir ./output
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from html import escape
from pathlib import Path
from typing import Any

SUPPORTED_FORMATS = {"markdown", "txt", "json", "srt", "html"}


class RenderError(RuntimeError):
    pass


def load_model(path: Path) -> dict[str, Any]:
    try:
        model = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise RenderError(f"Could not read normalized JSON: {exc}") from exc
    if not isinstance(model, dict) or model.get("schema_version") != "1.0":
        raise RenderError("Expected a normalized Bilibili model with schema_version 1.0.")
    return model


def slugify(value: str) -> str:
    value = re.sub(r"[^0-9A-Za-z._-]+", "-", value.strip()).strip("-._").lower()
    return value or "bilibili-video"


def default_basename(model: dict[str, Any]) -> str:
    metadata = model.get("metadata", {})
    selection = model.get("selection", {})
    bvid = metadata.get("bvid") or "bilibili-video"
    page = selection.get("page")
    return slugify(f"{bvid}-p{page}" if page else str(bvid))


def format_time(seconds: float) -> str:
    total = max(0, int(seconds))
    hours, remainder = divmod(total, 3600)
    minutes, secs = divmod(remainder, 60)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}"


def format_srt_time(seconds: float) -> str:
    millis = max(0, round(seconds * 1000))
    hours, remainder = divmod(millis, 3_600_000)
    minutes, remainder = divmod(remainder, 60_000)
    secs, millis = divmod(remainder, 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"


def metadata_lines(model: dict[str, Any]) -> list[str]:
    metadata = model.get("metadata", {})
    source = model.get("source", {})
    uploader = metadata.get("uploader") or {}
    selection = model.get("selection", {})
    return [
        f"Title: {metadata.get('title') or 'Unavailable'}",
        f"BVID: {metadata.get('bvid') or 'Unavailable'}",
        f"Uploader: {uploader.get('name') or 'Unavailable'}",
        f"Part: P{selection.get('page') or 1} {selection.get('part_title') or ''}".rstrip(),
        f"URL: {source.get('canonical_url') or 'Unavailable'}",
        f"Fetched at: {source.get('fetched_at') or 'Unavailable'}",
        f"Content source: {model.get('content', {}).get('source_type') or 'none'}",
    ]


def analysis_sections(model: dict[str, Any]) -> list[tuple[str, Any]]:
    analysis = model.get("analysis")
    if not isinstance(analysis, dict):
        return []
    keys = [
        ("Executive Summary", "executive_summary"),
        ("Timeline Outline", "outline"),
        ("Key Claims and Evidence", "claims"),
        ("Audience Reception", "audience_reception"),
        ("Insights", "insights"),
        ("Uncertainties", "uncertainties"),
    ]
    return [(title, analysis[key]) for title, key in keys if analysis.get(key)]


def value_to_markdown(value: Any) -> str:
    if isinstance(value, str):
        return value
    if isinstance(value, list):
        lines = []
        for item in value:
            if isinstance(item, dict):
                text = item.get("text") or item.get("claim") or item.get("title") or json.dumps(item, ensure_ascii=False)
                timestamp = item.get("timestamp") or item.get("time_range")
                lines.append(f"- {f'[{timestamp}] ' if timestamp else ''}{text}")
            else:
                lines.append(f"- {item}")
        return "\n".join(lines)
    return f"```json\n{json.dumps(value, ensure_ascii=False, indent=2)}\n```"


def render_markdown(model: dict[str, Any]) -> str:
    title = model.get("metadata", {}).get("title") or "Bilibili Video"
    content = model.get("content", {})
    warnings = model.get("diagnostics", {}).get("warnings", [])
    parts = [f"# {title}", "", "## Source", ""]
    parts.extend(f"- {line}" for line in metadata_lines(model))
    for heading, value in analysis_sections(model):
        parts.extend(["", f"## {heading}", "", value_to_markdown(value)])
    if content.get("segments"):
        parts.extend(["", "## Transcript", ""])
        parts.extend(
            f"[{format_time(float(item.get('start', 0)))}] {item.get('text', '')}"
            for item in content["segments"]
        )
    if warnings:
        parts.extend(["", "## Extraction Notes", ""])
        parts.extend(f"- {warning}" for warning in warnings)
    return "\n".join(parts).rstrip() + "\n"


def render_txt(model: dict[str, Any]) -> str:
    title = model.get("metadata", {}).get("title") or "Bilibili Video"
    content = model.get("content", {})
    lines = [title, "=" * len(title), "", *metadata_lines(model)]
    for heading, value in analysis_sections(model):
        markdown = value_to_markdown(value)
        plain = re.sub(r"^[-*] ", "", markdown, flags=re.MULTILINE)
        lines.extend(["", heading.upper(), plain])
    if content.get("segments"):
        lines.extend(["", "TRANSCRIPT"])
        lines.extend(
            f"[{format_time(float(item.get('start', 0)))}] {item.get('text', '')}"
            for item in content["segments"]
        )
    return "\n".join(lines).rstrip() + "\n"


def render_srt(model: dict[str, Any]) -> str:
    segments = model.get("content", {}).get("segments", [])
    if not segments:
        raise RenderError("SRT output requires timestamped content.segments.")
    blocks = []
    for index, item in enumerate(segments, start=1):
        start = float(item.get("start", 0))
        end = float(item.get("end", start))
        blocks.append(
            f"{index}\n{format_srt_time(start)} --> {format_srt_time(end)}\n{item.get('text', '').strip()}"
        )
    return "\n\n".join(blocks) + "\n"


def render_html(model: dict[str, Any]) -> str:
    title = str(model.get("metadata", {}).get("title") or "Bilibili Video")
    source_items = "".join(f"<li>{escape(line)}</li>" for line in metadata_lines(model))
    sections = []
    for heading, value in analysis_sections(model):
        body = escape(value_to_markdown(value)).replace("\n", "<br>")
        sections.append(f"<section><h2>{escape(heading)}</h2><div>{body}</div></section>")
    segments = model.get("content", {}).get("segments", [])
    if segments:
        transcript = "".join(
            f"<p><time>{format_time(float(item.get('start', 0)))}</time> {escape(str(item.get('text', '')))}</p>"
            for item in segments
        )
        sections.append(f"<section><h2>Transcript</h2><div class=\"transcript\">{transcript}</div></section>")
    body = "".join(sections)
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{escape(title)}</title>
<style>
:root{{--bg:#f7f8fa;--surface:#fff;--ink:#18191c;--muted:#61666d;--accent:#fb7299;--line:#e3e5e7}}
*{{box-sizing:border-box}}body{{margin:0;background:var(--bg);color:var(--ink);font:16px/1.7 system-ui,sans-serif}}
main{{width:min(920px,calc(100% - 32px));margin:40px auto}}header,section{{background:var(--surface);border:1px solid var(--line);border-radius:14px;padding:24px;margin:16px 0}}
h1,h2{{line-height:1.25}}h1{{margin-top:0}}h2{{border-left:4px solid var(--accent);padding-left:10px}}
li,time{{color:var(--muted)}}time{{display:inline-block;min-width:74px;font-variant-numeric:tabular-nums}}
.brand{{color:var(--accent);font-weight:700;letter-spacing:.04em}}.transcript p{{margin:.55em 0}}
</style>
</head>
<body><main><header><div class="brand">BILILENS</div><h1>{escape(title)}</h1><ul>{source_items}</ul></header>{body}</main></body>
</html>
"""


def parse_formats(value: str) -> list[str]:
    formats = [item.strip().lower() for item in value.split(",") if item.strip()]
    invalid = [item for item in formats if item not in SUPPORTED_FORMATS]
    if invalid:
        raise RenderError(f"Unsupported formats: {', '.join(invalid)}")
    if not formats:
        raise RenderError("At least one output format is required.")
    return list(dict.fromkeys(formats))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("model", type=Path, help="Normalized schema_version 1.0 JSON")
    parser.add_argument("--formats", required=True, help="Comma-separated: markdown,txt,json,srt,html")
    parser.add_argument("--out-dir", type=Path, required=True)
    parser.add_argument("--basename", help="Optional shared output basename")
    args = parser.parse_args()
    try:
        model = load_model(args.model)
        formats = parse_formats(args.formats)
        args.out_dir.mkdir(parents=True, exist_ok=True)
        basename = slugify(args.basename) if args.basename else default_basename(model)
        renderers = {
            "markdown": ("md", render_markdown),
            "txt": ("txt", render_txt),
            "json": ("json", lambda value: json.dumps(value, ensure_ascii=False, indent=2) + "\n"),
            "srt": ("srt", render_srt),
            "html": ("html", render_html),
        }
        files = []
        for output_format in formats:
            extension, renderer = renderers[output_format]
            output_path = args.out_dir / f"{basename}.{extension}"
            output_path.write_text(renderer(model), encoding="utf-8")
            files.append(str(output_path.resolve()))
        print(json.dumps({"ok": True, "files": files}, ensure_ascii=False))
        return 0
    except (OSError, RenderError) as exc:
        print(
            json.dumps({"ok": False, "stage": "render", "message": str(exc)}, ensure_ascii=False),
            file=sys.stderr,
        )
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
