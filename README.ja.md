# BiliLens · Codex 向け Bilibili 動画解析 Skill

[简体中文](README.zh-CN.md) · [English](README.md) · 日本語

![BiliLens — Codex 向けの追跡可能な Bilibili 動画理解](assets/bililens-banner.svg)

[![CI](https://github.com/AntaresGG/BiliBiliVideoParser/actions/workflows/ci.yml/badge.svg)](https://github.com/AntaresGG/BiliBiliVideoParser/actions/workflows/ci.yml)
[![Release](https://img.shields.io/github/v/release/AntaresGG/BiliBiliVideoParser?display_name=tag)](https://github.com/AntaresGG/BiliBiliVideoParser/releases)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![GitHub stars](https://img.shields.io/github/stars/AntaresGG/BiliBiliVideoParser?style=social)](https://github.com/AntaresGG/BiliBiliVideoParser/stargazers)

**Bilibili 動画の要約、字幕抽出、タイムライン作成、根拠分析、弾幕反応の調査**を行う、インストール可能な Codex Skill です。Bilibili の URL、または `BV`・`av`・`ep`・`ss` ID を渡すだけで、出典とタイムスタンプを確認できる中国語の分析結果を生成します。

BiliLens は Bilibili 固有の構造に対応しています。複数パートの選択、人手字幕と AI 字幕の優先順位付け、必要時のみのローカル音声認識、ライブメタデータ、任意の弾幕反応分析を扱います。話者の主張、視聴者の反応、外部の事実、Codex の推論を明確に分離します。

## BiliLens の特長

- **追跡可能な分析**：重要な内容をタイムスタンプとソースメタデータに結び付けます。
- **Bilibili ネイティブ**：短縮 URL、BV/av ID、番劇 ep/ss ID、`?p=` のパート指定に対応します。
- **字幕優先**：人手字幕、AI 字幕の順で使用し、ローカル ASR は最後の手段にします。
- **要約以上の理解**：タイムライン、根拠チェーン、不確実性、矛盾、示唆を整理します。
- **必要時のみ弾幕分析**：注目区間や反復反応を抽出し、反応と事実を混同しません。
- **プライバシー重視**：既定は匿名取得で、Cookie や認証情報を無断で読みません。
- **複数形式の出力**：チャット、Markdown、TXT、JSON、SRT、単体 HTML に対応します。

## クイックスタート

### 1. プラグインをインストール

Plugin 機能に対応した最新の Codex CLI が必要です。

```powershell
codex plugin marketplace add AntaresGG/BiliBiliVideoParser
codex plugin add bilibili-video-parser@bililens
```

すぐに表示されない場合は Codex を再起動してください。`/skills` で `bilibili-video-parser` が利用可能か確認できます。

Skill Installer から単体 Skill として導入することもできます。

```text
$skill-installer を使って、次のリポジトリパスから Skill をインストールしてください：
https://github.com/AntaresGG/BiliBiliVideoParser/tree/main/plugins/bilibili-video-parser/skills/bilibili-video-parser
```

### 2. Skill を呼び出す

明示的な呼び出しが最も確実です。

```text
Use $bilibili-video-parser to summarize this video with timestamps:
https://www.bilibili.com/video/BV...
```

自然言語でも利用できます。

```text
この Bilibili 動画を分析し、タイムライン、主要な主張、根拠をまとめてください：BV...
```

## 主なユースケース

| 目的 | プロンプト例 |
|---|---|
| 短い要約 | `Use $bilibili-video-parser to give me a concise summary of BV...` |
| タイムライン | `この Bilibili 動画のタイムスタンプ付き構成を作成してください：...` |
| 字幕の整形 | `字幕を抽出して読みやすく整え、タイムスタンプを保持してください：...` |
| 詳細調査 | `BV... の主張、根拠、不確実性、示唆を分析してください` |
| パート指定 | `このシリーズのパート 3 を分析してください：...` |
| 弾幕反応 | `動画を要約し、弾幕の注目区間と視聴者反応も含めてください：...` |
| ファイル出力 | `分析を Markdown と JSON で現在のフォルダーに保存してください：...` |

## 出力できる内容

BiliLens は **ソースカード → タイムライン → 根拠チェーン → 反応フィールド → 洞察レイヤー** の順で分析します。

| モード | 出力 |
|---|---|
| `metadata` | 正規 URL、選択パート、投稿者、公開日時、統計、ソース状態 |
| `transcript` | 最小限の修正を加えたタイムスタンプ付き原文 |
| `cleaned_transcript` | 意味を変えずに句読点と段落を整えた字幕 |
| `outline` | ソースカードとタイムスタンプ付き構成 |
| `summary` | 主題、要点、代表的な根拠、不確実性 |
| `research` | 主張と根拠の対応、矛盾、示唆、検証条件 |
| `full` | 字幕と適用可能なすべての BiliLens レイヤー |

既定ではチャットに結果を返します。ファイルは明示的に要求された場合のみ作成します。

## コンテンツ取得の流れ

1. 正規動画 URL と対象パートを確定します。
2. 公開メタデータと利用可能な字幕を匿名で取得します。
3. 人手字幕を優先し、次に AI 字幕を選びます。
4. 字幕がなく、内容解析に必要な場合のみローカル ASR を使用します。
5. 視聴者反応が要求された場合のみ弾幕を取得します。

ASR では必要に応じて [`bilibili-cli`](https://github.com/public-clis/bilibili-cli)、`yt-dlp`、`faster-whisper` を使用します。モデルのダウンロードと文字起こしはローカルで行われます。固有名詞、数値、銘柄コード、専門用語、アクセント、発話の重なりは認識精度を下げる可能性があります。

## 必要環境

- Skills 対応の Codex デスクトップアプリ、CLI、または IDE 拡張
- [`uv`](https://docs.astral.sh/uv/) と Python 3.12
- Bilibili の公開エンドポイントへ接続できるネットワーク
- 任意：ASR 用の `bilibili-cli`、`yt-dlp`、FFmpeg、`faster-whisper`

既定の抽出ツールは Python 標準ライブラリのみを使用します。この Skill 自体に OpenAI API キーは不要です。

## プライバシーと認証

既定は匿名取得です。ブラウザー Cookie や環境変数の認証情報を読む前に、Skill は必ず許可を求めます。認証付き取得を明示的に有効化した場合も、認証情報は Bilibili へのリクエスト Cookie としてのみ使われ、生成物には保存されません。

詳細は [PRIVACY.md](PRIVACY.md) と [SECURITY.md](SECURITY.md) を参照してください。Cookie やセッショントークンをチャット、Issue、ログに貼り付けないでください。

## リポジトリ構成

```text
.
├── .agents/plugins/marketplace.json       # Codex marketplace カタログ
├── plugins/bilibili-video-parser/
│   ├── .codex-plugin/plugin.json          # インストール可能なプラグイン定義
│   └── skills/bilibili-video-parser/
│       ├── SKILL.md                       # トリガーとワークフロー
│       ├── agents/openai.yaml             # Codex UI メタデータ
│       ├── references/                    # BiliLens 手法とレポート規約
│       └── scripts/                       # 取得、ASR、レンダリングツール
├── tests/                                 # オフラインテストと構造検証
└── .github/                               # CI、リリース、コミュニティテンプレート
```

インストール対象の Skill とリポジトリ文書を分離し、Codex が実行時に不要な文書を読み込まない構成です。

## 開発と検証

```powershell
uv sync
uv run --python 3.12 python -m unittest discover -s tests -v
uv run --python 3.12 python -m compileall -q plugins/bilibili-video-parser/skills/bilibili-video-parser/scripts
```

ライブ API の状態確認が必要な場合のみ、次を実行します。

```powershell
uv run --python 3.12 plugins/bilibili-video-parser/skills/bilibili-video-parser/scripts/bilibili_extract.py --self-check
```

コントリビューションについては [CONTRIBUTING.md](CONTRIBUTING.md)、リリース手順については [RELEASING.md](RELEASING.md) を参照してください。

## 制限と責任ある利用

- 字幕の可用性は動画、アカウント権限、地域、Bilibili のエンドポイント状態に依存します。
- 弾幕は視聴者反応であり、事実確認や代表性のある調査ではありません。
- ペイウォール、アクセス制御、DRM、著作権制限を回避しません。
- 利用者はプラットフォーム規約、著作権、プライバシー、各地域の法律を遵守してください。
- 本プロジェクトは Bilibili または OpenAI と提携・承認・後援関係にありません。

## リリースとライセンス

現在のリリース系列：**v1.0.x**。[CHANGELOG.md](CHANGELOG.md) と [GitHub Releases](https://github.com/AntaresGG/BiliBiliVideoParser/releases) を参照してください。

[MIT License](LICENSE) で公開しています。Copyright © 2026 AntaresGG.
