#!/usr/bin/env python3
"""Heuristic static audit of all tracked app-source lines for Fire TV hot paths.

This deliberately scans all tracked, readable app source. It cannot measure
performance or prove a line is slow: on-device profiling is still required.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from pathlib import Path
import re
import subprocess

ROOTS = ("lib/", "android/", "packages/", "windows/")
SOURCE_SUFFIXES = (".dart", ".kt", ".java", ".cpp", ".cc", ".c", ".h", ".hpp", ".kts", ".gradle", ".xml")
CHECKS = {
    "periodic_timer": re.compile(r"\bTimer\.periodic\s*\("),
    "frame_callback": re.compile(r"\b(addPostFrameCallback|addPersistentFrameCallback|addTimingsCallback)\s*\("),
    "widget_rebuild": re.compile(r"\b(setState|notifyListeners)\s*\("),
    "overlay_or_effect": re.compile(r"(BackdropFilter|ShaderMask|ImageFilter\.blur|Opacity\s*\(|AnimatedOpacity\s*\()"),
    "network_or_connect": re.compile(r"\b(connect|fetch|request|HttpClient|http\.(get|post)|Dio)\s*\("),
    "json_or_decode": re.compile(r"\b(jsonDecode|json\.decode|jsonEncode|json\.encode|compute)\s*\("),
    "concurrent_work": re.compile(r"\b(Future\.wait|\.wait|scheduleMicrotask)\b"),
    "jellyfin_or_emby": re.compile(r"\b(Jellyfin|Emby|jellyfin|emby)\b"),
}
WEIGHTS = {
    "periodic_timer": 7,
    "frame_callback": 4,
    "widget_rebuild": 2,
    "overlay_or_effect": 2,
    "network_or_connect": 1,
    "json_or_decode": 3,
    "concurrent_work": 2,
    "jellyfin_or_emby": 0,
}

def is_generated(path: str) -> bool:
    return path.endswith((".g.dart", ".freezed.dart", ".gr.dart", ".mocks.dart", ".gen.dart")) or "/build/" in path

def audit() -> str:
    paths = subprocess.check_output(["git", "ls-files", "-z"]).decode("utf-8", "replace").split("\0")
    totals = Counter()
    scores = defaultdict(Counter)
    samples: dict[str, list[tuple[str, int, str]]] = defaultdict(list)
    for name in paths:
        if not name.startswith(ROOTS) or not name.endswith(SOURCE_SUFFIXES):
            continue
        file = Path(name)
        if not file.is_file():
            continue
        try:
            # Read every line; skip binary/unreadable assets even when extension matches.
            with file.open(encoding="utf-8") as f:
                totals["scanned_files"] += 1
                for number, line in enumerate(f, 1):
                    totals["scanned_lines"] += 1
                    generated = is_generated(name)
                    if generated:
                        totals["generated_lines"] += 1
                    for key, regex in CHECKS.items():
                        if regex.search(line):
                            totals[key] += 1
                            if not generated:
                                scores[name][key] += 1
                                if len(samples[key]) < 14:
                                    samples[key].append((name, number, line.strip()[:140]))
        except (UnicodeError, OSError):
            totals["unreadable_files"] += 1

    high = []
    for path, counts in scores.items():
        score = sum(WEIGHTS[k] * n for k, n in counts.items())
        if score:
            high.append((score, path, counts))
    high.sort(reverse=True)

    out = [
        "PLEZY FIRE TV PLEX-ONLY: FULL TRACKED APP-SOURCE STATIC SCAN",
        "=" * 68,
        "Heuristic audit only. Source-pattern counts are NOT performance timings.",
        "Do not remove accessibility, playback, Plex auth, or caching without tests.",
        "",
        f"Source files inspected: {totals['scanned_files']:,}",
        f"Source lines inspected: {totals['scanned_lines']:,}",
        f"Generated source lines (included in coverage, excluded from ranking): {totals['generated_lines']:,}",
        f"Unreadable files: {totals['unreadable_files']:,}",
        "",
        "Occurrence counts (can include comments and tests in packaged source):",
    ]
    out.extend(f"  {key}: {totals[key]:,}" for key in CHECKS)
    out.extend(["", "Highest static-pattern scores (not necessarily slow at runtime):"])
    out.extend(f"  {score:4}  {path}  {dict(counts)}" for score, path, counts in high[:45])
    out.append("")
    out.append("Candidate call-site examples to profile on Fire TV:")
    for key in ("periodic_timer", "frame_callback", "widget_rebuild", "overlay_or_effect", "json_or_decode"):
        out.append(f"  {key}:")
        out.extend(f"    {path}:{line_num}  {source}" for path, line_num, source in samples[key])
    out.extend([
        "",
        "Next steps: compare cold/warm launch latency, UI frame timings, Plex artwork",
        "first-paint latency, ADB PSS/RSS, and shuffled-show first-frame/episode gaps",
        "on 1GB Fire OS 7 and 2GB Fire OS 8 hardware before changing hot paths.",
        "",
    ])
    return "\n".join(out)

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = audit()
    args.output.write_text(report, encoding="utf-8")
    print("\n".join(report.splitlines()[:22]))
    print(f"Full source audit: {args.output}")

if __name__ == "__main__":
    main()
