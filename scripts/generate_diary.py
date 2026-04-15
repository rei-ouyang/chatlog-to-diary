#!/usr/bin/env python3
"""
generate_diary.py — standalone diary generator (no Claude Code required).

Reads split chat files from a directory (output of split_by_date.py),
calls an LLM API to generate diary entries, and saves them to the output directory.

Supports:
  - Anthropic Claude API  (ANTHROPIC_API_KEY)
  - OpenAI-compatible API (OPENAI_API_KEY, or any base_url-compatible provider)

Usage:
    # Full pipeline: split then generate
    python3 scripts/split_by_date.py source/ --output-dir /tmp/chatlog-split
    python3 scripts/generate_diary.py --split-dir /tmp/chatlog-split

    # Or just generate from an already-split directory
    python3 scripts/generate_diary.py --split-dir /tmp/chatlog-split --config config.yaml

    # Skip interactive setup if config.yaml already exists
    python3 scripts/generate_diary.py --split-dir /tmp/chatlog-split --skip-setup

Environment variables:
    ANTHROPIC_API_KEY   — use Claude (default model: claude-3-5-haiku-20241022)
    OPENAI_API_KEY      — use OpenAI (default model: gpt-4o-mini)
    OPENAI_BASE_URL     — override base URL for OpenAI-compatible providers
    DIARY_MODEL         — override the model name
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    print("Error: PyYAML is required.\nInstall it with: pip install pyyaml", file=sys.stderr)
    sys.exit(1)


# ── Config helpers ────────────────────────────────────────────────────────────

DEFAULT_CONFIG = {
    "source_dir": "source/",
    "source_format": "auto",
    "output_dir": "output/",
    "diary_language": "zh",
    "user_labels": "",
    "chat_type": "private",
    "other_name": "",
    "group_name": "群",
    "writing_style": "concise",
    "keep_foreign_quotes": True,
    "foreign_languages": ["en", "ja"],
}

LANGUAGE_NAMES = {"zh": "Chinese", "en": "English", "ja": "Japanese"}


def load_config(config_path: Path) -> dict:
    cfg = dict(DEFAULT_CONFIG)
    if config_path.exists():
        with config_path.open(encoding="utf-8") as f:
            loaded = yaml.safe_load(f) or {}
        cfg.update(loaded)
    return cfg


def save_config(cfg: dict, config_path: Path) -> None:
    with config_path.open("w", encoding="utf-8") as f:
        yaml.dump(cfg, f, allow_unicode=True, default_flow_style=False, sort_keys=False)


def run_setup(config_path: Path) -> dict:
    """Interactive first-run setup. Returns the completed config dict."""
    print("\n── chatlog-to-diary setup ──────────────────────────────────────")
    print("Answer a few questions to configure the diary generator.")
    print("Press Enter to accept the default shown in [brackets].\n")

    cfg = dict(DEFAULT_CONFIG)

    cfg["source_dir"] = input("Where are your chat export files? [source/]: ").strip() or "source/"
    cfg["source_format"] = input("File format — txt / pdf / auto [auto]: ").strip() or "auto"
    cfg["output_dir"] = input("Where should diary files be saved? [output/]: ").strip() or "output/"
    cfg["diary_language"] = input("Diary language — zh / en / ja / other [zh]: ").strip() or "zh"

    chat_type = input("Chat type — private (1-on-1) or group [private]: ").strip() or "private"
    cfg["chat_type"] = chat_type if chat_type in ("private", "group") else "private"

    cfg["user_labels"] = input(
        "How does your name appear in chat logs? (comma-separated if multiple): "
    ).strip()

    if cfg["chat_type"] == "private":
        cfg["other_name"] = input("Other person's name or nickname: ").strip()
    else:
        cfg["group_name"] = input("Group label for the diary (e.g. 朋友群) [群]: ").strip() or "群"

    fq = input("Keep foreign-language quotes in original language? [yes]: ").strip().lower()
    cfg["keep_foreign_quotes"] = fq not in ("no", "n", "false")
    if cfg["keep_foreign_quotes"]:
        langs = input("Which languages to preserve? (comma-separated) [en, ja]: ").strip()
        cfg["foreign_languages"] = [l.strip() for l in langs.split(",")] if langs else ["en", "ja"]

    style = input("Writing style — concise / narrative [concise]: ").strip() or "concise"
    cfg["writing_style"] = style if style in ("concise", "narrative") else "concise"

    save_config(cfg, config_path)
    Path(cfg["source_dir"]).mkdir(parents=True, exist_ok=True)
    Path(cfg["output_dir"]).mkdir(parents=True, exist_ok=True)
    print(f"\n✓ Config saved to {config_path}")
    return cfg


# ── Prompt builder ────────────────────────────────────────────────────────────

def build_prompt(date_str: str, chat_text: str, cfg: dict) -> str:
    lang = cfg.get("diary_language", "zh")
    lang_name = LANGUAGE_NAMES.get(lang, lang)
    style = cfg.get("writing_style", "concise")
    user_labels_raw = cfg.get("user_labels", "")
    user_labels = [l.strip() for l in str(user_labels_raw).split(",") if l.strip()]
    chat_type = cfg.get("chat_type", "private")
    other_name = cfg.get("other_name", "")
    group_name = cfg.get("group_name", "群")
    keep_fq = cfg.get("keep_foreign_quotes", True)
    foreign_langs = cfg.get("foreign_languages", ["en", "ja"])

    user_label_str = ", ".join(f'"{l}"' for l in user_labels) if user_labels else "(not specified)"

    if chat_type == "group":
        participant_note = (
            f"This is a GROUP CHAT. The group is referred to as \"{group_name}\" in the diary.\n"
            f"Focus ONLY on what the user ({user_label_str}) said or arranged in the group.\n"
            "Ignore other participants' messages except when they directly relate to the user's actions.\n"
            "Do not attempt to summarise what other group members are doing with their lives."
        )
    else:
        participant_note = (
            f"This is a PRIVATE CHAT between the user and {other_name or 'the other person'}.\n"
            f"The user's name(s) in the log: {user_label_str}.\n"
            f"Refer to the other participant as \"{other_name}\" (not 他/她/they)."
        )

    fq_note = (
        f"Preserve quotes in these languages in their original form: {', '.join(foreign_langs)}."
        if keep_fq else
        "Translate all foreign-language quotes into the diary language."
    )

    style_note = (
        "Style: CONCISE. Event-driven, factual, short sentences. Focus on what happened."
        if style == "concise" else
        "Style: NARRATIVE. More detailed, include transitions, capture mood where evident."
    )

    return f"""You are converting a chat log into a first-person diary entry.

