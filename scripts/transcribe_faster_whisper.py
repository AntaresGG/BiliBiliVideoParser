"""Transcribe media with faster-whisper and optionally enrich a normalized model.

Examples:
    python transcribe_faster_whisper.py audio.m4a --json transcript.json
    python transcribe_faster_whisper.py audio.m4a --model-json source.json --model-out enriched.json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


def format_srt_time(seconds: float) -> str:
    millis = max(0, round(seconds * 1000))
    hours, remainder = divmod(millis, 3_600_000)
    minutes, remainder = divmod(remainder, 60_000)
    secs, millis = divmod(remainder, 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"


def choose_runtime(requested_device: str, requested_compute_type: str | None) -> tuple[str, str]:
    device = "cpu" if requested_device == "auto" else requested_device
    compute_type = requested_compute_type or ("float16" if device == "cuda" else "int8")
    return device, compute_type


def update_model(
    source_path: Path,
    output_path: Path,
    segments: list[dict[str, Any]],
    language: str,
    probability: float,
) -> None:
    model = json.loads(source_path.read_text(encoding="utf-8"))
    if model.get("schema_version") != "1.0":
        raise ValueError("Expected source model schema_version 1.0.")
    model["content"] = {
        "source_type": "asr",
        "language": language,
        "language_probability": round(probability, 4),
        "segments": segments,
        "transcript": "\n".join(item["text"] for item in segments),
    }
    duration = model.get("metadata", {}).get("duration_seconds") or 0
    coverage_seconds = segments[-1]["end"] - segments[0]["start"] if segments else 0
    model["source_status"] = {
        "content_source": "asr",
        "segment_count": len(segments),
        "coverage_seconds": round(coverage_seconds, 3),
        "coverage_ratio": round(min(1.0, coverage_seconds / duration), 4) if duration else None,
        "confidence": "medium",
    }
    diagnostics = model.setdefault("diagnostics", {})
    warnings = diagnostics.setdefault("warnings", [])
    warnings[:] = [warning for warning in warnings if not warning.startswith("No accessible subtitle text")]
    warnings.append("ASR transcript may contain errors in names, numbers, tickers, jargon, or dialect speech.")
    output_path.write_text(json.dumps(model, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("media", type=Path, help="Audio or video file")
    parser.add_argument("--txt", type=Path, help="Optional timestamped TXT output")
    parser.add_argument("--srt", type=Path, help="Optional SRT output")
    parser.add_argument("--json", type=Path, help="Optional structured transcript JSON output")
    parser.add_argument("--model-json", type=Path, help="Optional normalized source model to enrich")
    parser.add_argument("--model-out", type=Path, help="Output path for the enriched normalized model")
    parser.add_argument("--model", default="small", help="Whisper model size/name")
    parser.add_argument("--language", default="zh", help="Language code or 'auto'")
    parser.add_argument(
        "--device",
        choices=("auto", "cpu", "cuda"),
        default="cpu",
        help="Stable CPU default; choose CUDA explicitly when its runtime libraries are installed",
    )
    parser.add_argument("--compute-type", help="Override faster-whisper compute type")
    parser.add_argument("--beam-size", type=int, default=5)
    args = parser.parse_args()

    if args.model_json and not args.model_out:
        parser.error("--model-out is required with --model-json")
    if args.model_out and not args.model_json:
        parser.error("--model-json is required with --model-out")
    if not args.media.is_file():
        print(
            json.dumps({"ok": False, "stage": "input", "message": f"Media file not found: {args.media}"}),
            file=sys.stderr,
        )
        return 1

    try:
        from faster_whisper import WhisperModel

        device, compute_type = choose_runtime(args.device, args.compute_type)
        whisper = WhisperModel(args.model, device=device, compute_type=compute_type)
        generated, info = whisper.transcribe(
            str(args.media),
            language=None if args.language == "auto" else args.language,
            beam_size=args.beam_size,
            vad_filter=True,
            vad_parameters={"min_silence_duration_ms": 500},
        )

        segments: list[dict[str, Any]] = []
        for item in generated:
            text = item.text.strip()
            if text:
                segments.append(
                    {"start": round(item.start, 3), "end": round(item.end, 3), "text": text}
                )

        if args.txt:
            lines = [
                f"[{item['start']:.3f}-{item['end']:.3f}] {item['text']}" for item in segments
            ]
            args.txt.write_text("\n".join(lines) + "\n", encoding="utf-8")
        if args.srt:
            blocks = [
                f"{index}\n{format_srt_time(item['start'])} --> {format_srt_time(item['end'])}\n{item['text']}"
                for index, item in enumerate(segments, start=1)
            ]
            args.srt.write_text("\n\n".join(blocks) + "\n", encoding="utf-8")

        transcript = {
            "source_type": "asr",
            "language": info.language,
            "language_probability": round(info.language_probability, 4),
            "duration_seconds": round(info.duration, 3),
            "segments": segments,
            "transcript": "\n".join(item["text"] for item in segments),
        }
        if args.json:
            args.json.write_text(json.dumps(transcript, ensure_ascii=False, indent=2), encoding="utf-8")
        if args.model_json and args.model_out:
            update_model(
                args.model_json,
                args.model_out,
                segments,
                info.language,
                info.language_probability,
            )

        print(
            json.dumps(
                {
                    "ok": True,
                    "language": info.language,
                    "segments": len(segments),
                    "duration_seconds": round(info.duration, 3),
                    "device": device,
                    "compute_type": compute_type,
                }
            )
        )
        return 0
    except (ImportError, OSError, RuntimeError, TypeError, ValueError, json.JSONDecodeError) as exc:
        print(
            json.dumps({"ok": False, "stage": "asr", "message": str(exc)}, ensure_ascii=False),
            file=sys.stderr,
        )
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
