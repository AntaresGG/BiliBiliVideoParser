# BiliLens · 面向 Codex 的 Bilibili 视频解析 Skill

简体中文 · [English](README.md) · [日本語](README.ja.md)

![BiliLens——面向 Codex 的可追溯 Bilibili 视频理解](assets/bililens-banner.svg)

[![CI](https://github.com/AntaresGG/BiliBiliVideoParser/actions/workflows/ci.yml/badge.svg)](https://github.com/AntaresGG/BiliBiliVideoParser/actions/workflows/ci.yml)
[![Release](https://img.shields.io/github/v/release/AntaresGG/BiliBiliVideoParser?display_name=tag)](https://github.com/AntaresGG/BiliBiliVideoParser/releases)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![GitHub stars](https://img.shields.io/github/stars/AntaresGG/BiliBiliVideoParser?style=social)](https://github.com/AntaresGG/BiliBiliVideoParser/stargazers)

一个可安装的 Codex Skill，用于完成**哔哩哔哩视频总结、字幕提取、时间轴梳理、论据分析和弹幕反馈研究**。只需提供 Bilibili 链接或 `BV`、`av`、`ep`、`ss` 标识，即可获得有来源、有时间戳、可追溯的中文内容分析。

BiliLens 针对 B 站内容结构设计：识别多 P 视频，优先使用人工字幕，其次使用 AI 字幕，必要时在本地进行语音识别，并可按需分析弹幕热点。它会明确区分视频作者观点、观众反应、外部事实和 Codex 推断。

## 为什么选择 BiliLens

- **结论可追溯**：关键内容关联时间戳和来源元数据。
- **原生适配 B 站**：支持短链接、BV/av 号、番剧 ep/ss 号和 `?p=` 分 P。
- **字幕优先**：人工字幕优先于 AI 字幕，仅在必要时回退到本地 ASR。
- **不止是摘要**：可生成时间轴、论据链、不确定性、矛盾点和延伸洞察。
- **按需理解弹幕**：发现 30 秒注意力热点和重复反馈，同时明确弹幕不等于事实。
- **注重隐私**：默认匿名提取；不会静默读取浏览器 Cookie 或登录凭据。
- **多格式交付**：默认在对话中返回，也可导出 Markdown、TXT、JSON、SRT 和独立 HTML。

## 快速开始

### 1. 安装插件

需要支持 Plugin 的新版 Codex CLI。

```powershell
codex plugin marketplace add AntaresGG/BiliBiliVideoParser
codex plugin add bilibili-video-parser@bililens
```

如果安装后没有立即显示，请重启 Codex；可通过 `/skills` 确认 `bilibili-video-parser` 已可用。

也可以让 Skill Installer 直接安装独立 Skill：

```text
使用 $skill-installer 安装以下仓库路径中的 Skill：
https://github.com/AntaresGG/BiliBiliVideoParser/tree/main/plugins/bilibili-video-parser/skills/bilibili-video-parser
```

### 2. 调用 Skill

显式调用最稳定：

```text
使用 $bilibili-video-parser 总结这个视频，并保留关键时间戳：
https://www.bilibili.com/video/BV...
```

也可以直接用自然语言：

```text
分析这个 B 站视频，给我时间轴、核心论点和证据链：BV...
```

## 常见使用场景

| 目标 | 示例提示词 |
|---|---|
| 快速总结 | `用 $bilibili-video-parser 简要总结 BV...` |
| 时间轴大纲 | `为这个 B 站视频生成带时间戳的大纲：...` |
| 清洗字幕 | `提取并清洗字幕，保留时间戳：...` |
| 深度研究 | `分析 BV... 中的主张、证据、不确定性与影响` |
| 指定分 P | `分析这个系列视频的第 3 P：...` |
| 弹幕反馈 | `总结视频，并加入弹幕热点和观众反应：...` |
| 文件导出 | `将分析导出为 Markdown 和 JSON 到当前目录：...` |

## 能生成什么

BiliLens 使用固定分析顺序：**来源卡 → 时间轴 → 论据链 → 互动场 → 洞察层**。

| 模式 | 输出内容 |
|---|---|
| `metadata` | 规范链接、所选分 P、UP 主、发布时间、实时统计和来源状态 |
| `transcript` | 仅做必要修正的时间戳字幕 |
| `cleaned_transcript` | 优化标点和分段，但不改变原意 |
| `outline` | 来源卡和带时间戳的内容结构 |
| `summary` | 主旨、关键观点、代表性证据和不确定性 |
| `research` | 主张—证据映射、矛盾、影响和验证条件 |
| `full` | 完整字幕及所有适用的 BiliLens 层级 |

默认直接在对话中返回结果；仅在明确要求时创建文件。

## 内容获取流程

1. 解析规范视频地址并确认所选分 P。
2. 匿名获取公开元数据和可用字幕轨道。
3. 优先选择人工字幕，其次选择 AI 字幕。
4. 在没有字幕且任务确实需要内容时，才回退到本地 ASR。
5. 仅在要求观众反馈分析时获取弹幕。

ASR 回退可能使用 [`bilibili-cli`](https://github.com/public-clis/bilibili-cli)、`yt-dlp` 和 `faster-whisper`。模型下载和转写在本地完成。人名、数字、证券代码、术语、口音及多人重叠说话可能降低识别准确率。

## 环境要求

- 支持 Skills 的 Codex 桌面端、CLI 或 IDE 扩展
- [`uv`](https://docs.astral.sh/uv/) 和 Python 3.12
- 能访问 Bilibili 公开接口的网络
- 可选：用于 ASR 回退的 `bilibili-cli`、`yt-dlp`、FFmpeg 和 `faster-whisper`

默认提取器仅使用 Python 标准库，本 Skill 不要求 OpenAI API Key。

## 隐私与认证

默认使用匿名提取。Skill 在读取浏览器 Cookie 或环境凭据前必须征得同意。若你主动启用认证提取，凭据只会作为请求 Cookie 发送至 Bilibili，不会写入生成结果。

详见 [PRIVACY.md](PRIVACY.md) 和 [SECURITY.md](SECURITY.md)。不要把原始 Cookie 或会话令牌粘贴到聊天、Issue 或日志中。

## 仓库结构

```text
.
├── .agents/plugins/marketplace.json       # Codex marketplace 目录
├── plugins/bilibili-video-parser/
│   ├── .codex-plugin/plugin.json          # 可安装插件清单
│   └── skills/bilibili-video-parser/
│       ├── SKILL.md                       # Skill 触发条件与工作流
│       ├── agents/openai.yaml             # Codex 界面元数据
│       ├── references/                    # BiliLens 方法和报告规范
│       └── scripts/                       # 提取、ASR 和渲染工具
├── tests/                                 # 离线单元测试与结构测试
└── .github/                               # CI、发布和社区模板
```

可安装的 Skill 载荷与仓库说明文档分离，避免 Codex 在运行时加载无关内容。

## 开发与验证

```powershell
uv sync
uv run --python 3.12 python -m unittest discover -s tests -v
uv run --python 3.12 python -m compileall -q plugins/bilibili-video-parser/skills/bilibili-video-parser/scripts
```

仅在需要检查实时接口时运行：

```powershell
uv run --python 3.12 plugins/bilibili-video-parser/skills/bilibili-video-parser/scripts/bilibili_extract.py --self-check
```

贡献规范见 [CONTRIBUTING.md](CONTRIBUTING.md)，发布流程见 [RELEASING.md](RELEASING.md)。

## 限制与合规使用

- 字幕可用性受视频、账号权限、地区和 Bilibili 接口状态影响。
- 弹幕只代表观众反馈，不构成事实验证或代表性调查。
- 本项目不会绕过付费墙、访问控制、DRM 或版权限制。
- 使用者需自行遵守平台条款、版权、隐私和当地法律。
- 本项目与 Bilibili、OpenAI 均无隶属、授权或背书关系。

## 版本与版权

当前版本线：**v1.0.x**。更新内容见 [CHANGELOG.md](CHANGELOG.md) 和 [GitHub Releases](https://github.com/AntaresGG/BiliBiliVideoParser/releases)。

本项目采用 [MIT License](LICENSE)。Copyright © 2026 AntaresGG。
