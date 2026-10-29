# Plex movies + TV: ExoPlayer-only Fire TV edition

Status: source changes prepared. **Not yet built, signed, installed or tested.** This candidate must not replace the existing published APK or Home Assistant nightly updater until its checks and physical-device playback tests pass.

## Scope

- Fire OS 7 and Fire OS 8, 32-bit `armeabi-v7a`.
- Plex media server only; movies and television only. **No Plex music support.**
- ExoPlayer / Android Media3 is the only video playback engine.
- No native libmpv engine, MPV JNI, MPV video fallback, or MPV audio plugin is included in the desired output APK.
- Retain native Android MediaCodec, subtitles (libass), FFmpeg audio decoding for TV/movie tracks, Dolby Vision support, audio passthrough where supported, live TV, video downloads, HDR and Plex profile / Home Assistant deep-link compatibility.

## Source changes

The non-publishing candidate workflow `firetv-no-mpv-candidate.yml` applies, in order:

1. Existing Home Assistant shuffle compatibility patch for the pinned upstream release.
2. `apply_firetv_plex_only.py` (disables non-Plex browsing and updates).
3. `apply_firetv_exoplayer_video.py` (video creation and configuration forced to Media3).
4. `apply_firetv_mpv_retirement.py` (the native MPV player sources and registrations are removed, `ExoPlayerPlugin.kt` is replaced, music audio-only playback is disabled, MPV fallback event handling and extra properties are removed).

The replacement native bridge is maintained in `.github/patches/firetv_exoplayer_only/ExoPlayerPlugin.kt`, and copied into the exact upstream source checkout before compilation. The exact modified GPL source is archived with the test APK. All changes are isolated from the normal upstream and future Windows builds.

## FFmpeg is retained, MPV isn't

ExoPlayer's FFmpeg audio extension needs `libffmpegJNI.so`, `libavcodec.so`, `libavutil.so` and `libswresample.so`. In upstream 2.25.0, those FFmpeg libraries are supplied by the checksum-pinned `mpv-android` AAR. The candidate retains the separate build-time extraction configuration **but removes `implementation(mpvAarDependency)`**, which otherwise adds the entire MPV runtime to the app.

This means the build process still downloads a verified AAR containing MPV in order to **extract only FFmpeg components**. This is a transitional build provenance dependency, **not a runtime MPV player**. Replacing the AAR with a completely independent pinned FFmpeg artifact can happen later and does not require restoring MPV playback.

A final APK check must reject native library members whose names reference MPV, and require the FFmpeg decoder. Native libraries must actually be inspected after compilation; source changes alone cannot prove their absence.

## Unsupported media without a fallback player

Native `ExoPlayerCore` retains its in-place decoder recovery and Dolby Vision fallback behavior. If those fail, its existing `onFormatUnsupported` callback returns `false`, causing the core to emit an error to the Dart player layer. The new bridge does **not** silently switch to MPV or hide the error. Plex server-side transcoding remains available through the existing Plex quality/source selection paths; automatic transcoding for every unsupported local source is **not yet guaranteed** by these changes.

The native method channel still accepts a method named `setMpvProperty` as a compatibility shim for ExoPlayer-specific audio and subtitle offsets; it does not construct or call MPV and should be renamed only after a coordinated Dart/native protocol change.

## Required checks before release

- Apply all source overlays against **exact** upstream Plezy 2.25.0. If any anchor fails, stop instead of silently releasing an incompatible APK.
- Compile Flutter release AOT for ARMv7 and Android native Media3, including optimized R8/proguard output.
- Run all existing Home Assistant shuffle tests and Plex profile/deep-link tests.
- Check binary ZIP + DEX for embedded MPV runtime / player classes, verify FFmpeg decoder and retained libass/libdovi libraries as appropriate.
- Verify certificate matches the published Plezy APK, for both Android API 28 and 30.
- Ensure no Plex tokens, signing keys, or credentials were included in source/artifacts.
- On Bedroom Stick Lite, Game Room Stick Lite and Living Room 4K Plus: cold/warm launches; Plex movie + TV playback; seeking and subtitle selection; AC3/EAC3/DTS/TrueHD where available; HEVC/H.264; 4K HDR/Dolby Vision where supported; Home Assistant shuffle and 10+ transitions; Live TV and offline movie/TV files if used; recovery from network failures.
- Document unsupported formats and demonstrate appropriate error UI / Plex transcoding manually before treating ExoPlayer-only as functionality-preserving.

The existing production release workflow and `Plezy.apk` remain unchanged. Use the manual candidate artifact only, and do not install it until a successful build has passed static and signature checks.
