#!/usr/bin/env python3
"""Stage C-E: remove MPV playback from exact Plezy 2.25.0 Fire TV source.

Apply after both apply_firetv_plex_only.py and apply_firetv_exoplayer_video.py.
This prepares source for a *later* manual build; it does not build or publish.
No music support is promised for this dedicated movies-and-TV edition.

The verified mpv-android AAR is downloaded as an INPUT only to extract
FFmpeg decoder libraries for Media3. Its MPV runtime and JNI glue are NOT
a Gradle implementation dependency and must NOT appear in the final APK.
"""
from pathlib import Path
import shutil
import subprocess


def replace_one(path: str, before: str, after: str) -> None:
    file = Path(path)
    data = file.read_text(encoding="utf-8")
    n = data.count(before)
    if n != 1:
        raise SystemExit(f"{path}: expected exactly one anchor, found {n}: {before[:110]!r}")
    file.write_text(data.replace(before, after), encoding="utf-8")
    print(f"ExoPlayer-only: modified {path}")


flag = Path("lib/services/firetv_build_flags.dart")
if not flag.exists() or "kFireTvForceExoVideo" not in flag.read_text(encoding="utf-8"):
    raise SystemExit("Plex-only + forced-ExoPlayer Stage B source overlays are required")

# The existing Flutter API remains intact: ExoPlayerCore still handles video,
# ASS subtitles, Dolby Vision conversion, decoder recovery and error reporting.
# Native MPV does not exist, including on unsupported format failures.
src = Path("scripts/firetv_exoplayer_only_plugin/ExoPlayerPlugin.kt")
if not src.is_file():
    raise SystemExit("Missing reviewed ExoPlayer-only plugin source")
dest = Path("android/app/src/main/kotlin/com/edde746/plezy/exoplayer/ExoPlayerPlugin.kt")
if not dest.exists() or "usingMpvFallback" not in dest.read_text(encoding="utf-8"):
    raise SystemExit("Unexpected upstream ExoPlayer plugin: review before replacing")
shutil.copyfile(src, dest)
print("ExoPlayer-only: replaced native plugin with a Media3-only bridge")

activity = "android/app/src/main/kotlin/com/edde746/plezy/PlezyActivity.kt"
replace_one(activity, "import com.edde746.plezy.mpv.MpvAudioPlayerPlugin\n", "")
replace_one(activity, "import com.edde746.plezy.mpv.MpvPlayerPlugin\n", "")
replace_one(activity, "    flutterEngine.plugins.add(MpvPlayerPlugin())\n", "")
replace_one(activity, "    flutterEngine.plugins.add(MpvAudioPlayerPlugin())\n", "")

# Build-time dependency only: the pinned and SHA-verified AAR is still used for
# FFmpeg 8.0.1 decoder .so files. Removing its implementation dependency means
# Gradle cannot merge libmpv JNI, mpv classes or its bundled player engine
# into the final APK. We keep its selective standalone extraction.
gradle = "android/app/build.gradle.kts"
replace_one(
    gradle,
    '  implementation(mpvAarDependency)\n  mpvAarNatives(mpvAarDependency)',
    '  // Media3 FFmpeg decoders extracted from a checksum-pinned build-time AAR only.\n'
    '  // Do NOT link the full mpv-android AAR: it would package native libmpv.\n'
    '  mpvAarNatives(mpvAarDependency)',
)

# This device never exposes Plex music; throw explicitly if a stray route
# attempts to open a legacy audio-only MPV player. Do not change other builds.
player = "lib/mpv/player/player.dart"
replace_one(
    player,
    "  factory Player.audio() {\n",
    "  factory Player.audio() {\n"
    "    if (Platform.isAndroid && kFireTvForceExoVideo) {\n"
    "      throw UnsupportedError('Music playback is not included in this Fire TV movies-and-TV edition');\n"
    "    }\n",
)

