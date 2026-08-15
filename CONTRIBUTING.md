# Contributing

Contributions that improve source fidelity, Bilibili compatibility, privacy, portability, or analysis quality are welcome.

## Before opening a change

- Search existing issues and discussions.
- Keep one pull request focused on one problem.
- Do not include copyrighted video, audio, subtitle dumps, cookies, tokens, or personal data.
- For endpoint changes, document the public endpoint and the observed failure mode.
- Preserve the distinction between speaker claims, audience reaction, external facts, and Codex inference.

## Development setup

Install `uv`, clone the repository, then run:

```powershell
uv sync
uv run --python 3.12 python -m unittest discover -s tests -v
```

The default codebase has no third-party runtime dependency. `faster-whisper`, `bilibili-cli`, `yt-dlp`, and FFmpeg are optional and should not be added to the default environment.

## Change guidelines

- Keep `SKILL.md` concise and imperative; put detailed methods in `references/`.
- Keep scripts deterministic and return structured errors without inventing missing data.
- Use asynchronous execution for independent network I/O.
- Add or update offline tests for behavior changes.
- Do not make live Bilibili calls in the standard test suite.
- Update all three README files when user-facing behavior or installation steps change.
- Update `CHANGELOG.md` for notable changes.

## Pull requests

Include:

- the problem and intended behavior;
- the smallest relevant implementation;
- validation commands and results;
- privacy or compatibility implications;
- screenshots only when presentation changes require them.

By contributing, you agree that your contribution is licensed under the repository's MIT License.
