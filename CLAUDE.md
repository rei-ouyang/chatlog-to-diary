# chatlog-to-diary

Convert chat logs into first-person diary entries.

## Overview

This tool reads exported chat logs (txt or pdf), splits them by date, and generates a first-person diary entry for each day.

## Usage

Run `/chatlog-to-diary` to start. The skill handles both first-run setup (creating `config.yaml`) and daily diary generation.

## Project Structure

- `scripts/split_by_date.py` — splits chat logs into per-date files
- `config.yaml` — user configuration (created on first run)
- `config.example.yaml` — example configuration
- `source/` — chat export files go here
- `output/` — generated diary entries saved here
