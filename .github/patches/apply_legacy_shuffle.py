#!/usr/bin/env python3
"""Preserve Home Assistant plezy://shuffle?server=...&show=... deep links.

Plezy 2.25+ provides native PlayLink mode=shuffle; this shim delegates to it.
Fail if upstream's parser changes so compatibility must be reviewed.
"""
from pathlib import Path

path = Path("lib/services/deep_links/deep_link.dart")
source = path.read_text(encoding="utf-8")
anchor = "      PlayLink.host => PlayLink._parse(params, profile),"
if source.count(anchor) != 1:
    raise SystemExit("Upstream deep-link parser changed; review compatibility shim before releasing")
# Only inspect the URI-HOST switch, not other switches in this file.
# Plezy 2.25 has a separate 'shuffle' => PlayMode.shuffle case; that
# is expected and is *not* support for plezy://shuffle URLs.
host_switch = "return switch (uri.host.toLowerCase()) {"
if source.count(host_switch) != 1:
    raise SystemExit("Upstream host parser changed; review the compatibility shim")
host_cases = source.split(host_switch, 1)[1].split("\n    };", 1)[0]
if "'shuffle' =>" in host_cases:
    raise SystemExit("Upstream already supports the legacy shuffle host; review the compatibility shim")

bridge = """      // Preserve older Home Assistant plezy://shuffle links without
      // duplicating upstream's playback or server reconnect logic.
      'shuffle' => _param(params, 'server') != null && _param(params, 'show') != null
          ? PlayLink._parse(
              {'server': params['server']!, 'id': params['show']!, 'mode': 'shuffle'},
              profile,
            )
          : null,
"""
path.write_text(source.replace(anchor, anchor + "\n" + bridge.rstrip()), encoding="utf-8")

test_path = Path("test/services/deep_links/legacy_shuffle_link_test.dart")
if test_path.exists():
    raise SystemExit(f"Upstream already has {test_path}; review before replacing it")
test_path.parent.mkdir(parents=True, exist_ok=True)
test_path.write_text("""import 'package:flutter_test/flutter_test.dart';
import 'package:plezy/media/ids.dart';
import 'package:plezy/services/deep_links/deep_link.dart';

void main() {
  test('legacy HA shuffle deep link uses native shuffle mode', () {
    final link = DeepLink.tryParse('plezy://shuffle?server=abc123&show=456');
    expect(link, isA<PlayLink>());
    final play = link! as PlayLink;
    expect(play.mode, PlayMode.shuffle);
    expect(play.target, isA<ItemPlayTarget>());
    final item = play.target as ItemPlayTarget;
    expect(item.serverId, ServerId('abc123'));
    expect(item.itemId, '456');
  });

  test('upstream native shuffle link still works', () {
    final link = DeepLink.tryParse('plezy://play?server=abc123&id=456&mode=shuffle');
    expect(link, isA<PlayLink>());
    expect((link! as PlayLink).mode, PlayMode.shuffle);
  });

  test('legacy shuffle requires a server and show', () {
    expect(DeepLink.tryParse('plezy://shuffle?server=abc123'), isNull);
    expect(DeepLink.tryParse('plezy://shuffle?show=456'), isNull);
    expect(DeepLink.tryParse('plezy://shuffle?server=abc123&show='), isNull);
  });
}
""", encoding="utf-8")
print("Preserved old Home Assistant shuffle links using native Plezy PlayLink")
