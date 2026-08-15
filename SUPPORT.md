# Support

Use the appropriate GitHub channel:

- **Bug or compatibility problem:** open a bug report with a public Bilibili identifier, expected behavior, actual behavior, Codex version, operating system, and sanitized logs.
- **Feature proposal:** open a feature request describing the user problem and a concrete example prompt.
- **Security or credential issue:** follow [SECURITY.md](SECURITY.md); do not use a public issue.
- **Usage question:** open a GitHub Discussion when available, or a focused issue if discussions are disabled.

Before reporting extraction problems, run the self-check and include only its sanitized JSON result:

```powershell
uv run --python 3.12 plugins/bilibili-video-parser/skills/bilibili-video-parser/scripts/bilibili_extract.py --self-check
```

Never attach cookies, tokens, private videos, downloaded media, or full copyrighted subtitle files.
