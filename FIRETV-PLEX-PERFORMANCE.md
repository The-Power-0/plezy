# Fire TV Plex-only performance program

## Scope

- Production target: Amazon Fire OS 7 and Fire OS 8, 32-bit ARM `armeabi-v7a`.
- Home Assistant manages discovery of new custom releases and Android APK updates.
- Plex is the only required media-server backend; **preserve Plex Home, profile PINs, Plex authentication, media server playback, native mpv and ExoPlayer fallback, audio passthrough, subtitles, and existing `plezy://` deep links**.
- The maintained `ha-shuffle-v2` branch remains the build coordinator; this candidate overlays the *exact* tagged upstream Plezy source before compiling.
- Future Windows builds retain normal upstream behavior unless explicitly built with optional flags.

## What this candidate actually changes

The standalone `Fire TV Plex-Only Optimized APK Test` workflow makes a fully AOT release APK with `--dart-define=PLEZY_FIRETV_PLEX_ONLY=true` and `--dart-define=PLEZY_HA_MANAGED_UPDATES=true`. Source overlay `.github/patches/apply_firetv_plex_only.py`:

1. Hides Jellyfin and Emby onboarding entries (Plex account sign-in remains).
2. Prevents existing Jellyfin/Emby connections from opening a native backend during profile binding. Does **not** delete user credentials, preferences, or old connections from the database.
3. Skips initialization of the Jellyfin API cache.
4. Skips Plezy's in-app update request at startup, since Home Assistant owns APK distribution.
5. Preserves the existing Home Assistant legacy shuffle compatibility patch and tests.
6. Keeps both flags false by default, so ordinary upstream/Windows variants retain functionality.
7. Runs build flag and deep-link tests, Flutter analyzer, APK AOT and ABI checks, and Android 9/11 certificate verification against the currently published APK.

This should remove irrelevant work and simplify sign-in. **It is not yet proven to speed up startup or playback.** Size reduction from debug → release was previously verified; any additional size/time benefit here must be measured.

## Automated source-line audit

`scripts/audit_firetv_source.py` scans **every readable line of tracked application source** under `lib/`, `android/`, `packages/`, and `windows/` in the exact upstream checkout. It inventories periodic timers, frame callbacks, rebuild notifications, expensive visual-effects markers, network/JSON operations, and remaining Jellyfin/Emby references. It reports top-ranked source files and example lines in `Plezy-FireTV-PlexOnly-SourceAudit.txt`, bundled in the Actions artifact. Generated Dart is counted but excluded from hotspot rankings.

**Limitations:** Pattern searches do not establish real runtime cost, and counting lines is not a semantic code review. We will only change additional hot paths after measured Fire TV timings support them.

## Why not delete all Jellyfin source folders?

Plezy shares profile, server, UI, playback, database, and library interfaces between Plex and Jellyfin. Physically deleting Jellyfin implementations without untangling cross-references can break compilation, onboarding, persisted settings, and Plex queues. Flutter's AOT tree shaker can drop unreferenced code when build flags are compile-time constants. Any later deeper backend removal should follow a dependency-graph and test-driven migration, not a blanket directory deletion.

## Baseline and measurements

Compare **three builds**:
- Published 2.25.0 HA-shuffle DEBUG APK (roughly 172.9 MB).
- Previously verified 2.25.0 HA-shuffle release candidate (roughly 98.0 MB; signed).
- New Plex-only AOT candidate (size not yet measured).

On each device, compare warm launches, cold launches (`adb shell am force-stop com.edde746.plezy`), first usable focus, first Plex poster, first playback frame, D-pad row navigation, scrolling smoothness, shuffle launch and 10+ consecutive episode transitions. Use consistent network, same Plex profile/library, video files, and power state. Capture `adb shell dumpsys meminfo com.edde746.plezy`, logcat startup logs, and Plezy's in-player FPS/drop-frame diagnostics. Measure multiple repetitions (e.g., 5) and use medians. **Don't conflate APK size reduction with CPU, memory, or latency improvements.**

## Further work ranked by likely return

| Priority | Candidate | Exact area | Risk/verification |
|---|---|---|---|
| P0 | AOT release builds | Existing `firetv-performance-candidate.yml` | Already built, verify on-device |
| P1 | Plex-only backend gating | `main.dart`, `active_profile_binder.dart`, authentication and connections UI | Check signed-in and fresh-device startup, Plex Home switching |
| P1 | HA-managed update bypass | `main_screen.dart` | Ensure HA updater still works; check launch-to-play |
| P2 | Prioritize visible artwork over old queued requests | `image_cache_service.dart`, `optimized_media_image.dart`, `tv_browse_rail.dart` | Measure visible-poster latency and cancel safety |
| P2 | Profile and server bind timings | `active_profile_binder.dart`, `multi_server_manager.dart`, `plex_auth_service.dart` | Preserve PIN/access control and offline recovery |
| P2 | Defer only unneeded background work until after first playback | `main.dart` / startup services | Respect tracker scrobbling, watch-state and download recovery |
| P3 | Memory-tier tuning for 1 GB vs 2 GB | `device_performance.dart` | OOM risk, GPU pressure and poster sharpness |
| P3 | Optimize native playback startup based on traces | `android/**/exoplayer`, `android/**/mpv` | Retain codec/Dolby/AC3/DTS/subtitle interoperability |
| P3 | Reduce bundled APK assets/libraries | Gradle, pubspec asset list | Determine real on-device resource use first |

## Rollback and publication policy

This workflow is **manual**, test-only, and read-only to GitHub Releases. Its artifact name differs from the previous baseline; it contains an APK, checksum, corresponding GPL-3.0 source archive, and build report. It leaves `Plezy.apk` (latest release), the production hourly workflow, and Home Assistant updates unchanged. First validate on one Fire TV Stick Lite. If Plex Home profiles, shuffle, streaming, captions, and resume work, then compare on Fire OS 8. Promote to production only after those checks.

Every optimization overlay is an unofficial GPL-3.0 modification of Plezy; preserve original attribution/license and corresponding source with all distributed APKs.
