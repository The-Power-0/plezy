# Pre-PowerPlay archive

PowerPlay 1.0.0 and later releases are the maintained application history. PowerPlay 1.1.1 remains Latest.

## Legacy releases

| Tag | Archive disposition | Asset handling |
| --- | --- | --- |
| `2.25.0-ha-shuffle.1` | Public prerelease, labelled Archived / rollback only | Original APK, source and checksums retained at the same URLs; Home Assistant's pinned Plezy fallback keeps working |
| `2.24.0-ha-shuffle.1` | Unpublished archived draft | APK and checksum retained; owner can republish if needed |
| `2.23.0-ha-shuffle.1` | Unpublished archived draft | APK and checksum retained; owner can republish if needed |
| `2.22.0-ha-shuffle.1` | Unpublished archived draft | APK and checksum retained; owner can republish if needed |

GitHub has no separate release-archive state. Drafts hide obsolete releases from the public listing while retaining their assets. The one public rollback release is labelled Archived and marked prerelease; it cannot replace a stable PowerPlay release as Latest. No release assets, tags, commits, or branches are deleted by this cleanup.

The [manifest](pre-powerplay-manifest.json) preserves original release titles, notes, flags, asset IDs/URLs and sizes, plus the original open PR descriptions and source commit IDs. To restore an archived release, the repository owner can edit its draft, restore the original metadata from the manifest, and publish it. To restore a historical proposal, reopen its PR; the original branch and commit remain.

## Historical pull requests

PRs **#8–#24** were the stacked Plezy/Fire TV optimization overlays, validation, and candidate-build work. They are closed as superseded rather than merged into the legacy application tree. Their build output was preserved in the tested frozen source used for PowerPlay 1.0.0 and subsequent PowerPlay releases. PRs #25, #26 and #27 introduced the PowerPlay release machinery, settings/branding batch and device-aware library defaults.

The exact corresponding source for released APKs is the `PowerPlay-…-Source.tar.gz` attachment on each release, together with its native-source inputs. The repository-root legacy source and automatic GitHub source archives remain distinct from that complete application source. Current candidate builds continue to use the checksum-pinned PowerPlay 1.0.0 baseline and reviewed overlays.

## Branch cleanup and main migration

The [branch manifest](branch-manifest.json) records all 29 branch names and original tips before cleanup. Original tips are preserved as lightweight `archive/branches/<name>/<short-sha>` tags before obsolete branch names are removed. Restore a branch by creating it at the recorded tag or full commit SHA.

The existing `main` was an ancestor of `ha-shuffle-v2`, 80 commits behind at inventory time. It can be fast-forwarded to the maintained PowerPlay history. `ha-shuffle-v2` is retained while it is the repository default, and is removed only after an administrator selects `main` and the cleanup verifies that main contains its final commit. No release tags or APK/source assets are removed. PowerPlay candidate builds remain on release branches; legacy repository-root CI is manual so activating main does not reactivate upstream-only checks.
