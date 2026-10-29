# Fire TV Plezy: stacked draft PR review and merge guide

**All PRs below are draft/source-only. No APK build or device verification has been run. Do not publish a new Plezy.apk or alter Home Assistant's update source during review.**

| Order | PR | Branch purpose |
|---|---|---|
| 1 | #8 | ExoPlayer-only movie/TV native MPV retirement |
| 2 | #9 | External catalogs, Seerr, Trakt/MAL/AniList/Simkl/MDBList runtime exclusion |
| 3 | #10 | Discord Rich Presence source removal |
| 4 | #11 | Watch Together runtime exclusion |
| 5 | #12 | Plezy Remote host/discovery/pairing runtime exclusion |
| 6 | #13 | Plex library sliver ID index snapshot |
| 7 | #14 | HA cold-start priority and skipped obsolete warmups |
| 8 | #15 | O(1) D-pad action-bar focus binding lookup |
| 9 | #16 | Disable persisted music playback restoration |

Each PR is based on the *previous PR's feature branch*, rather than directly on `ha-shuffle-v2`. This keeps each PR's own diff reviewable. **Do not simply click Merge on all of these stacked PRs**: that would merge changes into intermediate branches, not necessarily into production. After approving a PR, merge it into `ha-shuffle-v2` by retargeting that PR's base to `ha-shuffle-v2`, verifying its diff and checks, and merging it. Repeat in order, or prepare an approved aggregate integration PR once the full stack is reviewed.

**The source must be compiled, checked and tested before production promotion.** Until then, keep experimental changes unmerged. Stacked source overlays intentionally apply against upstream Plezy 2.25.0 at candidate build time. Python source checks and exact string anchor verification are not evidence of Flutter/Kotlin compilation or hardware compatibility.

Remaining optimization work: priority artwork fetch/cancellation, widget rebuilds, Plex request deduplication, background scheduling, Media3 command pipeline and preparation, memory/cache tiers, assets/dependency pruning, release AOT/Gradle, allocation/database profiling, codec/buffer tuning, Android component cleanup. Some of these require first measuring a working candidate to avoid negative regressions. Watch Together's OpenWatchParty dependency and Plezy Remote source types are still present but disabled in the specialized runtime; full deletion awaits reachability/compilation proof.

Preserve the existing Fire OS 7/8 package identity, signing certificate, exact GPL corresponding source archive, `plezy://shuffle?server=...&show=...`, Plex auth, subtitle and movie/TV audio support, player Back/D-pad controls and Home Assistant nightly updater behavior.
