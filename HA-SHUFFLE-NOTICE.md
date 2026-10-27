# Unofficial Plezy fork — Home Assistant / Fire TV shuffle

This repository builds an independently maintained modification of [Plezy](https://github.com/edde746/plezy), authored and maintained by the upstream Plezy contributors. This fork is not an official Plezy release and is not endorsed by its maintainers.

**License:** Plezy and this derivative are distributed under the **GNU General Public License, version 3 (GPL-3.0)**. The original [LICENSE](LICENSE), source copyright statements, and applicable third-party notices are retained. Modifications are also GPL-3.0 licensed. No warranty is offered to the extent allowed by the GPL.

**Modifications (October 2026):** The custom build preserves `plezy://shuffle?server=<serverId>&show=<showRatingKey>` for Home Assistant and ADB automation. The original implementation added Android intent handling, a Dart shuffle launcher, and tests. Beginning with upstream Plezy **2.25.0**, the upstream project implements native `plezy://play?server=<serverId>&id=<showId>&mode=shuffle` links; the fork now uses a small compatibility adapter that translates the legacy URL to native Plezy shuffle playback.

**Source and rebuilding:** For a newly published custom APK, download the **`Plezy-Source.tar.gz` attachment on that exact GitHub release**, which contains the source snapshot used to build it, this license notice, upstream build scripts and pinned dependency manifests, compatibility code, and `BUILDING-CUSTOM-FIRE-TV.md`. The auto-generated GitHub source ZIP/TAR attached to a release points to the *automation branch*, not necessarily the APK build source, and must **not** be substituted for the `Plezy-Source.tar.gz` attachment.

**Signing:** The workflow signs the APK with a repository secret containing the previously established signing key. The signing key is not included in source releases. Anyone can build with their own signing key, but Android will not replace an installed APK signed by a different key without uninstalling it.

For upstream issues, please contact the upstream project only when the issue reproduces on unmodified Plezy. For Home Assistant fork changes, use this repository's issue tracker.