Date: {date_str}
Diary language: {lang_name}
{style_note}
{fq_note}

Participant context:
{participant_note}

Rules:
- Write in first person (我 / I / 私).
- Describe events, actions, and arrangements directly — not "I told X that..." or "X said Y".
  Good: "今天搬进了新公寓"  Bad: "我跟Sam说我搬到新公寓了"
- Write as if reflecting at the end of the day.
- No bullet points — flowing prose only.
- No headers, labels, or meta-commentary. Output only the diary text.
- Length proportional to information density:
  - Very few messages → one sentence, e.g. "今天记录极少。"
  - Light day → 2–4 sentences
  - Normal day → a short paragraph
  - Dense day → a full paragraph or two
- Do not invent emotions, intentions, or events not present in the chat.

Chat log:
{chat_text}

Write the diary entry now:"""


# ── LLM clients ──────────────────────────────────────────────────────────────

def call_anthropic(prompt: str, model: str) -> str:
    try:
        import anthropic
    except ImportError:
        print("Error: anthropic package required.\nInstall: pip install anthropic", file=sys.stderr)
        sys.exit(1)

    client = anthropic.Anthropic()
    message = client.messages.create(
        model=model,
        max_tokens=1024,
        messages=[{"role": "user", "content": prompt}],
    )
    return message.content[0].text.strip()


def call_openai(prompt: str, model: str, base_url: str | None = None) -> str:
    try:
        from openai import OpenAI
    except ImportError:
        print("Error: openai package required.\nInstall: pip install openai", file=sys.stderr)
        sys.exit(1)

    kwargs: dict = {}
    if base_url:
        kwargs["base_url"] = base_url

    client = OpenAI(**kwargs)
    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=1024,
    )
    return response.choices[0].message.content.strip()


def generate_entry(prompt: str) -> str:
    """Auto-select LLM backend based on available env vars."""
    model_override = os.environ.get("DIARY_MODEL", "")

    if os.environ.get("ANTHROPIC_API_KEY"):
        model = model_override or "claude-3-5-haiku-20241022"
        return call_anthropic(prompt, model)

    if os.environ.get("OPENAI_API_KEY"):
        model = model_override or "gpt-4o-mini"
        base_url = os.environ.get("OPENAI_BASE_URL")
        return call_openai(prompt, model, base_url)

    print(
        "Error: No API key found.\n"
        "Set ANTHROPIC_API_KEY or OPENAI_API_KEY in your environment.",
        file=sys.stderr,
    )
    sys.exit(1)


# ── Main ─────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate diary entries from split chat log files."
    )
    parser.add_argument(
        "--split-dir",
        type=Path,
        default=Path("/tmp/chatlog-split"),
        help="Directory containing per-date .txt files from split_by_date.py (default: /tmp/chatlog-split).",
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=Path("config.yaml"),
        help="Path to config.yaml (default: config.yaml in current directory).",
    )
    parser.add_argument(
        "--skip-setup",
        action="store_true",
        help="Skip interactive setup even if config.yaml does not exist; use defaults.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help="Override output directory from config.",
    )
    args = parser.parse_args()

    # ── Config
    if not args.config.exists() and not args.skip_setup:
        print(f"No config found at {args.config}. Starting setup...")
        cfg = run_setup(args.config)
    else:
        cfg = load_config(args.config)
        if not args.config.exists():
            print(f"Note: {args.config} not found; using built-in defaults (--skip-setup).")

    output_dir = args.output_dir or Path(cfg.get("output_dir", "output/"))
    output_dir.mkdir(parents=True, exist_ok=True)

    # ── Collect split files
    split_files = sorted(args.split_dir.glob("*.txt"))
    if not split_files:
        print(f"No .txt files found in {args.split_dir}.", file=sys.stderr)
        print("Run split_by_date.py first to produce per-date files.", file=sys.stderr)
        sys.exit(1)

    print(f"Found {len(split_files)} day(s) to process.\n")

    stats = {"new": 0, "appended": 0, "skipped": 0}

    for split_file in split_files:
        date_str = split_file.stem  # YYYY-MM-DD
        year = date_str[:4]

        chat_text = split_file.read_text(encoding="utf-8").strip()
        if not chat_text:
            print(f"  {date_str}: empty — skipped")
            stats["skipped"] += 1
            continue

        print(f"  {date_str}: generating...", end=" ", flush=True)
        prompt = build_prompt(date_str, chat_text, cfg)

        try:
            entry = generate_entry(prompt)
        except Exception as e:
            print(f"ERROR — {e}")
            stats["skipped"] += 1
            continue

        # Save output
        year_dir = output_dir / year
        year_dir.mkdir(parents=True, exist_ok=True)
        out_file = year_dir / f"{date_str}.md"

        if out_file.exists():
            existing = out_file.read_text(encoding="utf-8")
            out_file.write_text(existing.rstrip() + "\n\n" + entry + "\n", encoding="utf-8")
            print("appended")
            stats["appended"] += 1
        else:
            out_file.write_text(entry + "\n", encoding="utf-8")
            print("new")
            stats["new"] += 1

    print(
        f"\nDone: {stats['new']} new, {stats['appended']} appended, "
        f"{stats['skipped']} skipped → {output_dir}"
    )


if __name__ == "__main__":
    main()
