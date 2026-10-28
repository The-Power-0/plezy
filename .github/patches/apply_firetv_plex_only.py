#!/usr/bin/env python3
"""Conservative source overlay for the manual Fire TV Plex-only AOT candidate.

Applied only AFTER checking out a verified upstream Plezy release; never edits
production or Windows source in the maintained automation branch. Exact
anchors fail closed when upstream changes.
"""
from pathlib import Path

def edit(path: str, original: str, replacement: str) -> None:
    file = Path(path)
    source = file.read_text(encoding="utf-8")
    occurrences = source.count(original)
    if occurrences != 1:
        raise SystemExit(f"{path}: expected one source anchor; found {occurrences}: {original[:100]!r}")
    file.write_text(source.replace(original, replacement), encoding="utf-8")
    print(f"Fire TV overlay: modified {path}")

flags = Path("lib/services/firetv_build_flags.dart")
if flags.exists():
    raise SystemExit("Upstream has firetv_build_flags.dart; review rather than overwrite")
flags.write_text(
    """/// Compile-time flags for the optional, unofficial Home Assistant Fire TV APK.
///
/// Defaults remain OFF to preserve all upstream functionality in any future
/// Windows, Android, or other platform build.
const bool kFireTvPlexOnly =
    bool.fromEnvironment('PLEZY_FIRETV_PLEX_ONLY', defaultValue: false);

/// Home Assistant already owns installation and version checks on these sticks.
const bool kHomeAssistantManagedUpdates =
    bool.fromEnvironment('PLEZY_HA_MANAGED_UPDATES', defaultValue: false);
""",
    encoding="utf-8",
)

edit(
    "lib/main.dart",
    "import 'services/jellyfin_api_cache.dart';",
    "import 'services/jellyfin_api_cache.dart';\nimport 'services/firetv_build_flags.dart';",
)
edit(
    "lib/main.dart",
    "    JellyfinApiCache.initialize(_appDatabase);",
    "    // This device never uses Jellyfin/Emby. Avoid initializing its database cache.\n"
    "    if (!kFireTvPlexOnly) JellyfinApiCache.initialize(_appDatabase);",
)

edit(
    "lib/screens/main_screen.dart",
    "import '../services/settings_service.dart';",
    "import '../services/settings_service.dart';\nimport '../services/firetv_build_flags.dart';",
)
edit(
    "lib/screens/main_screen.dart",
    "      // Check for updates on startup\n      unawaited(_checkForUpdatesOnStartup());",
    "      // In HA-managed Fire TV builds the external updater owns version checks.\n"
    "      if (!kHomeAssistantManagedUpdates) unawaited(_checkForUpdatesOnStartup());",
)

edit(
    "lib/screens/settings/add_connection_screen.dart",
    "import 'add_jellyfin_screen.dart';",
    "import 'add_jellyfin_screen.dart';\nimport '../../services/firetv_build_flags.dart';",
)
edit(
    "lib/screens/settings/add_connection_screen.dart",
    "      _BackendOption(\n        backend: MediaBackend.jellyfin,",
    "      if (!kFireTvPlexOnly) _BackendOption(\n        backend: MediaBackend.jellyfin,",
)
edit(
    "lib/screens/settings/add_connection_screen.dart",
    "      _BackendOption(\n        backend: MediaBackend.emby,",
    "      if (!kFireTvPlexOnly) _BackendOption(\n        backend: MediaBackend.emby,",
)

edit(
    "lib/screens/auth_screen.dart",
    "import 'settings/add_jellyfin_screen.dart';",
    "import 'settings/add_jellyfin_screen.dart';\nimport '../services/firetv_build_flags.dart';",
)
auth_file = Path("lib/screens/auth_screen.dart")
auth = auth_file.read_text(encoding="utf-8")
start_anchor = (
    "        const SizedBox(height: 24),\n"
    "        Row(\n"
    "          children: [\n"
    "            Expanded(child: Divider(color: Theme.of(context).colorScheme.outlineVariant)),"
)
end_anchor = "        if (kDebugMode) ...["
if auth.count(start_anchor) != 1 or auth.count(end_anchor) != 1:
    raise SystemExit("Auth buttons layout changed upstream; review before applying")
start = auth.index(start_anchor)
end = auth.index(end_anchor, start)
auth = (
    auth[:start] + "        if (!kFireTvPlexOnly) ...[\n"
    + auth[start:end]
    + "        ],\n"
    + auth[end:]
)
auth_file.write_text(auth, encoding="utf-8")
print("Fire TV overlay: hid Jellyfin/Emby sign-in buttons")

edit(
    "lib/profiles/active_profile_binder.dart",
    "import 'profile_connection.dart';",
    "import 'profile_connection.dart';\nimport '../services/firetv_build_flags.dart';",
)
edit(
    "lib/profiles/active_profile_binder.dart",
    "      final localProfileHasJoinRows = profile.isLocal && joinRows.isNotEmpty;",
    "      final localProfileHasJoinRows = profile.isLocal && joinRows.any(\n"
    "        (pc) => !kFireTvPlexOnly || connectionsById[pc.connectionId] is PlexAccountConnection,\n"
    "      );",
)
edit(
    "lib/profiles/active_profile_binder.dart",
    "        case JellyfinConnection(:final serverMachineId):\n"
    "          expected.add(serverMachineId);",
    "        case JellyfinConnection(:final serverMachineId):\n"
    "          // Never attempt to bind old non-Plex connections on this appliance.\n"
    "          if (!kFireTvPlexOnly) expected.add(serverMachineId);",
)
edit(
    "lib/profiles/active_profile_binder.dart",
    "        case JellyfinConnection():\n"
    "          expected.add(conn.serverMachineId);\n"
    "          futures.add(_bindMediaBrowser(conn, profileId: profile.id, generation: generation));",
    "        case JellyfinConnection():\n"
    "          if (!kFireTvPlexOnly) {\n"
    "            expected.add(conn.serverMachineId);\n"
    "            futures.add(_bindMediaBrowser(conn, profileId: profile.id, generation: generation));\n"
    "          }",
)
edit(
    "lib/profiles/active_profile_binder.dart",
    "          if (connectionsById[pc.connectionId] case JellyfinConnection(:final id)) id,",
    "          if (!kFireTvPlexOnly && connectionsById[pc.connectionId] case JellyfinConnection(:final id)) id,",
)

test = Path("test/services/firetv_build_flags_test.dart")
if test.exists():
    raise SystemExit("Upstream has build flag test; review first")
test.parent.mkdir(parents=True, exist_ok=True)
test.write_text(
    """import 'package:flutter_test/flutter_test.dart';
import 'package:plezy/services/firetv_build_flags.dart';

void main() {
  test('the Fire TV Plex-only build flags are enabled for candidate', () {
    expect(kFireTvPlexOnly, isTrue);
    expect(kHomeAssistantManagedUpdates, isTrue);
  });
}
""",
    encoding="utf-8",
)
print("Prepared Plex-only source overlay and compile-time mode regression test")
