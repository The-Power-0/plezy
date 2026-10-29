## Stage 06 — prioritize cold-start Plex video

Upstream already schedules most noncritical tasks after the first app frame, and its database/credentials/PlexHome startup gating is correctness-critical. We intentionally preserve that logic.

This custom Fire TV overlay skips third-party tracker initialization entirely when Stage 01 has disabled all trackers and their persisted write queue. It also skips the scheduled TV virtual-keyboard text warmup, which normally runs 3 seconds after opening the app and can compete with HA-initiated media launch. In this appliance, the first manual keyboard invocation may incur an additional font/layout delay; that is an explicit performance tradeoff.

These are source-only changes, not proof of performance gains. When building later, compare cold startup, HA shuffle-to-first-frame, D-pad search latency and other pending work with the prior candidate. Standard Plezy defaults retain the original behavior.
