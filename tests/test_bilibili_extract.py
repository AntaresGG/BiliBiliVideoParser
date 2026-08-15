import os
import sys
import unittest
from pathlib import Path
from unittest.mock import patch


SKILL_ROOT = (
    Path(__file__).resolve().parents[1]
    / "plugins"
    / "bilibili-video-parser"
    / "skills"
    / "bilibili-video-parser"
)
sys.path.insert(0, str(SKILL_ROOT / "scripts"))

import bilibili_extract  # noqa: E402


class ReferenceTests(unittest.TestCase):
    def test_parses_bvid_and_linked_page(self) -> None:
        result = bilibili_extract.parse_reference(
            "https://www.bilibili.com/video/BV1xx411c7mD/?p=3"
        )
        self.assertEqual(result, {"bvid": "BV1xx411c7mD", "page": 3})

    def test_parses_supported_identifier_types(self) -> None:
        self.assertEqual(bilibili_extract.parse_reference("av170001")["aid"], 170001)
        self.assertEqual(bilibili_extract.parse_reference("ep12345")["ep_id"], 12345)
        self.assertEqual(bilibili_extract.parse_reference("ss6789")["season_id"], 6789)

    def test_rejects_unknown_reference(self) -> None:
        with self.assertRaises(bilibili_extract.ParserError):
            bilibili_extract.parse_reference("https://example.com/video")


class SubtitleTests(unittest.TestCase):
    def test_prefers_human_chinese_subtitle(self) -> None:
        tracks = [
            {"lan": "ai-zh", "lan_doc": "中文（自动生成）", "ai_type": 1},
            {"lan": "en", "lan_doc": "English", "ai_type": 0},
            {"lan": "zh-CN", "lan_doc": "中文", "ai_type": 0},
        ]
        selected = bilibili_extract.choose_subtitle(tracks, None)
        self.assertEqual(selected["lan"], "zh-CN")

    def test_honors_requested_language(self) -> None:
        tracks = [
            {"lan": "zh-CN", "lan_doc": "中文"},
            {"lan": "ja", "lan_doc": "日本語"},
        ]
        selected = bilibili_extract.choose_subtitle(tracks, "ja")
        self.assertEqual(selected["lan"], "ja")


class DanmakuTests(unittest.TestCase):
    def test_summarizes_entries_without_treating_them_as_facts(self) -> None:
        payload = (
            '<i><d p="1.2,1,25,0,0,0,0,0">好</d>'
            '<d p="4.8,1,25,0,0,0,0,0">好</d>'
            '<d p="35,1,25,0,0,0,0,0">重点</d></i>'
        ).encode("utf-8")
        result = bilibili_extract.parse_danmaku(payload, limit=2)
        self.assertEqual(result["fetched_count"], 3)
        self.assertEqual(result["sampled"], 2)
        self.assertEqual(result["repeated_comments"], [{"text": "好", "count": 2}])
        self.assertIn("not factual verification", result["interpretation_warning"])


class AuthenticationTests(unittest.TestCase):
    @patch.dict(os.environ, {"BILI_JCT": "csrf-only"}, clear=True)
    def test_requires_sessdata(self) -> None:
        with self.assertRaises(bilibili_extract.ParserError):
            bilibili_extract.BilibiliClient(use_env_cookie=True)

    @patch.dict(
        os.environ,
        {"BILI_SESSDATA": "session", "BILI_JCT": "csrf", "BILI_BUVID3": "device"},
        clear=True,
    )
    def test_builds_cookie_only_after_explicit_opt_in(self) -> None:
        client = bilibili_extract.BilibiliClient(use_env_cookie=True)
        self.assertEqual(client.cookie, "SESSDATA=session; bili_jct=csrf; buvid3=device")


if __name__ == "__main__":
    unittest.main()