# With only Media3 video, a native player factory can no longer ever choose
# MPV. Remove Kotlin MPV implementation sources in this *candidate checkout*,
# never from the maintained automation/upstream source branch. Android MPV tests
# are excluded because they explicitly exercise removed MPV runtime interfaces.
native_mpv = Path("android/app/src/main/kotlin/com/edde746/plezy/mpv")
if not native_mpv.is_dir() or not (native_mpv / "MpvPlayerCore.kt").exists():
    raise SystemExit("Expected upstream native MPV directory missing")
shutil.rmtree(native_mpv)
for relative in (
    "android/app/src/main/kotlin/com/edde746/plezy/shared/MpvContentUriResolver.kt",
):
    target = Path(relative)
    if not target.is_file():
        raise SystemExit(f"Expected MPV-only source missing: {relative}")
    target.unlink()

native_tests = Path("android/app/src/test")
if native_tests.exists():
    for f in native_tests.rglob("*.kt"):
        source = f.read_text(encoding="utf-8", errors="replace")
        # Target native MPV unit tests only; retain ExoPlayer/Media3 tests.
        if "/mpv/" in f.as_posix().lower() or (
            "com.edde746.plezy.mpv." in source
            or "com.edde746.mpv." in source
        ):
            f.unlink()
            print(f"ExoPlayer-only: removed MPV-specific native test {f}")

# Retain libass/libdovi and FFmpeg; do not confuse shared 'mpv' Dart package
# naming with the shipped player engine. Dart AOT still carries the common
# Player API, which ExoPlayer uses.
source_map = {
    "android/app/src/main/kotlin/com/edde746/plezy/exoplayer/ExoPlayerPlugin.kt": [
        "class ExoPlayerPlugin", 'result.success("exoplayer")', "override fun onFormatUnsupported("
    ],
    "android/app/src/main/kotlin/com/edde746/plezy/PlezyActivity.kt": [
        "flutterEngine.plugins.add(ExoPlayerPlugin())"
    ],
    "android/app/build.gradle.kts": ["mpvAarNatives(mpvAarDependency)"],
}
for p, required in source_map.items():
    data = Path(p).read_text(encoding="utf-8")
    for marker in required:
        if data.count(marker) != 1:
            raise SystemExit(f"{p}: expected one marker {marker!r}")

native_bridge = dest.read_text(encoding="utf-8")
for forbidden in (
    "MpvPlayerCore", "usingMpvFallback", "MpvPlayerPlugin",
    "MpvAudioPlayerPlugin", "import com.edde746.plezy.mpv."
):
    if forbidden in native_bridge:
        raise SystemExit(f"Native ExoPlayer bridge still references MPV: {forbidden}")

# Update the original ExoPlayerCore misleading callback comments and remove
# its test-only explicit trigger method. Format errors already call the
# delegate; new bridge returns false and core emits the terminal error once.
core = "android/app/src/main/kotlin/com/edde746/plezy/exoplayer/ExoPlayerCore.kt"
replace_one(
    core,
    "   * The plugin should handle fallback to MPV.\n"
    "   * @return true if fallback was handled, false to emit error event to Flutter",
    "   * Return false to emit a terminal error to Flutter for unsupported formats.\n"
    "   * The Fire TV edition deliberately has no alternative MPV playback engine.",
)
core_text = Path(core).read_text(encoding="utf-8")
start = core_text.index("  fun triggerFallback() {\n")
end = core_text.index("  // Cleanup\n", start)
if core_text.count("  fun triggerFallback() {\n") != 1:
    raise SystemExit("Unexpected ExoPlayerCore fallback trigger layout")
Path(core).write_text(core_text[:start] + core_text[end:], encoding="utf-8")

# Stage B selection remains true and *only* video is supported on this target.
# If a source refactor removes this guard in a later upstream version, fail.
if "kFireTvForceExoVideo" not in Path(player).read_text(encoding="utf-8"):
    raise SystemExit("Forced ExoPlayer player-factory guard missing")
print("Prepared Fire TV movies/TV only source: native MPV removed; Media3 FFmpeg retained.")
print("NOT yet compiled. Source and compiled APK must be inspected before device installation.")
