# Release process

Maintainers publish releases from the PC source-of-truth checkout. Deployment-only working-tree changes from another machine must not be included.

## Prepare

1. Pull the latest `main` branch and confirm the worktree is clean.
2. Choose a Semantic Versioning number.
3. Update the same version in:
   - `pyproject.toml`
   - `plugins/bilibili-video-parser/.codex-plugin/plugin.json`
   - `CHANGELOG.md`
4. Move completed entries from `Unreleased` into the dated release section.

## Validate

```powershell
uv sync
uv run --python 3.12 python -m unittest discover -s tests -v
uv run --python 3.12 python -m compileall -q plugins/bilibili-video-parser/skills/bilibili-video-parser/scripts
```

Optionally run the live endpoint health check. A live failure caused by Bilibili rate limiting must be investigated but does not invalidate offline tests.

## Publish

```powershell
git add --all
git commit -m "Release v1.0.0"
git tag -a v1.0.0 -m "BiliLens v1.0.0"
git push origin main
git push origin v1.0.0
```

The release workflow validates the repository, checks that the tag matches both version files, packages `plugins/bilibili-video-parser`, and creates the GitHub Release with generated notes.

After publication, install the released plugin in a clean Codex environment and run one metadata request plus one subtitle-backed summary request.
