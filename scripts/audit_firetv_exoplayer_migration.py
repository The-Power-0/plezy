#!/usr/bin/env python3
"""Evidence-only MPV retirement audit for the exact patched Plezy upstream tree.

Run in the checked-out, patched release source:
  python3 scripts/audit_firetv_exoplayer_migration.py --output ExoPlayer-Migration-Audit.json

No mutations. The audit NEVER reports final migration readiness based only on
source-pattern matching; device/codec tests and binary inspection are required.
"""
from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path
import re
import subprocess

SOURCE_EXTENSIONS = {".dart", ".kt", ".java", ".kts", ".cpp", ".cc", ".c", ".h", ".xml", ".gradle", ".pro", ".yaml"}
ROOTS = ("lib/", "android/", "packages/", "test/", "scripts/")
BINARY_EXTENSIONS = {".so", ".aar", ".a", ".jar"}
CATEGORIES = {
    "mpv_symbol": re.compile(r"\b(?:libmpv|MPV|Mpv[A-Za-z_]*|mpv[A-Za-z_]*)\b", re.I),
    "mpv_native": re.compile(r"(?:MpvPlayerCore|MpvPlayerPlugin|MpvAudioPlayerPlugin|mpvAarDependency|mpvAarNatives|MPV_FFMPEG_ROOT)"),
    "fallback": re.compile(r"(?:triggerFallback|onFormatUnsupported|usingMpvFallback|setupMpvFallback|fallbackInProgress|backend-switched)"),
    "audio_factory": re.compile(r"(?:Player\.audio\(|PlayerNative\.audio\(|_audioPlayerFactory|setNext\()"),
    "exoplayer": re.compile(r"(?:ExoPlayerCore|ExoPlayerPlugin|PlayerAndroid|media3-exoplayer|DefaultRenderersFactory)"),
    "ffmpeg": re.compile(r"(?:FFmpeg|ffmpeg|libavcodec|libavutil|libswresample|ffmpegJNI)"),
    "subtitle": re.compile(r"(?:SecondarySubtitle|secondary.subtitle|libass|AssSubtitle|subtitleRenderScale)"),
    "build": re.compile(r"(?:signingConfig|release|abiFilters|jniLibs|R8|proguard|externalNativeBuild)"),
}
REQUIRED = {
    "lib/mpv/player/player.dart": ("PlayerNative.audio()", "return PlayerNative(hardwareDecoding:"),
    "lib/mpv/player/platform/player_android.dart": ("usingMpvFallback", "backend-switched"),
    "lib/services/music/music_playback_service_impl.dart": ("Player.audio",),
    "android/app/src/main/kotlin/com/edde746/plezy/PlezyActivity.kt": ("MpvAudioPlayerPlugin", "ExoPlayerPlugin"),
    "android/app/src/main/kotlin/com/edde746/plezy/exoplayer/ExoPlayerPlugin.kt": ("MpvPlayerCore", "usingMpvFallback"),
    "android/app/src/main/kotlin/com/edde746/plezy/exoplayer/ExoPlayerCore.kt": ("onFormatUnsupported",),
    "android/app/build.gradle.kts": ("mpvAarDependency", "mpvAarNatives", "media3-exoplayer"),
    "android/app/src/main/cpp/CMakeLists.txt": ("MPV_FFMPEG_ROOT", "ffmpegJNI"),
}
HOT_MODULES = {
    "video_engine_factory": "lib/mpv/player/player.dart",
    "android_exoplayer_bridge": "lib/mpv/player/platform/player_android.dart",
    "native_fallback": "android/app/src/main/kotlin/com/edde746/plezy/exoplayer/ExoPlayerPlugin.kt",
    "native_exoplayer": "android/app/src/main/kotlin/com/edde746/plezy/exoplayer/ExoPlayerCore.kt",
    "music": "lib/services/music/music_playback_service_impl.dart",
    "activity": "android/app/src/main/kotlin/com/edde746/plezy/PlezyActivity.kt",
    "gradle": "android/app/build.gradle.kts",
    "cmake": "android/app/src/main/cpp/CMakeLists.txt",
}
def audit() -> dict:
    paths = subprocess.check_output(["git", "ls-files", "-z"]).decode("utf-8").split("\0")
    metrics = Counter()
    matches: dict[str, list[dict]] = {key: [] for key in CATEGORIES}
    per_file = {}
    native_sources = []
    warnings = []
    for path in paths:
        if not path.startswith(ROOTS):
            continue
        file = Path(path)
        if not file.is_file():
            continue
        if file.suffix in BINARY_EXTENSIONS:
            native_sources.append(path)
            continue
        if file.suffix not in SOURCE_EXTENSIONS:
            continue
        try:
            lines = file.read_text(encoding="utf-8").splitlines()
        except (OSError, UnicodeError):
            warnings.append(f"Unreadable source: {path}")
            continue
        metrics["source_files"] += 1
        metrics["source_lines"] += len(lines)
        file_counts = Counter()
        for number, line in enumerate(lines, 1):
            for name, pattern in CATEGORIES.items():
                if pattern.search(line):
                    metrics[name] += 1
                    file_counts[name] += 1
                    # Bounded excerpt sample; full source remains in the repo.
                    if len(matches[name]) < 250:
                        matches[name].append({
                            "path": path, "line": number,
                            "excerpt": line.strip()[:190],
                        })
        if file_counts:
            per_file[path] = dict(file_counts)
    blocker_anchors = {}
    for path, anchors in REQUIRED.items():
        try:
            s = Path(path).read_text(encoding="utf-8")
        except (OSError, UnicodeError):
            blocker_anchors[path] = {"exists": False, "anchors": {k: False for k in anchors}}
            continue
        blocker_anchors[path] = {
            "exists": True, "anchors": {key: key in s for key in anchors}
        }
    ranked = sorted(
        per_file.items(),
        key=lambda kv: kv[1].get("mpv_native", 0) * 7
          + kv[1].get("fallback", 0) * 5
          + kv[1].get("audio_factory", 0) * 4
          + kv[1].get("mpv_symbol", 0),
        reverse=True,
    )
    return {
        "audit_kind": "source_inventory_only",
        "migration_ready": False,
        "migration_ready_reason": "Native binary audit, music migration, independent FFmpeg, codec parity and device regression testing required.",
        "repository_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
        "coverage": dict(metrics),
        "hot_modules": HOT_MODULES,
        "known_blocker_anchors": blocker_anchors,
        "source_mentions": matches,
        "top_mpvspecific_files": [{"path": p, "counts": c} for p, c in ranked[:100]],
        "tracked_native_binary_paths": native_sources[:200],
        "warnings": warnings,
        "notes": [
            "Source mentions include comments/tests and are not reachable-code analysis.",
            "An absent source symbol does not prove a native MPV library is absent from the APK.",
            "Do not remove libass or FFmpeg simply because MPV previously supplied their libraries.",
            "Never commit signing keys or Plex access tokens in audit artifacts."
        ],
    }

def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--output", required=True, type=Path)
    args = ap.parse_args()
    result = audit()
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(f"Analyzed {result['coverage'].get('source_files', 0)} source files, "
          f"{result['coverage'].get('source_lines', 0)} source lines")
    print("MPV migration ready: NO — source inventory alone never approves native removal")
    for path, results in result["known_blocker_anchors"].items():
        print(path, "present=" + str(results["exists"]), "anchors=" + str(results["anchors"]))

if __name__ == "__main__":
    main()
