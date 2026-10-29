# Fire TV Plex-only: MPV retirement and ExoPlayer-only migration

Status: **design and automated audit only**, NOT an ExoPlayer-only APK yet.

Source baseline: upstream Plezy `2.25.0` as fetched and patched by the existing Home Assistant shuffle and Plex-only candidate workflows. Apply these changes only to the isolated Fire TV build. Preserve `ha-shuffle-v2`, `Plezy.apk`, Home Assistant scripts, package ID, signing key, and exact GPL corresponding source. Do not modify ordinary upstream or future Windows builds.

## Required outcome

- Android Fire OS 7 (API 28) and Fire OS 8 (API 30), `armeabi-v7a`; Plex only.
- ExoPlayer/Media3 handles **all** video and music, including continuous shuffled Plex queues.
- No MPV player, native `libmpv`, MPV Flutter plugin, hidden runtime fallback, or native MPV playback path in the final APK.
- Keep hardware decoding, audio passthrough where supported, codec negotiation, Plex transcode fallback, subtitles, track selection, resume, seeks, Live TV, offline files, Plex Home users/profiles, and existing `plezy://shuffle` and native deep links.
- Keep the FFmpeg audio decoder (if needed for supported content) through an **independently packaged and checksum-verified** native FFmpeg build. ExoPlayer is still the *only player engine*: FFmpeg is a decoder library, not MPV.
- Keep libass overlay and libdovi bridge if required by ExoPlayer; do not mistake these for MPV-only modules.
- Preserve licensing, build provenance, exact source archive, signatures, and rollback.

## Confirmed blockers in upstream 2.25.0

1. **Native ExoPlayer fallback**: `android/app/src/main/kotlin/com/edde746/plezy/exoplayer/ExoPlayerPlugin.kt` imports `MpvPlayerCore` and hands unsupported/decode-failure paths to MPV. `ExoPlayerCore.kt` requests fallback. Failures must instead be classified into recoverable ExoPlayer retry, Plex transcode/alternate source, and terminal errors—without infinite retries or treating HTTP authorization errors as codec errors.
2. **Default video engine**: `lib/mpv/player/player.dart` defaults Android to `PlayerNative` unless `useExoPlayer` is true; `SettingsService.useExoPlayer` is user-editable. A Fire TV compile-time flag must force `PlayerAndroid` and suppress misleading backend selection, while keeping ordinary builds untouched.
3. **MPV music engine**: `Player.audio()` returns `PlayerNative.audio()` on Android, and `MusicPlaybackServiceImpl` uses `Player.audio`. Simply removing the native MPV plugins would break music, background playback, gapless advance, and music audio focus. Implement a dedicated ExoPlayer audio session with independent channel/lifecycle behavior and queue handoff semantics, or explicitly gate music until exact parity is achieved; the stated target is parity.
4. **FFmpeg packaging dependency**: `android/app/build.gradle.kts` pulls `mpvAarDependency`, extracts the FFmpeg `libavcodec`, `libavutil`, `libswresample`, plus `libc++_shared`. `android/app/src/main/cpp/CMakeLists.txt` builds `ffmpegJNI` against `MPV_FFMPEG_ROOT`. Cutting the mpv AAR before supplying independently built ABI-compatible FFmpeg/libc++ would silently break TrueHD/DTS-HD/etc. Preserve pinned FFmpeg source/version and checksum, and run decoder reachability/R8 tests.
5. **Native plugin registration**: `PlezyActivity.kt` registers `MpvPlayerPlugin`, `ExoPlayerPlugin`, and `MpvAudioPlayerPlugin`. Final builds must register only ExoPlayer video/audio implementations, with safe plugin teardown and no stale method channels.
6. **Subtitle/feature gaps**: `PlayerAndroid.supportsSecondarySubtitles == false`; deinterlacing and several MPV shader/filter controls do not have ExoPlayer equivalents. Do not claim complete feature parity until tested or implemented (for instance, secondary subtitles using dual libass overlays). Preserve primary ASS/SSA/PGS/SRT where supported.
7. **Shared Dart interface**: `lib/mpv/player/player_base.dart`, `models.dart`, `video.dart`, player-state streams, track selection, and numerous screen/services remain common to both engines. Refactor *interfaces*, not wholesale delete `lib/mpv/` before call sites compile.

## Implementation gates (independent, reviewable PRs)

### Gate A — Inventory, audit, reproducible measurement (this PR)

- Collect source-level MPV, ExoPlayer, FFmpeg, and music dependency anchors from the **exact patched upstream candidate**.
- Generate machine-readable JSON and readable Markdown reports, with file/line evidence and explicit blockers.
- Source inventory is not a benchmark; add cold/warm startup, D-pad frame times, memory/PSS, Plex first-frame, and shuffle/episode transition baselines on both Fire OS versions.
- No production code or shipped APK behavior changes in this gate.

