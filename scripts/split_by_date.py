#!/usr/bin/env python3
"""
Split chat log files by date.

Reads one or more chat export files (txt or pdf), auto-detects the format,
and outputs one .txt file per calendar day into the output directory.

Usage:
    python3 split_by_date.py source/ --output-dir /tmp/chatlog-split
    python3 split_by_date.py source/ --format pdf --output-dir /tmp/chatlog-split
    python3 split_by_date.py source/chat.txt --output-dir /tmp/chatlog-split
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


# ── Format detection patterns ────────────────────────────────────────────────

# Format A: [2025-01-01 12:00:00] Speaker：message
# Also handles [2025-01-01 12:00] and various separators (：, :)
WECHAT_MSG_RE = re.compile(
    r"^\[(\d{4}-\d{2}-\d{2})\s+(\d{2}:\d{2}(?::\d{2})?)\]\s*"
    r"([^：:]+)[：:](.*)$"
)

# Format B: LINE-style with date header and tab-separated messages
LINE_DATE_RE = re.compile(
    r"^(\d{4})/(\d{2})/(\d{2})"  # 2025/01/01 ...
)
LINE_MSG_RE = re.compile(
    r"^(\d{2}:\d{2})\t([^\t]+)\t(.*)$"
)

# Generic date separator lines: ── 2025年01月01日 ──, --- 2025-01-01 ---, etc.
DATE_SEPARATOR_RE = re.compile(
    r"(\d{4})\s*[年/-]\s*(\d{1,2})\s*[月/-]\s*(\d{1,2})"
)

# Fallback: any line starting with a date-like pattern
GENERIC_DATE_RE = re.compile(
    r"^.*?(\d{4})[/\-.](\d{1,2})[/\-.](\d{1,2})"
)

GENERIC_DATETIME_RE = re.compile(
    r"(\d{4})[/\-.](\d{1,2})[/\-.](\d{1,2})\s+(\d{2}:\d{2}(?::\d{2})?)"
)


# ── PDF text extraction ─────────────────────────────────────────────────────

def extract_text_from_pdf(path: Path) -> str:
    """Extract text from a PDF file using PyMuPDF (fitz)."""
    try:
        import fitz  # PyMuPDF
    except ImportError:
        print(
            "Error: PyMuPDF is required for PDF support.\n"
            "Install it with: pip install PyMuPDF",
            file=sys.stderr,
        )
        sys.exit(1)

    doc = fitz.open(str(path))
    pages: list[str] = []
    for page in doc:
        text = page.get_text()
        if text.strip():
            pages.append(text)
    doc.close()
    return "\n".join(pages)


# ── Parsing ──────────────────────────────────────────────────────────────────

def detect_and_parse(lines: list[str], source_name: str) -> dict[str, list[str]]:
    """
    Auto-detect chat format and parse lines into {date_str: [lines...]}.
    Returns a dict mapping "YYYY-MM-DD" to the list of raw lines for that day.

    Each line in the output is normalised to:
        [YYYY-MM-DD HH:MM] Speaker：message
    so downstream consumers always see a consistent format regardless of source.
    """
    # Try WeChat format first (most specific)
    result = _try_wechat(lines)
    if result:
        return result

    # Try LINE format
    result = _try_line(lines)
    if result:
        return result

    # Try generic date-separator format
    result = _try_separator(lines)
    if result:
        return result

    # Fallback: scan for any date patterns
    result = _try_generic(lines)
    if result:
        return result

    print(f"  Warning: could not detect format for {source_name}", file=sys.stderr)
    return {}


def count_speakers(days: dict[str, list[str]]) -> int:
    """
    Heuristic: count unique speakers across all parsed lines.
    Used to flag likely group chats (>2 speakers).
    """
    speakers: set[str] = set()
    for day_lines in days.values():
        for line in day_lines:
            m = WECHAT_MSG_RE.match(line)
            if m:
                speakers.add(m.group(3).strip())
    return len(speakers)


def _try_wechat(lines: list[str]) -> dict[str, list[str]] | None:
    """Parse WeChat-style: [YYYY-MM-DD HH:MM:SS] Speaker：message"""
    days: dict[str, list[str]] = {}
    matched = 0

    for line in lines:
        m = WECHAT_MSG_RE.match(line.strip())
        if m:
            date_str = m.group(1)  # YYYY-MM-DD
            days.setdefault(date_str, []).append(line.strip())
            matched += 1
        elif days:
            # Continuation line — append to the last day's last entry
            last_day = list(days.keys())[-1]
            if days[last_day]:
                days[last_day][-1] += " " + line.strip()

    # Need at least a few matches to consider this format valid
    if matched < 2:
        return None
    return days


def _try_line(lines: list[str]) -> dict[str, list[str]] | None:
    """Parse LINE-style: date header + tab-separated messages."""
    days: dict[str, list[str]] = {}
    current_date: str | None = None
    matched = 0

    for line in lines:
        raw = line.rstrip("\n")

        # Check for date header
        dm = LINE_DATE_RE.match(raw)
        if dm:
            y, m, d = dm.groups()
            current_date = f"{y}-{m}-{d}"
            days.setdefault(current_date, [])
            continue

        # Check for message line
        mm = LINE_MSG_RE.match(raw)
        if mm and current_date is not None:
            time_str, speaker, content = mm.groups()
            formatted = f"[{current_date} {time_str}] {speaker.strip()}：{content.strip()}"
            days[current_date].append(formatted)
            matched += 1
            continue

        # Continuation line
        if raw.strip() and current_date and days.get(current_date):
            days[current_date][-1] += " " + raw.strip()

    if matched < 2:
        return None
    return days


def _try_separator(lines: list[str]) -> dict[str, list[str]] | None:
    """Parse format with date separator lines (── 2025年01月01日 ──)."""
    days: dict[str, list[str]] = {}
    current_date: str | None = None
    has_separators = False

    for line in lines:
        raw = line.strip()
        if not raw:
            continue

        # Check if this line is a date separator
        sm = DATE_SEPARATOR_RE.search(raw)
        if sm and _looks_like_separator(raw):
            y, m, d = sm.groups()
            current_date = f"{y}-{int(m):02d}-{int(d):02d}"
            days.setdefault(current_date, [])
            has_separators = True
            continue

        if current_date and raw:
            days[current_date].append(raw)

    if not has_separators:
        return None
    return days


def _looks_like_separator(line: str) -> bool:
    """Check if a line looks like a date separator rather than a message."""
    # Separator lines typically have decorative characters or are short
    decorative = sum(1 for c in line if c in "─━—-=═~")
    return decorative >= 2 or len(line) < 30


def _try_generic(lines: list[str]) -> dict[str, list[str]] | None:
    """Fallback: extract dates from any recognizable pattern."""
    days: dict[str, list[str]] = {}
    current_date: str | None = None

    for line in lines:
        raw = line.strip()
        if not raw:
            continue

        dm = GENERIC_DATETIME_RE.search(raw)
        if dm:
            y, m, d, _ = dm.groups()
            current_date = f"{y}-{int(m):02d}-{int(d):02d}"
            days.setdefault(current_date, []).append(raw)
            continue

        dm = GENERIC_DATE_RE.match(raw)
        if dm:
            y, m, d = dm.groups()
            current_date = f"{y}-{int(m):02d}-{int(d):02d}"
            days.setdefault(current_date, []).append(raw)
            continue

        if current_date and raw:
            days[current_date].append(raw)

    if not days:
        return None
    return days


# ── File handling ────────────────────────────────────────────────────────────

def read_source_file(path: Path, fmt: str) -> list[str]:
    """Read a source file and return lines of text."""
    if fmt == "pdf" or (fmt == "auto" and path.suffix.lower() == ".pdf"):
        text = extract_text_from_pdf(path)
        return text.splitlines()

    # Default: read as text
    encodings = ["utf-8", "utf-8-sig", "gbk", "shift_jis", "euc-jp"]
    for enc in encodings:
        try:
            return path.read_text(encoding=enc).splitlines()
        except (UnicodeDecodeError, UnicodeError):
            continue

    print(f"  Warning: could not decode {path.name}, skipping", file=sys.stderr)
    return []


def collect_source_files(source_path: Path, fmt: str) -> list[Path]:
    """Collect all source files from a path (file or directory)."""
    if source_path.is_file():
        return [source_path]

    if not source_path.is_dir():
        print(f"Error: {source_path} is not a file or directory", file=sys.stderr)
        sys.exit(1)

    extensions = {".txt", ".pdf"} if fmt == "auto" else {f".{fmt}"}
    files = sorted(
        p for p in source_path.iterdir()
        if p.is_file() and p.suffix.lower() in extensions
    )
    return files


# ── Main ─────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Split chat log files by date."
    )
    parser.add_argument(
        "source",
        type=Path,
        help="Source file or directory containing chat exports.",
    )
    parser.add_argument(
        "--format", "-f",
        choices=["txt", "pdf", "auto"],
        default="auto",
        dest="fmt",
        help="Source file format (default: auto-detect from extension).",
    )
    parser.add_argument(
        "--output-dir", "-o",
        type=Path,
        default=Path("/tmp/chatlog-split"),
        help="Directory to write per-date output files (default: /tmp/chatlog-split).",
    )
    parser.add_argument(
        "--warn-group",
        action="store_true",
        help="Print a warning if more than 2 unique speakers are detected (likely a group chat).",
    )
    args = parser.parse_args()

    # Collect source files
    files = collect_source_files(args.source, args.fmt)
    if not files:
        print("No source files found.", file=sys.stderr)
        sys.exit(1)

    print(f"Found {len(files)} source file(s)")

    # Parse all files and merge by date
    all_days: dict[str, list[str]] = {}
    for path in files:
        print(f"  Parsing {path.name}...", end=" ")
        lines = read_source_file(path, args.fmt)
        if not lines:
            print("empty")
            continue

        days = detect_and_parse(lines, path.name)
        print(f"{len(days)} day(s)")

        if args.warn_group:
            n = count_speakers(days)
            if n > 2:
                print(
                    f"  Note: {n} unique speakers found in {path.name} — "
                    "this looks like a group chat. "
                    "Set chat_type: group in config.yaml for best results.",
                    file=sys.stderr,
                )

        for date_str, day_lines in days.items():
            all_days.setdefault(date_str, []).extend(day_lines)

    if not all_days:
        print("No dates found in any source file.", file=sys.stderr)
        sys.exit(1)

    # Write output files
    args.output_dir.mkdir(parents=True, exist_ok=True)

    written = 0
    for date_str in sorted(all_days.keys()):
        day_lines = all_days[date_str]
        if not day_lines:
            continue

        output_file = args.output_dir / f"{date_str}.txt"
        output_file.write_text("\n".join(day_lines) + "\n", encoding="utf-8")
        written += 1

    print(f"\nDone: {written} day(s) written to {args.output_dir}")


if __name__ == "__main__":
    main()
