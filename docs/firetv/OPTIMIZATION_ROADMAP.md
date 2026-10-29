# Plezy Fire TV: 16-workstream optimization and feature removal plan

**Scope:** custom signed `armeabi-v7a` APK for Fire OS 7 and 8. Plex movies and television only; Home Assistant deep-link shuffle, ordinary local Plex connections, Plex Home users, watched/resume state, downloads, subtitles, hardware decoding, HDR, movie/TV audio decoding/passthrough, error recovery, and current release/HA-updater contract MUST remain.

**Process:** Keep each feature removal or optimization in a separate stacked PR. Apply source overlays in order against the exact pinned upstream checkout and archive exact GPL source. No candidate build, publication, or Fire Stick update until the requested source work has been reviewed. Compilation, signing/ABI checks and physical-device regressions still precede any production promotion.

## Features excluded from the appliance

| Component | Target | Guardrails | Progress |
|---|---|---|---|
| Jellyfin/Emby | Eliminate backend auth/requests/dispatch | Keep Plex multi-server and Plex Home | Foundation in PR #8 |
| MPV runtime | Media3/ExoPlayer-only movies and TV | Keep FFmpeg, libass and movie/TV audio | Source overlay in PR #8; uncompiled |
| Music | No music libraries, playback controls, or audio-only MPV | Keep movie/TV audio track support | Source overlay in PR #8 |
| Plex cloud Discover/Explore | Disable online catalog and watchlist | Keep **local Plex Home**, Continue Watching and server hubs | Removal step 01 |
| Seerr/Overseerr/Jellyseerr requests | No request sheet, permissions refresh, session or API calls | Do not interfere with server-side Sonarr/Radarr | Removal step 01 |
| Trakt/MAL/AniList/Simkl | No session restore, watched sync, ratings or scrobbling | Preserve Plex watched state | Removal step 01 |
| MDBList | Also disable external scores and catalog watchlists | Preserve metadata returned by Plex | Removal step 01 |
| Discord Rich Presence | Remove desktop RPC integration | Preserve diagnostics and Android app lifecycle | Source overlay + audit in step 02 (not compiled) |
| Watch Together | Block room providers, relay and UI; later prune SDK/types | Preserve ordinary playback and episode advance | Source overlay + audit in step 03, not compiled |
| Plezy Remote | Disable host/peer, pairing, LAN discovery and UI | Keep Fire TV D-pad, Android remote keys, and HA deep links | Stage 04 source overlay and audit drafted, no build |

**Naming trap — "Discover":** `DiscoverScreen`/`DiscoverProvider` is the *local Plex Home* (Continue Watching and server media hubs). `discover.provider.plex.tv` is the cloud catalog/watchlist surfaced through Explore. Only the latter is removed; Home remains.

## Step 01 — External services runtime exclusion

Opt-in `PLEZY_FIRETV_NO_EXTERNAL_SERVICES=true`:
- bypasses session hydration for Trakt, MAL, AniList, Simkl, MDBList and Seerr;
- does not initialize Plex cloud Discover credentials;
- hides all external catalog sources and their Explore tab;
- makes `TrackerCoordinator`'s outbound tracker list empty;
- skips Seerr permission polling on resume;
- hides the now-unused Services settings hub;
- keeps default builds unaffected and does not erase saved credentials.

This is runtime exclusion and entry-point deactivation, **not proof that unused source has been deleted or removed from the compiled binary**. Reachable-source pruning will follow full dependency analysis.

## Step 02 — Discord Rich Presence removal

The isolated source overlay deletes Discord's Dart package and service, removes startup and video/music callback traffic (including a rate-listener subscription), removes its settings and direct-control routes, and retains all normal Plex progress tracking. A source audit rejects active Discord runtime references. No APK build or device benchmark has run. See `OPTIMIZATION_02_DISCORD.md`.

## Step 03 — Watch Together isolation

The optional build flag blocks room providers, transport, session navigation and playback takeover, hides Home/player room controls, and avoids watch-room layout selectors. The SDK and source types **remain for the later dependency-pruning step**, so this is not yet an APK size win. See `OPTIMIZATION_03_WATCH_TOGETHER.md`. No build was executed.

## Sixteen performance workstreams

| # | Area | Target | Key regression risk |
|---|---|---|---|
| 1 | Plex-only specialization | Remove unused backend, catalog and auth work | Plex profile and multi-server compatibility |
| 2 | Cold-start path | Defer noncritical work, prioritize HA shuffle deep link | Credential/database races |
| 3 | Library indexing | Replace repeated linear item-ID scans | Sort, alpha-jump, evictions and live updates |
| 4 | D-pad focus | Reduce focus-processing overhead | No key loss, Back and Select preserved |
| 5 | Artwork priority | Focus-first prefetch and stale-request cancellation | No missing artwork or starvation |
| 6 | Flutter rebuilds | Cut unnecessary listeners and derived allocations | Stable p95/p99 UI frames |
| 7 | Plex request consolidation | Deduplicate metadata/hub/watch-state requests | Retry, cache freshness and failover |
| 8 | Background scheduling | Protect playback startup from noncritical tasks | Offline sync and downloads intact |
| 9 | Media3 command pipeline | Reduce native method/event traffic | Ordered seek, volume, pause semantics |
| 10 | Playback initialization | Reduce preparation and episode transitions | Codec and queue behavior intact |
| 11 | Device memory/cache | Adaptive Lite vs 4K Plus memory policies | No OOM/background kills |
| 12 | APK/asset trimming | Remove unreachable assets and libraries | Keep fonts, FFmpeg, subtitle codecs |
| 13 | Release/Gradle | AOT/R8/ABI and reproducible source | Signature and HA release contract |
| 14 | DB/allocation | Optimize hot allocations, indexed Drift lookups | No data loss or migration errors |
| 15 | Codec/audio/buffer | Measured Media3 load-control and formats | AC3/EAC3/DTS/TrueHD/HDR/DV |
| 16 | Android components | Remove unused providers/receivers/permissions | Keep Fire TV launcher and HA deep links |

**Workstream 09 adapts the earlier MPV queue proposal to Media3**, since the custom target has no MPV runtime.

## Verification gates after code phases

- Source scan is not proof of compilation or codec behavior.
- APK must contain no MPV classes/runtime and must preserve required FFmpeg and libass components.
- Signed release AOT for `armeabi-v7a`; API 28/30 checks; exact signer match; exact GPL corresponding source included.
- Compare cold/warm startup, HA shuffle-to-first-frame, p95/p99 UI frame timing, PSS, GC, focused art, search, and shuffled transitions.
- Independently exercise both Lite Sticks and the 4K Plus. Test audio, video, subtitle, HDR/DV, offline, profile switching, errors, and at least 10 consecutive shuffled episodes.
- Do not publish, change the production workflow or automatically deploy a candidate before validation.
