import json
import sys
import tempfile
import unittest
from pathlib import Path


SKILL_ROOT = (
    Path(__file__).resolve().parents[1]
    / "plugins"
    / "bilibili-video-parser"
    / "skills"
    / "bilibili-video-parser"
)
sys.path.insert(0, str(SKILL_ROOT / "scripts"))

import transcribe_faster_whisper  # noqa: E402


class RuntimeTests(unittest.TestCase):
    def test_uses_safe_cpu_default(self) -> None:
        self.assertEqual(transcribe_faster_whisper.choose_runtime("auto", None), ("cpu", "int8"))

    def test_uses_float16_for_explicit_cuda(self) -> None:
        self.assertEqual(
            transcribe_faster_whisper.choose_runtime("cuda", None),
            ("cuda", "float16"),
        )

    def test_updates_normalized_model_without_leaving_missing_subtitle_warning(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            source = root / "source.json"
            output = root / "content.json"
            source.write_text(
                json.dumps(
                    {
                        "schema_version": "1.0",
                        "metadata": {"duration_seconds": 10},
                        "diagnostics": {
                            "warnings": [
                                "No accessible subtitle text; use audio transcription fallback when content is required."
                            ]
                        },
                    }
                ),
                encoding="utf-8",
            )
            transcribe_faster_whisper.update_model(
                source,
                output,
                [{"start": 1.0, "end": 9.0, "text": "转写文本"}],
                "zh",
                0.95,
            )
            model = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(model["content"]["source_type"], "asr")
            self.assertEqual(model["source_status"]["coverage_ratio"], 0.8)
            self.assertEqual(len(model["diagnostics"]["warnings"]), 1)
            self.assertIn("ASR transcript", model["diagnostics"]["warnings"][0])


if __name__ == "__main__":
    unittest.main()
