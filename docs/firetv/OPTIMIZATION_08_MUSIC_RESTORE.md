## Stage 08 — prevent saved music-session restore on the movies/TV appliance

Even after the music UI and MPV audio player are removed, upstream `MusicPlaybackServiceImpl` can restore the previous music queue from `MusicSessionStore` during provider creation. In a movies/TV-only APK that could attempt to instantiate the deliberately unsupported `Player.audio` path, compete with video startup, or produce an unnecessary playback error.

This source overlay passes a null `sessionStore` only when `kFireTvMoviesTvOnly` is enabled, retaining the shared `MusicPlaybackService` provider and video audio-focus ownership hooks. Default builds still receive the original profile session store. This is source-only; later compilation and a Fire TV playback/Back/shuffle smoke test are required.
