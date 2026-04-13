[English](README.md) | **中文**

# chatlog-to-diary

把聊天记录自动转化为第一人称日记。

导出微信、LINE 或其他聊天工具的对话记录 → 本工具按日期切分，为每一天生成一篇第一人称日记，像是你自己在当晚写下的。

## 工作原理

1. 将聊天记录导出为 `.txt` 或 `.pdf`
2. 工具自动解析时间戳，按日期切分消息
3. 为每一天生成以「我」为视角的日记，聚焦你做了什么、说了什么、经历了什么
4. 如果当天已有日记，新内容追加在末尾，不会覆盖

## 示例

**聊天记录输入：**
```
[2025-03-15 09:30:00] Alice：今天搬到新公寓了，叫了个搬家公司
[2025-03-15 09:31:00] Sam：怎么样新地方
[2025-03-15 09:32:00] Alice：比想象中大！阳台能看到河
[2025-03-15 09:33:00] Sam：That's amazing, jealous
[2025-03-15 18:00:00] Alice：刚组装完书架，腰快断了
[2025-03-15 18:01:00] Sam：辛苦了！来暖房的时候我带酒
```

**日记输出：**
```
今天搬进了新公寓，叫了搬家公司。比想象中大，阳台能看到河。Sam说That's amazing, jealous。
傍晚组装完书架，腰快断了。Sam说来暖房的时候带酒。
```

信息极少的天只生成一句话：
```
今天记录极少。
```

## 环境要求

- [Claude Code](https://docs.anthropic.com/en/docs/claude-code)（本工具作为 Claude Code skill 运行）
- Python 3.9+
- `PyMuPDF`（仅 PDF 格式需要）：`pip install PyMuPDF`

## 快速开始

```bash
# 1. 克隆仓库
git clone https://github.com/yourname/chatlog-to-diary.git
cd chatlog-to-diary

# 2. 打开 Claude Code
claude

# 3. 运行 skill —— 首次使用会引导你完成配置
/chatlog-to-diary
```

首次运行时，skill 会交互式地问你几个问题：

- 聊天记录文件在哪里？
- 什么格式（txt/pdf）？
- 日记用什么语言？
- 你在聊天记录中的名字
- 对方的名字或昵称
- 写作风格偏好（简洁事件驱动 vs 详细叙事）

回答会保存到 `config.yaml`（已 gitignore）。之后每次运行 `/chatlog-to-diary` 直接自动处理，不再重复提问。

## 支持的聊天格式

解析器（`scripts/split_by_date.py`）自动检测以下格式：

**格式 A —— 带时间戳的消息（微信风格）：**
```
[2025-01-01 12:00:00] Alice：Happy new year!
[2025-01-01 12:01:00] Bob：新年快乐！
```

**格式 B —— 带日期分隔线（LINE 风格）：**
```
2025/01/01（水）
12:00	Alice	Happy new year!
12:01	Bob	新年快乐！
```

**格式 C —— PDF 导出：**
先提取文本，再按上述规则解析。

其他格式也可能支持——解析器会尝试多种模式并选择最佳匹配。

## 项目结构

```
chatlog-to-diary/
├── .claude/
│   └── settings.json      # Claude Code 权限配置
├── CLAUDE.md               # Skill 逻辑（Claude 如何生成日记）
├── config.example.yaml     # 配置模板（虚构示例数据）
├── config.yaml             # 你的实际配置（gitignored）
├── scripts/
│   └── split_by_date.py    # 聊天记录解析与按日期切分
├── source/                 # 你的聊天记录文件（gitignored）
├── output/                 # 生成的日记（gitignored）
├── .gitignore
└── README.md
```

## 配置说明

复制 `config.example.yaml` 为 `config.yaml` 手动编辑，或者在首次运行时让 skill 引导你完成配置。

主要选项：

| 选项 | 说明 | 默认值 |
|---|---|---|
| `source_dir` | 聊天记录文件所在目录 | `source/` |
| `source_format` | `txt`、`pdf` 或 `auto` | `auto` |
| `output_dir` | 日记输出目录 | `output/` |
| `diary_language` | `zh`、`en`、`ja` 等 | `zh` |
| `user_labels` | 你在聊天记录中的名字 | — |
| `other_name` | 对方的显示名称 | — |
| `writing_style` | `concise`（简洁）或 `narrative`（叙事） | `concise` |
| `keep_foreign_quotes` | 是否保留对方的外语原文 | `true` |
| `foreign_languages` | 保留哪些语言的原文 | `[en, ja]` |

## 隐私保护

- `source/` 和 `output/` 已 gitignore —— 你的聊天数据和日记不会离开本地
- `config.yaml` 已 gitignore —— 你的个人配置不会被提交
- 本仓库所有示例均使用虚构人名和内容
- 项目中不包含任何真实个人数据

## 许可证

MIT
