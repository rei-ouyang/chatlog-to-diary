**English** | [中文](README.zh-CN.md)

# chatlog-to-diary

![License](https://img.shields.io/badge/License-MIT-yellow?style=flat-square)
![Python](https://img.shields.io/badge/Python-3.9%2B-blue?style=flat-square)
![Claude Code](https://img.shields.io/badge/Claude%20Code-Skill-8A2BE2?style=flat-square)
![Local First](https://img.shields.io/badge/Local-First-brightgreen?style=flat-square)

> Turn each day's chat logs into the diary you might have written that night.

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

## Usage

### Option 1: Claude Code Skill (recommended)

```bash
# 1. Clone the repo
git clone https://github.com/rei-ouyang/chatlog-to-diary.git
cd chatlog-to-diary

# 2. Open in Claude Code
claude

# 3. Run the skill — first time will walk you through setup
/chatlog-to-diary
```

On first run, the skill asks a few questions interactively: where your chat files are, the format, diary language, your name(s) in the chat, the other person's name, and style preference. Answers are saved to `config.yaml` (gitignored). After that, `/chatlog-to-diary` processes everything automatically.

### Option 2: Standalone script (no Claude Code required)

```bash
# Install dependencies
pip install pyyaml anthropic   # or: pip install pyyaml openai

# Set your API key
export ANTHROPIC_API_KEY=sk-ant-...
# or
export OPENAI_API_KEY=sk-...

# Step 1: split chat log by date
python3 scripts/split_by_date.py source/ --output-dir /tmp/chatlog-split

# Step 2: generate diary entries (first run starts interactive setup)
python3 scripts/generate_diary.py --split-dir /tmp/chatlog-split

# If config.yaml already exists, skip setup entirely
python3 scripts/generate_diary.py --split-dir /tmp/chatlog-split --skip-setup
```

Optional environment overrides:
```bash
export DIARY_MODEL=claude-3-5-sonnet-20241022   # override model
export OPENAI_BASE_URL=https://your-provider/v1  # OpenAI-compatible providers
```

## Requirements

- Python 3.9+
- `PyMuPDF` (PDF exports only): `pip install PyMuPDF`
- Option 1 additionally requires: [Claude Code](https://docs.anthropic.com/en/docs/claude-code)
- Option 2 additionally requires: `pip install pyyaml anthropic` (or `openai`)

## Group Chat Support

Group chats are supported, but work differently from private chats.

In `config.yaml`:
```yaml
chat_type: group
group_name: "朋友群"   # how the group is referred to in the diary
```

In group mode, diary entries focus only on **your** messages and the concrete outcomes that involved you. Other members' conversations are ignored — this is by design. Group chats are noisy, and what others say there usually isn't a reliable snapshot of their lives.

**Group chat example input:**
```
[2025-04-01 20:00:00] 小明：周末有人打球吗
[2025-04-01 20:01:00] Alice：我可以！周六下午
[2025-04-01 20:02:00] 小红：我也去
[2025-04-01 20:03:00] Alice：太好了，那约球场吧
```

**Group chat diary output (only user's contribution):**
```
在朋友群里约好了周六下午打球，顺便约了球场。
```

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
│   ├── split_by_date.py    # Chat log parser & date splitter
│   └── generate_diary.py   # Standalone diary generator (no Claude Code needed)
├── source/                 # Your chat exports (gitignored)
├── output/                 # Generated diaries (gitignored)
├── .gitignore
└── README.md
```

## Configuration

Copy `config.example.yaml` to `config.yaml` and edit, or let the skill / script guide you through setup on first run.

Key options:

| Option | Description | Default |
|---|---|---|
| `source_dir` | Directory with chat export files | `source/` |
| `source_format` | `txt`, `pdf`, or `auto` | `auto` |
| `output_dir` | Where diary files are saved | `output/` |
| `diary_language` | `zh`, `en`, `ja`, etc. | `zh` |
| `chat_type` | `private` (1-on-1) or `group` | `private` |
| `user_labels` | Your name(s) in the chat log, comma-separated | — |
| `other_name` | Other person's display name (private chat) | — |
| `group_name` | Group label used in diary text (group chat) | `群` |
| `writing_style` | `concise` or `narrative` | `concise` |
| `keep_foreign_quotes` | Preserve foreign-language quotes | `true` |
| `foreign_languages` | Which languages to preserve | `[en, ja]` |

**About `user_labels`**: If you're "Alice" on WeChat and "アリス" on LINE, list both:
```yaml
user_labels: "Alice, アリス"
```
The tool will recognise either name as you.

## Privacy

- `source/` and `output/` are gitignored — your chat data and diaries never leave your machine
- `config.yaml` is gitignored — your personal settings stay local
- All examples in this repo use fictional names and content
- No real personal data is included anywhere in this project

## License

MIT
