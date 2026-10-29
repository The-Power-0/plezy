package com.edde746.plezy.exoplayer

import io.flutter.plugin.common.MethodCall
import io.flutter.plugin.common.MethodChannel
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertNull
import org.junit.Test
import org.junit.runner.RunWith
import org.robolectric.RobolectricTestRunner
import org.robolectric.annotation.Config

/** Tests for the Fire TV-specific Media3-only channel; no native MPV is linked. */
@RunWith(RobolectricTestRunner::class)
@Config(sdk = [28])
class ExoPlayerOnlyPluginTest {

  @Test
  fun unsupportedMediaCannotSwitchToAnyOtherPlaybackEngine() {
    val plugin = ExoPlayerPlugin()
    val didHandover = plugin.onFormatUnsupported(
      mediaGeneration = 3,
      uri = "https://example.invalid/media",
      headers = null,
      positionMs = 1000L,
      playWhenReady = true,
      errorMessage = "Unsupported video format"
    )
    assertFalse(didHandover)
  }

  @Test
  fun backendIsAlwaysExoPlayer() {
    val plugin = ExoPlayerPlugin()
    val result = RecordingResult()
    plugin.onMethodCall(MethodCall("getPlayerType", null), result)
    assertEquals("exoplayer", result.value)
    assertNull(result.errorCode)
  }

  @Test
  fun debugFallbackRequestIsRejectedExplicitly() {
    val plugin = ExoPlayerPlugin()
    val result = RecordingResult()
    plugin.onMethodCall(MethodCall("triggerFallback", null), result)
    assertEquals("UNSUPPORTED", result.errorCode)
  }

  private class RecordingResult : MethodChannel.Result {
    var value: Any? = null
    var errorCode: String? = null

    override fun success(result: Any?) { value = result }

    override fun error(errorCode: String, errorMessage: String?, errorDetails: Any?) {
      this.errorCode = errorCode
    }

    override fun notImplemented() { errorCode = "NOT_IMPLEMENTED" }
  }
}
