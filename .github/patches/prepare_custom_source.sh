#!/usr/bin/env bash
set -euo pipefail
UPSTREAM_TAG="$1"
if [[ "$UPSTREAM_TAG" == 2.24.0 || "$UPSTREAM_TAG" == v2.24.0 ]]; then
  git am "$RUNNER_TEMP/ha-shuffle.patch"
  echo "implementation=legacy" >> "$GITHUB_OUTPUT"
else
  python3 "$RUNNER_TEMP/apply_legacy_shuffle.py"
  git add lib/services/deep_links/deep_link.dart test/services/deep_links/legacy_shuffle_link_test.dart
  git commit -m "feat: keep HA legacy shuffle URLs via native Plezy playback"
  echo "implementation=native" >> "$GITHUB_OUTPUT"
fi
cp "$RUNNER_TEMP/HA-SHUFFLE-NOTICE.md" HA-SHUFFLE-NOTICE.md
cat > BUILDING-CUSTOM-FIRE-TV.md <<'DOC'
# Rebuilding the unofficial Plezy Fire TV APK

Modified corresponding source for this release; see LICENSE and
HA-SHUFFLE-NOTICE.md. Original project: https://github.com/edde746/plezy.

Use Java 21, Flutter 3.47.0, an Android SDK with build tools, and
dependencies in pubspec.lock. From this source tree:

    flutter pub get
    flutter build apk --debug --split-per-abi

The Fire TV armeabi-v7a APK is:
build/app/outputs/flutter-apk/app-armeabi-v7a-debug.apk

For Plezy 2.25+ compatibility:
    flutter test test/services/deep_links/legacy_shuffle_link_test.dart

The release's private signing key is not provided; self-built APKs
may use your own signing key but cannot replace the existing signed
APK in place without matching signatures.
DOC
git add HA-SHUFFLE-NOTICE.md BUILDING-CUSTOM-FIRE-TV.md
git commit -m "docs: carry GPL attribution and build instructions with source"
test -s LICENSE
grep -q 'GNU GENERAL PUBLIC LICENSE' LICENSE
grep -q 'Version 3' LICENSE
echo "commit=$(git rev-parse HEAD)" >> "$GITHUB_OUTPUT"
