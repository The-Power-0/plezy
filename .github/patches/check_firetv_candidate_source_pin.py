#!/usr/bin/env python3
"""Ensure the manual candidate checks out selected SHA, not production."""
from pathlib import Path
s=Path(".github/workflows/firetv-no-mpv-candidate.yml").read_text(encoding="utf-8")
checks=(
    "ref: ${{ github.sha }}",
    'test "$(git rev-parse HEAD)" = "$SELECTED_SHA"',
    "test -f .github/patches/apply_firetv_no_music_restore.py",
    "git fetch --force upstream-release",
    "python3 scripts/apply_firetv_no_music_restore.py",
)
for marker in checks:
    if marker not in s: raise SystemExit("Missing provenance guard: "+marker)
if "ref: ha-shuffle-v2" in s: raise SystemExit("Candidate checks out production")
if s.index('test "$(git rev-parse HEAD)"') > s.index("git fetch --force upstream-release"):
    raise SystemExit("SHA verification must precede upstream checkout")
if "  workflow_dispatch:" not in s or "\n  push:" in s: raise SystemExit("Workflow must be manual")
print("Selected-commit candidate source pin validated; no APK compiled.")