### Gate B — Force ExoPlayer for Fire TV video

- Introduce `PLEZY_FIRETV_EXO_ONLY` compile-time flag default **false**; true only for the Fire TV candidate. Do not reuse a runtime preference as the build guard.
- Force `PlayerAndroid` on Android, hide backend option and MPV-specific settings in this variant, retain stored preferences (do not delete them).
- Keep MPV native library temporarily only during this **intermediate test** so non-Exo fallback regressions can be measured and classified. This is explicitly NOT the final Exo-only APK.
- Validate known codec sample files and native deep links before proceeding.

### Gate C — Replace native fallback behavior

- Implement typed errors from ExoPlayer without any MPV handover. Distinguish unsupported video/audio codec, HTTP/DRM/authentication errors, decoder stalls, and device buffer pressure.
- For server-hosted Plex items, attempt a bounded alternate-media-source or server transcode path where supported; otherwise show a meaningful error. Do not falsely advertise guaranteed transcoding for all files.
- Retain existing decoder retry, stall, and recovery guardrails; validate seek, resume, and queue advancement.

### Gate D — Migrate Plex music to ExoPlayer

- Replace `Player.audio()`'s Android MPV core with a dedicated audio-only ExoPlayer instance and channels; preserve media session, gapless `setNext`, audio focus, idle/background lifecycle, notifications, track transition streams, volume/rate, and failure recovery.
- Test long music playlists, gapless transition semantics, play/pause, next/back, app backgrounding, and video/music ownership handoff.

### Gate E — Decouple FFmpeg and remove MPV binaries

- Build or retrieve a pinned, verified independent Android FFmpeg decoder artifact compatible with Media3's `ffmpegJNI` and the exact ARMv7 ABI. Verify licenses and dynamic library dependencies.
- Remove `mpvAarDependency`, MPV-specific native Kotlin modules, plugin registrations, compiled MPV core assets, and unused config screens. Retain libass, libdovi, FFmpeg audio decoder, and any other libraries ExoPlayer actually uses.
- Refactor shared abstractions only after compile/usage analysis. Inspect the final APK ZIP: **zero** `libmpv*.so`/MPV JNI libraries; `libffmpegJNI.so` and needed codec libraries present.
- Run release/R8 tests, check APK signer/certificate against existing published `Plezy.apk`, test both API 28 and 30, and verify the GPL source bundle.

### Gate F — Device regression and measured promotion

- Bedroom Fire TV Stick Lite first, Game Room Stick Lite second, Living Room 4K Plus third.
- For each, run controlled cold/warm UI, navigation, media loading, common Plex codecs, subtitles, audio passthrough, 4K HDR/DV where appropriate, downloads, Plex Home profiles, shuffle, and 10+ episode transitions.
- Record median and p95 times and PSS. If Exo-only codec or reliability regressions persist, keep the existing working release—not an unstable Exo-only candidate.
- Only then update the production workflow and existing `Plezy.apk` asset; signing continuity and HA update contract remain unchanged.

## Nonnegotiable safety rules

- Never disable player error handling or rewrite auth/profiles for a speed benchmark.
- Never remove MPV FFmpeg payload until independent Exo FFmpeg support is validated.
- Never use MPV as a silent fallback in the **final** build.
- Never claim playback functionality is preserved without corresponding device tests; known MPV-only functionality needs an explicit Exo replacement or an approved feature tradeoff.
- Never publish from an audit PR, force updates to any Fire Stick, overwrite `Plezy.apk`, or alter the 3 AM Home Assistant updater.
- Do not bypass licensing obligations; the released APK must carry/offer its exact GPL-3.0 corresponding source and build instructions.

## Compatibility matrix to capture

| Test | Fire OS 7 Lite | Fire OS 8 4K Plus |
|---|---|---|
| cold/warm startup and deep-link priority | pending | pending |
| H.264 / HEVC direct play | pending | pending |
| 1080p / 4K and HDR/Dolby Vision | pending | pending |
| EAC3, AC3, DTS, TrueHD / passthrough | pending | pending |
| FFmpeg audio decode and Plex transcode fallback | pending | pending |
| primary text, ASS/SSA, image subtitles | pending | pending |
| secondary subtitle feature parity | pending | pending |
| Plex music, gapless queue, background audio | pending | pending |
| seek, resume, refresh-rate change, error recovery | pending | pending |
| Home Assistant legacy and native shuffle links | pending | pending |
| 10+ consecutive shuffled episodes | pending | pending |
| APK signer and native library inventory | pending | pending |

The companion auditor in this PR deliberately returns `migration_ready=false` until every blocker is removed. Passing a source scan never substitutes for build or on-device tests.
