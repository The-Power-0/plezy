# Stage 04 — Plezy Remote removal from the custom Fire TV edition

This source-only overlay opts the Fire TV appliance out of **Plezy Companion Remote**. It does not change Android's physical Fire TV remote, D-pad, Select/Back, native media keys, Plex playback, or Home Assistant's `plezy://shuffle` launch URI.

The `PLEZY_FIRETV_NO_COMPANION_REMOTE=true` build flag disables provider creation, host auto-start, LAN discovery, direct pairing by discovery or IP address, the Home remote button, server settings, profile logout access to a missing remote provider, player binding and background resume checks. Shared remote classes remain in the checkout until dependency reachability can be audited safely.

The normal Plezy build defaults the flag to false. Existing stored remote pairing data and preferences are not deleted, which avoids a destructive preference migration. Nothing in this stage publishes, builds, or installs an APK.

After all 16 performance workstreams, the manual candidate must compile, verify the APK and test physical Fire TV D-pad input, Back navigation, shuffle URI invocation and playback on Fire OS 7 and 8. The remote subsystem is not yet claimed to be absent from the final binary.
