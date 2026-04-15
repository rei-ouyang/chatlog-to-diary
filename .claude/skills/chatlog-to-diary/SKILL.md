---
name: chatlog-to-diary
description: Convert chat logs into first-person diary entries. Use when user says "生成日记", "generate diary", "转日记", "chatlog to diary", or wants to convert chat export files into diary entries.
allowed-tools: Bash(python3:*) Bash(mkdir:*) Bash(ls:*)
---

# chatlog-to-diary

Convert chat logs into first-person diary entries.

## Mode Selection

Check whether `config.yaml` exists in the project root.

- If **no** `config.yaml` → run First-Run Setup
- If `config.yaml` exists → run Daily Generation (skip setup entirely)

## First-Run Setup

Ask the user the following questions **one at a time** (have a conversation, don't dump all at once):

1. **Source path**: "Where are your chat export files? (default: `source/`)"
2. **Source format**: "What format are they in? (txt / pdf / auto)"
3. **Output directory**: "Where should I save the diary files? (default: `output/`)"
4. **Diary language**: "What language should the diary be in? (zh / en / ja / other)"
5. **Chat type**: "Is this a private chat (1-on-1) or a group chat? (private / group)"
6. **User labels**: "How does your name appear in the chat logs? You may have different names across apps — list all aliases separated by commas. (e.g. 我, Alice, アリス)"
7. **Other participant / group name**:
   - If private: "What's the other person's name or nickname? (used when referring to them in the diary)"
   - If group: "What should I call this group in the diary? (e.g. 朋友群, 旅行小队)"
8. **Foreign quotes**: "Should I keep the other person's foreign-language quotes in their original language? (yes/no)" — if yes, ask "Which languages? (e.g., en, ja)"
9. **Writing style**: "Do you prefer concise event-driven entries or more detailed narrative style? (concise / narrative)"

After collecting all answers, write `config.yaml` and create directories:
```bash
mkdir -p source/ output/
```

Confirm setup is complete.

## Daily Generation

**Step 1 — Split chat logs by date**

```bash
python3 scripts/split_by_date.py <source_dir> --format <source_format> --output-dir /tmp/chatlog-split --warn-group
```

Produces one `.txt` file per date in `/tmp/chatlog-split/`, named `YYYY-MM-DD.txt`.

If `--warn-group` prints a warning about multiple speakers, remind the user to set `chat_type: group` in `config.yaml` if this is indeed a group chat.

**Step 2 — Generate diary for each date**

Read config values from `config.yaml`. For each date file, read the chat content and generate a diary entry following these rules:

### Diary Generation Rules (private chat)

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
- Length proportional to information density:
  - Very few messages → one sentence, e.g., "今天记录极少。"
  - Light day → 2-4 sentences
  - Normal day → a short paragraph
  - Dense day → a full paragraph or two
- Output the diary entry only — no labels, no headers, no explanations

### Diary Generation Rules (group chat)

Group chats are inherently noisy — focus only on what the **user** said or arranged:

- Use the group label (from config `group_name`) when referring to the group, e.g., "在朋友群里约好了周六打球。"
- Only include the user's own messages and the concrete outcomes that involved the user
- Ignore side conversations that don't involve the user
- Do not summarise what other group members are doing with their lives — group chat is not a reliable source for that
- Keep entries short; most group chat days will be 1–3 sentences
- If the user said nothing meaningful in the group that day: "今天记录极少。"

### User Labels Across Multiple Apps

The user may appear under different names in different chat files (e.g. "Alice" in WeChat, "アリス" in LINE). The `user_labels` config field is a comma-separated list of all aliases. When identifying the user's messages, match against **any** of these labels.

### Writing Style Variations

- `concise`: event-driven, factual, short sentences. Focus on what happened.
- `narrative`: more detailed, includes transitions, captures mood when evident from chat.

**Step 3 — Save to output directory**

Save each diary entry to `<output_dir>/YYYY/YYYY-MM-DD.md`.

**Important**: if the output file already exists, **append** (with a blank line separator). Never overwrite existing diary content.

Create year subdirectories as needed.

**Step 4 — Report**

Tell the user:
- How many days were processed
- How many were new vs appended
- How many were skipped (no meaningful content)
- Where the output files are

## Quality Checklist

Before outputting each diary entry, verify:
- [ ] Written in first person from the user's perspective
- [ ] No dialogue transcript format (no "A说...B说..." back and forth)
- [ ] Private chat: other participant referred to by name, not pronouns
- [ ] Group chat: only user's own actions and outcomes included
- [ ] Length matches information density
- [ ] No invented content beyond what the chat supports
- [ ] Foreign quotes preserved if configured

## Style Examples

All examples below use fictional people and events.

### Private chat

**Input (chat log):**
```
[2025-03-15 09:30:00] Alice：今天搬到新公寓了，叫了个搬家公司
[2025-03-15 09:31:00] Sam：怎么样新地方
[2025-03-15 09:32:00] Alice：比想象中大！阳台能看到河
[2025-03-15 09:33:00] Sam：That's amazing, jealous
[2025-03-15 18:00:00] Alice：刚组装完书架，腰快断了
[2025-03-15 18:01:00] Sam：辛苦了！来暖房的时候我带酒
```

**Output (concise, Chinese, keep English quotes):**
```
今天搬进了新公寓，叫了搬家公司。比想象中大，阳台能看到河。Sam说That's amazing, jealous。傍晚组装完书架，腰快断了。Sam说来暖房的时候带酒。
```

**Output (narrative, Chinese):**
```
今天终于搬进了新公寓。叫了搬家公司来帮忙，到了才发现比想象中大不少，阳台居然能看到河，跟Sam分享的时候他说That's amazing, jealous。傍晚自己组装书架，搞了很久，腰快断了。Sam说来暖房的时候带酒过来。
```

### Group chat

**Input (group chat log, user = Alice, group_name = 朋友群):**
```
[2025-04-01 20:00:00] 小明：周末有人打球吗
[2025-04-01 20:01:00] Alice：我可以！周六下午
[2025-04-01 20:02:00] 小红：我也去
[2025-04-01 20:03:00] Alice：太好了，那约球场吧
[2025-04-01 20:10:00] 小明：小红你最近工作怎么样
[2025-04-01 20:11:00] 小红：还行，就是很忙
```

**Output (concise, Chinese — only user's contribution):**
```
在朋友群里约好了周六下午打球，顺便约了球场。
```

### Minimal-information day
```
今天记录极少。
```
