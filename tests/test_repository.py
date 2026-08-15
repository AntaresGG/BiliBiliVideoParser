import json
import re
import tomllib
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PLUGIN_ROOT = ROOT / "plugins" / "bilibili-video-parser"
SKILL_ROOT = PLUGIN_ROOT / "skills" / "bilibili-video-parser"


class RepositoryStructureTests(unittest.TestCase):
    def test_required_skill_and_plugin_files_exist(self) -> None:
        required = [
            ROOT / ".agents" / "plugins" / "marketplace.json",
            PLUGIN_ROOT / ".codex-plugin" / "plugin.json",
            SKILL_ROOT / "SKILL.md",
            SKILL_ROOT / "agents" / "openai.yaml",
            SKILL_ROOT / "scripts" / "bilibili_extract.py",
            SKILL_ROOT / "scripts" / "render_outputs.py",
            SKILL_ROOT / "scripts" / "transcribe_faster_whisper.py",
        ]
        self.assertEqual([str(path) for path in required if not path.is_file()], [])

    def test_versions_are_synchronized(self) -> None:
        plugin = json.loads((PLUGIN_ROOT / ".codex-plugin" / "plugin.json").read_text("utf-8"))
        with (ROOT / "pyproject.toml").open("rb") as stream:
            project = tomllib.load(stream)
        self.assertEqual(plugin["version"], project["project"]["version"])
        self.assertRegex(plugin["version"], r"^\d+\.\d+\.\d+$")

    def test_marketplace_points_to_existing_matching_plugin(self) -> None:
        marketplace = json.loads(
            (ROOT / ".agents" / "plugins" / "marketplace.json").read_text("utf-8")
        )
        entry = marketplace["plugins"][0]
        plugin = json.loads((PLUGIN_ROOT / ".codex-plugin" / "plugin.json").read_text("utf-8"))
        source = (ROOT / entry["source"]["path"]).resolve()
        self.assertEqual(entry["name"], plugin["name"])
        self.assertEqual(source, PLUGIN_ROOT.resolve())
        self.assertTrue(source.is_dir())

    def test_skill_frontmatter_contains_only_name_and_description(self) -> None:
        text = (SKILL_ROOT / "SKILL.md").read_text("utf-8")
        match = re.match(r"^---\n(.*?)\n---\n", text, re.DOTALL)
        self.assertIsNotNone(match)
        keys = {
            line.split(":", 1)[0].strip()
            for line in match.group(1).splitlines()
            if ":" in line
        }
        self.assertEqual(keys, {"name", "description"})

    def test_local_markdown_links_resolve(self) -> None:
        missing = []
        link_pattern = re.compile(r"(?<!!)\[[^]]+\]\(([^)]+)\)")
        for document in ROOT.glob("*.md"):
            for target in link_pattern.findall(document.read_text("utf-8")):
                clean_target = target.split("#", 1)[0]
                if not clean_target or "://" in clean_target or clean_target.startswith("mailto:"):
                    continue
                if not (document.parent / clean_target).exists():
                    missing.append(f"{document.name}: {target}")
        self.assertEqual(missing, [])


if __name__ == "__main__":
    unittest.main()
