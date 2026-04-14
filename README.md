**English** | [中文](README.zh-CN.md)

# chatlog-to-diary

Turn your chat logs into first-person diary entries, automatically.

Export a conversation from WeChat, LINE, or any messenger → this tool splits it by date and writes a diary entry for each day, as if you wrote it yourself at the end of the night.

## How It Works

1. You export your chat history as `.txt` or `.pdf`
2. The tool parses timestamps and splits messages by date
3. For each day, it generates a first-person diary entry focused on what **you** did, said, and experienced
4. If a diary already exists for that day, new content is appended — nothing gets overwritten

## Example

**Chat log input:**
```
[2025-03-15 09:30:00] Alice：今天搬到新公寓了，叫了个搬家公司
[2025-03-15 09:31:00] Sam：怎么样新地方
[2025-03-15 09:32:00] Alice：比想象中大！阳台能看到河
[2025-03-15 09:33:00] Sam：That's amazing, jealous
[2025-03-15 18:00:00] Alice：刚组装完书架，腰快断了
[2025-03-15 18:01:00] Sam：辛苦了！来暖房的时候我带酒
```

**Diary output:**
```
今天搬进了新公寓，叫了搬家公司。比想象中大，阳台能看到河。Sam说That's amazing, jealous。
傍晚组装完书架，腰快断了。Sam说来暖房的时候带酒。
```

Days with very few messages produce a single line:
```
今天记录极少。
```

## Requirements

- [Claude Code](https://docs.anthropic.com/en/docs/claude-code) (this tool runs as a Claude Code skill)
- Python 3.9+
- `PyMuPDF` (only if you have PDF chat exports): `pip install PyMuPDF`

## Quick Start

```bash
# 1. Clone the repo
git clone https://github.com/rei-ouyang/chatlog-to-diary.git
cd chatlog-to-diary

# 2. Open in Claude Code
claude

# 3. Run the skill — first time will walk you through setup
/chatlog-to-diary
```

On first run, the skill asks a few questions interactively:

- Where are your chat files?
- What format (txt/pdf)?
- What language for the diary?
- Your name as it appears in the chat
- The other person's name
- Style preference (concise vs. narrative)

Answers are saved to `config.yaml` (gitignored). After that, just run `/chatlog-to-diary` and it processes everything automatically.

## Supported Chat Formats

The parser (`scripts/split_by_date.py`) auto-detects these formats:

**Format A — Timestamped messages (WeChat-style):**
```
[2025-01-01 12:00:00] Alice：Happy new year!
[2025-01-01 12:01:00] Bob：新年快乐！
```

**Format B — Date separator lines (LINE-style):**
```
2025/01/01（水）
12:00	Alice	Happy new year!
12:01	Bob	新年快乐！
```

**Format C — PDF exports:**
Text is extracted first, then parsed using the same rules.

Other formats can work too — the parser tries multiple patterns and picks the best match.

## Project Structure

```
chatlog-to-diary/
├── .claude/
│   └── settings.json      # Claude Code permissions
├── .claude/skills/         # Claude Code skill definition
│   └── chatlog-to-diary/
│       └── SKILL.md
├── CLAUDE.md               # Project overview
├── config.example.yaml     # Example config with fictional data
├── config.yaml             # Your config (gitignored)
├── scripts/
│   └── split_by_date.py    # Chat log parser & date splitter
├── source/                 # Your chat exports (gitignored)
├── output/                 # Generated diaries (gitignored)
├── .gitignore
└── README.md
```

## Configuration

Copy `config.example.yaml` to `config.yaml` and edit, or let the skill guide you through setup on first run.

Key options:

| Option | Description | Default |
|---|---|---|
| `source_dir` | Directory with chat export files | `source/` |
| `source_format` | `txt`, `pdf`, or `auto` | `auto` |
| `output_dir` | Where diary files are saved | `output/` |
| `diary_language` | `zh`, `en`, `ja`, etc. | `zh` |
| `user_labels` | Your name(s) in the chat log | — |
| `other_name` | Other person's display name | — |
| `writing_style` | `concise` or `narrative` | `concise` |
| `keep_foreign_quotes` | Preserve foreign-language quotes | `true` |
| `foreign_languages` | Which languages to preserve | `[en, ja]` |

## Privacy

- `source/` and `output/` are gitignored — your chat data and diaries never leave your machine
- `config.yaml` is gitignored — your personal settings stay local
- All examples in this repo use fictional names and content
- No real personal data is included anywhere in this project

## License

MIT
