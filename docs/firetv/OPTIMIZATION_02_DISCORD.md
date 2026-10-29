# Optimization stage 02 — Remove Discord Rich Presence

**Status:** source-only overlay committed, not applied to a full Flutter/Android build.

## Scope

This is the Fire TV Plex movies-and-TV edition only, stacked after the existing no-MPV and external services PRs. Ordinary upstream Plezy and a possible future Windows build retain Discord Rich Presence unless a different source variant explicitly opts out.

## Removed from candidate source

- The `dart_discord_presence` package is removed from `pubspec.yaml`; its lockfile resolution will be updated by `flutter pub get` when the candidate build is eventually permitted.
- `lib/services/discord_rpc_service.dart` and its Discord-specific test/fake are deleted from the patched checkout.
- Desktop startup no longer initializes the Discord IPC client.
- Video playback stops sending Discord start, stop, resume, pause, position, and rate events. The extra rate stream subscription exists solely for Discord and is deleted.
- The unused music playback service also loses Discord calls without disturbing its other service logic.
- Discord integration controls and mutation side effects are deleted from the Services settings screen.
- The agent control setting `enable_discord_rpc` responds as unsupported instead of trying to connect, even if invoked directly.
- The mixed music service test keeps all non-Discord tests and drops only its Discord-specific group.
- Fixed-endpoint TLS test stops scanning the deleted service source.

## Intentionally retained

- The old `SettingsService.enableDiscordRPC` preference key stays inert. Removing a stored pref key or deleting credentials is not necessary for APK speed and could complicate future migration.
- Local Plex Continue Watching, play/resume progress tracking, server-scoped watched state, Home Assistant shuffle URI, native media controls, Plex Home users, and all video audio/subtitle processing remain untouched.
- Existing test cases for local Plex/media controls remain present. Only tests depending on the deleted Discord implementation are removed.

## Verification plan

The stage 02 source audit fails if runtime sources still reference `DiscordRPCService` or `dart_discord_presence`, if the old dependency is in pubspec, if the startup initializer or Discord-only rate listener remains, or if the media progress tracker has been removed.

The audit does **not** validate whether Flutter compiles or whether the final APK contains a transitive desktop library. After all source workstreams have been approved, verify resolved dependencies via `flutter pub deps` and the compiled release APK, then benchmark cold startup, playback event frequency, memory, and frame pacing. No performance improvement is claimed yet.

**No production release publication, no HA updater changes, no build dispatch.**
