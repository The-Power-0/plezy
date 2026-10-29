# Optimization Stage 03 — Watch Together removal

Status: runtime-removal source overlay and fail-closed source audit committed; **no build or device testing**.

## User-specific scope

Dedicated Plezy Fire TV Plex movies/TV ExoPlayer-only build. Preserve HA shuffle/deep links, Plex Home and Continue Watching, normal next-episode queue, native D-pad and Android media controls, seek/play/pause, subtitles and stored profile settings. Standard Plezy and possible future Windows builds are not patched.

## Source overlay

`apply_firetv_remove_watch_together.py` runs after the Plex-only, no-MPV, no-music, no-external-services and no-Discord overlays. It adds `PLEZY_FIRETV_NO_WATCH_TOGETHER=true`, default **false** in ordinary builds.

- No WatchTogetherProvider constructed in the profile scope.
- WatchNoticeListener returns before looking up or subscribing to a nonexistent provider.
- No Watch Together callback established from MainScreen.
- Local Plex Home toolbar removes room action, participant badge and routing; retains Refresh and existing Companion Remote until its separate removal phase.
- Video screen never registers a player adapter with a room; room-owned playback start and rate handling cannot take effect.
- ExoPlayer UI skips room authority selection during layout; omits room overlays, header pill, settings-menu item and rate ownership checks.
- Watch Together relay URL setting is hidden; its persisted value remains inert.
- Direct room creation/joining is refused in the provider before the SDK transport starts.
- Room deep-link navigation is rejected without entering the regular Plex player route. HA agent playback doesn't look up absent room provider.
- Positive/negative Flutter flag tests and a source guard verify these entry points.

## Important limitation

This source overlay makes Watch Together **unavailable at runtime**, but `openwatchparty` remains a declared Dart dependency and its interfaces/source remain in the repository: shared player/navigator types, existing widget tests and source still reference them. Removing the package immediately without a full call-site rewrite would break compilation.

A later dependency-pruning workstream must remove all remaining room-specific types, imports and tests, delete the `openwatchparty` dependency and validate AOT size. This phase does not claim a finished package/binary deletion. No network behavior or performance improvement has been measured.

## Validation before release

1. Apply all overlays to **exact upstream 2.25.0** in a disposable checkout and run the no-room source check; fail closed if anchors drift.
2. Run Flutter compile, native Android compile, relevant unit/widget tests, AOT release and scan packaged native/Dart dependencies.
3. Verify normal Plex Home content, HA deep links, playback and 10+ shuffled TV episode transitions, Back/select/seek, Fire TV 7/8.
4. Confirm no room connection attempt or relay traffic at runtime, and that Watch Together settings/buttons cannot appear.
5. Only after all 16 optimization workstreams are approved and validated should production GitHub releases or HA update feeds change.

No production branch, signed APK, or Home Assistant updater has been modified.
