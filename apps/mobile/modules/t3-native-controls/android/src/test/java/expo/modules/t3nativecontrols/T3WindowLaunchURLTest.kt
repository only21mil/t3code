package expo.modules.t3nativecontrols

import org.junit.Assert.assertEquals
import org.junit.Assert.assertNull
import org.junit.Test
import org.junit.runner.RunWith
import org.robolectric.RobolectricTestRunner
import org.robolectric.annotation.Config

// launchURL's file sets up a main-thread Handler when it loads, which needs Android's Looper.
@RunWith(RobolectricTestRunner::class)
@Config(sdk = [36], manifest = Config.NONE)
class T3WindowLaunchURLTest {
  @Test
  fun aWindowOpenedFromALinkReadsThatLink() {
    assertEquals(
      "t3code://threads/demo/t1",
      launchURL("android.intent.action.VIEW", "t3code://threads/demo/t1")
    )
  }

  // An explicit null: the root must not fall back to another window's launch link.
  @Test
  fun aWindowOpenedFromTheLauncherHasNoLink() {
    assertNull(launchURL("android.intent.action.MAIN", null))
    assertNull(launchURL("android.intent.action.SEND", "content://shared/1"))
  }
}
