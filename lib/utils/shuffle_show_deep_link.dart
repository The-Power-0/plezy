import 'package:flutter/widgets.dart';

import '../media/ids.dart';
import '../media/media_kind.dart';
import '../providers/multi_server_provider.dart';
import '../services/media_list_playback_launcher.dart';
import 'app_logger.dart';

/// A `plezy://shuffle` deep link that starts Plezy's normal shuffled-show
/// playback flow.
///
/// Format: `plezy://shuffle?server=<serverId>&show=<showRatingKey>`
class ShuffleShowDeepLink {
  const ShuffleShowDeepLink({
    required this.serverId,
    required this.showRatingKey,
  });

  static const scheme = 'plezy';
  static const host = 'shuffle';

  static const coldStartAttempts = 10;
  static const coldStartRetryDelay = Duration(seconds: 1);

  final String serverId;
  final String showRatingKey;

  static ShuffleShowDeepLink? tryParse(String link) {
    final uri = Uri.tryParse(link);
    if (uri == null || uri.scheme != scheme || uri.host != host) {
      return null;
    }

    final server = uri.queryParameters['server']?.trim();
    final show = uri.queryParameters['show']?.trim();

    if (server == null || server.isEmpty || show == null || show.isEmpty) {
      return null;
    }

    return ShuffleShowDeepLink(serverId: server, showRatingKey: show);
  }

  /// Resolves the requested show and delegates to Plezy's existing shuffled
  /// play-queue launcher.
  ///
  /// Returns true when playback was successfully launched.
  Future<bool> launch(
    BuildContext context,
    MultiServerProvider multiServer,
  ) async {
    final requestedServer = ServerId(serverId);
    var client = multiServer.getClientForServer(requestedServer);

    // On a cold Fire TV launch, the deep link can reach Flutter before the
    // saved media-server connection has finished coming back online.
    for (
      var attempt = 0;
      client == null && attempt < coldStartAttempts;
      attempt++
    ) {
      await Future<void>.delayed(coldStartRetryDelay);

      if (!context.mounted) {
        return false;
      }

      client = multiServer.getClientForServer(requestedServer);
    }

    if (client == null) {
      appLogger.w('Shuffle deep link: server $serverId is not available');
      return false;
    }

    final metadata = await client.fetchItem(showRatingKey);

    if (metadata == null) {
      appLogger.w(
        'Shuffle deep link: show $showRatingKey was not found on $serverId',
      );
      return false;
    }

    if (metadata.kind != MediaKind.show && metadata.kind != MediaKind.season) {
      appLogger.w('Shuffle deep link: $showRatingKey is not a show or season');
      return false;
    }

    if (!context.mounted) {
      return false;
    }

    final launcher = MediaListPlaybackLauncher.forItem(context, metadata);

    final result = await launcher.launchShuffledShow(metadata: metadata);

    return result is PlayQueueSuccess;
  }
}
