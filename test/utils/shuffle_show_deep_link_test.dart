import 'package:flutter_test/flutter_test.dart';
import 'package:plezy/utils/shuffle_show_deep_link.dart';

void main() {
  group('ShuffleShowDeepLink.tryParse', () {
    test('parses server and show rating key', () {
      final link = ShuffleShowDeepLink.tryParse(
        'plezy://shuffle?server=abc123&show=456',
      );

      expect(link, isNotNull);
      expect(link!.serverId, 'abc123');
      expect(link.showRatingKey, '456');
    });

    test('decodes URI query parameters', () {
      final link = ShuffleShowDeepLink.tryParse(
        'plezy://shuffle?server=server%20id&show=show%2Fkey',
      );

      expect(link, isNotNull);
      expect(link!.serverId, 'server id');
      expect(link.showRatingKey, 'show/key');
    });

    test('rejects missing or empty parameters', () {
      expect(ShuffleShowDeepLink.tryParse('plezy://shuffle'), isNull);
      expect(
        ShuffleShowDeepLink.tryParse('plezy://shuffle?server=abc'),
        isNull,
      );
      expect(ShuffleShowDeepLink.tryParse('plezy://shuffle?show=123'), isNull);
      expect(
        ShuffleShowDeepLink.tryParse('plezy://shuffle?server=&show=123'),
        isNull,
      );
      expect(
        ShuffleShowDeepLink.tryParse('plezy://shuffle?server=abc&show='),
        isNull,
      );
    });

    test('rejects other deep-link types', () {
      expect(
        ShuffleShowDeepLink.tryParse('plezy://play?content_id=plezy_abc_123'),
        isNull,
      );
      expect(ShuffleShowDeepLink.tryParse('plezy://live?channel=4'), isNull);
      expect(ShuffleShowDeepLink.tryParse('https://example.com'), isNull);
    });
  });
}
