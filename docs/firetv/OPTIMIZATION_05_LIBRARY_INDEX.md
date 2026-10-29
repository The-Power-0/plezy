## Stage 05 — Browse grid key lookup

Plezy 2.25.0 currently scans the entire sparse `loadedItems` map whenever Flutter's sliver key reconciliation asks where an item moved. On large Plex libraries, repeated scans during live refresh or scrolling cost O(N) per callback.

The candidate source overlay builds one ID-to-index snapshot when the library sliver is rebuilt and uses O(1) lookup in the common case. It verifies that the item at the cached index still has the same ID. If an asynchronous refresh changed the sparse map mid-frame, the previous linear lookup is retained as a safe fallback; no persistent state or fragile invalidation hook is added.

Source-only check confirms all guards; actual Flutter compilation and p95/p99 navigation performance remain untested. The original widget, Plex requests, sort order, focused item and Home Assistant shuffle routing are unchanged.
