# Privacy

BiliLens is a local Codex workflow and does not operate a hosted service or collect analytics.

## Data accessed

Depending on the request, the bundled tools may access public Bilibili metadata, subtitle tracks, and danmaku endpoints. Live engagement statistics include a retrieval timestamp because they can change.

## Authentication

Anonymous extraction is the default. Authenticated extraction is opt-in and may use deliberately configured `BILI_SESSDATA`, `BILI_JCT`, and `BILI_BUVID3` environment variables. The Skill must ask before accessing browser cookies or other local session data.

Credentials are used only as request cookies sent to Bilibili. The bundled extractor does not write credential values into its normalized JSON output.

## Local files

When subtitles are unavailable, optional ASR can download audio and a speech-recognition model. Transcription occurs locally. Temporary audio, intermediate models created for the task, and one-time outputs should be removed after delivery unless the user explicitly asks to keep them.

## Third parties

Network requests are governed by the policies and terms of the services contacted, including Bilibili and any explicitly selected download or model provider. This repository is not affiliated with Bilibili or OpenAI.
