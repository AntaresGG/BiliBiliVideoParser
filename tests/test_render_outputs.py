import sys
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

import render_outputs  # noqa: E402


def sample_model() -> dict:
    return {
        "schema_version": "1.0",
        "source": {
            "canonical_url": "https://www.bilibili.com/video/BV1xx411c7mD/",
            "fetched_at": "2026-08-15T00:00:00Z",
        },
        "metadata": {
            "bvid": "BV1xx411c7mD",
            "title": "测试 <标题>",
            "uploader": {"name": "UP 主"},
        },
        "selection": {"page": 1, "part_title": "正片"},
        "content": {
            "source_type": "official_subtitle",
            "segments": [
                {"start": 1.25, "end": 3.5, "text": "第一句"},
                {"start": 4.0, "end": 6.0, "text": "第二句"},
            ],
        },
        "analysis": {"executive_summary": "核心结论"},
        "diagnostics": {"warnings": []},
    }


class FormatTests(unittest.TestCase):
    def test_deduplicates_formats(self) -> None:
        self.assertEqual(render_outputs.parse_formats("markdown,txt,markdown"), ["markdown", "txt"])

    def test_rejects_unknown_format(self) -> None:
        with self.assertRaises(render_outputs.RenderError):
            render_outputs.parse_formats("pdf")

    def test_renders_timestamped_srt(self) -> None:
        output = render_outputs.render_srt(sample_model())
        self.assertIn("00:00:01,250 --> 00:00:03,500", output)
        self.assertIn("第一句", output)

    def test_escapes_html_content(self) -> None:
        output = render_outputs.render_html(sample_model())
        self.assertIn("测试 &lt;标题&gt;", output)
        self.assertNotIn("<h1>测试 <标题></h1>", output)

    def test_uses_stable_bvid_basename(self) -> None:
        self.assertEqual(render_outputs.default_basename(sample_model()), "bv1xx411c7md-p1")


if __name__ == "__main__":
    unittest.main()
