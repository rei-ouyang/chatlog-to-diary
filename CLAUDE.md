# chatlog-to-diary

Convert chat logs into first-person diary entries.

## Overview

This tool reads exported chat logs (txt or pdf), splits them by date, and generates a first-person diary entry for each day. It is designed as a Claude Code skill — run it by opening this project directory in Claude Code.

## Workflow

There are two modes: **first-run setup** and **daily generation**.

### First-Run Setup

If `config.yaml` does not exist, run the interactive setup before doing anything else.

Ask the user the following questions one at a time. Use their answers to generate `config.yaml`. Do not dump all questions at once — have a conversation.

1. **Source path**: "Where are your chat export files? (default: `source/`)"
2. **Source format**: "What format are they in? (txt / pdf / auto)"
3. **Output directory**: "Where should I save the diary files? (default: `output/`)"
4. **Diary language**: "What language should the diary be in? (zh / en / ja / other)"
5. **User labels**: "How does your name appear in the chat logs? If you have multiple names or aliases, separate them with commas."
6. **Other participant name**: "What's the other person's name or nickname? (used when referring to them in the diary)"
7. **Foreign quotes**: "Should I keep the other person's foreign-language quotes in their original language? (yes/no)" — if yes, ask "Which languages? (e.g., en, ja)"
8. **Writing style**: "Do you prefer concise event-driven entries or more detailed narrative style? (concise / narrative)"

After collecting all answers, write `config.yaml` with the values. Confirm to the user that setup is complete and they can now run the skill again to generate diaries.

Create the `source/` and `output/` directories if they don't exist:
```bash
mkdir -p source/ output/
```

### Daily Generation

If `config.yaml` exists, proceed with diary generation.

**Step 1 — Split chat logs by date**

Run the split script:
```bash
python3 scripts/split_by_date.py <source_dir> --format <source_format> --output-dir /tmp/chatlog-split
```

This produces one `.txt` file per date in `/tmp/chatlog-split/`, named `YYYY-MM-DD.txt`.

**Step 2 — Generate diary for each date**

For each date file from step 1, read the day's chat content and generate a diary entry.

Read the config values from `config.yaml` to determine language, style, participant names, etc.

**Diary generation rules:**

- Write in first person (我 / I / 私)
- The diary subject is always the user
- Write events, actions, arrangements, and states directly — not "我说了X" or "对方说了Y"
  - Good: "今天搬进了新公寓"
  - Bad: "我跟Sam说我搬到新公寓了"
- Use the other person's name directly (from config `other_name`) instead of 他/她/对方/the other person
- Do not invent emotions, intentions, or events not in the chat
- Write as if reflecting at the end of that day
- No bullet points — flowing prose only
- If `keep_foreign_quotes` is true, preserve quotes in the specified languages
- Length is proportional to information density:
  - Very few messages → one sentence, e.g., "今天记录极少。" or "Not much happened today."
  - Light day → 2-4 sentences
  - Normal day → a short paragraph
  - Dense day → a full paragraph or two
- Output the diary entry only — no labels, no headers, no explanations

**Writing style variations:**

- `concise`: event-driven, factual, short sentences. Focus on what happened.
- `narrative`: more detailed, includes transitions, captures mood when evident from chat.

**Step 3 — Save to output directory**

Save each diary entry to `<output_dir>/YYYY/YYYY-MM-DD.md`.

**Important**: if the output file already exists, **append** the new content to the end of the file (with a blank line separator). Never overwrite existing diary content.

Create year subdirectories as needed.

**Step 4 — Report**

After processing, tell the user:
- How many days were processed
- How many were new vs appended
- How many were skipped (no meaningful content)
- Where the output files are

## Reference: Style Examples

All examples below use fictional people and events.

**Input (chat log):**
```
[2025-03-15 09:30:00] Alice：今天搬到新公寓了，叫了个搬家公司
[2025-03-15 09:31:00] Sam：怎么样新地方
[2025-03-15 09:32:00] Alice：比想象中大！阳台能看到河
[2025-03-15 09:33:00] Sam：That's amazing, jealous
[2025-03-15 18:00:00] Alice：刚组装完书架，腰快断了
[2025-03-15 18:01:00] Sam：辛苦了！来暖房的时候我带酒
```

**Output (diary, concise style, Chinese, keep English quotes):**
```
今天搬进了新公寓，叫了搬家公司。比想象中大，阳台能看到河。Sam说That's amazing, jealous。傍晚组装完书架，腰快断了。Sam说来暖房的时候带酒。
```

**Output (diary, narrative style, Chinese):**
```
今天终于搬进了新公寓。叫了搬家公司来帮忙，到了才发现比想象中大不少，阳台居然能看到河，跟Sam分享的时候他说That's amazing, jealous。傍晚自己组装书架，搞了很久，腰快断了。Sam说来暖房的时候带酒过来。
```

**Minimal-information day:**
```
今天记录极少。
```

## Quality Checklist

Before outputting each diary entry, verify:
- [ ] Written in first person from the user's perspective
- [ ] No dialogue transcript format (no "A说...B说..." back and forth)
- [ ] Other participant referred to by name, not pronouns
- [ ] Length matches information density
- [ ] No invented content beyond what the chat supports
- [ ] Foreign quotes preserved if configured
