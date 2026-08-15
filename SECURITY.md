# Security policy

## Supported versions

| Version | Security fixes |
|---|---|
| 1.x | Supported |
| < 1.0 | Not supported |

## Report a vulnerability

Use GitHub's private security advisory flow:

1. Open the repository's **Security** tab.
2. Select **Report a vulnerability**.
3. Include affected versions, impact, reproduction steps, and a minimal proof of concept.

Do not open a public issue for credential exposure, arbitrary code execution, unsafe file handling, or authentication bypass. Do not include real Bilibili cookies, session tokens, personal data, or copyrighted media in a report.

You should receive an acknowledgement within seven days. Publication and credit will be coordinated after a fix is available.

## Security model

- Anonymous public-data extraction is the default.
- Authentication requires explicit user consent and opt-in environment variables.
- Credentials must never appear in output, logs, fixtures, or error messages.
- Downloaded media and intermediate transcription files are temporary and should be removed after use.
- Generated paths must remain within the user-selected output directory.
