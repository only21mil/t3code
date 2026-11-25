package expo.modules.t3nativecontrols

import android.app.Activity
import android.content.Context
import android.content.Intent
import android.os.Bundle
import androidx.appcompat.app.AppCompatActivity
import expo.modules.kotlin.activityresult.AppContextActivityResultContract
import expo.modules.kotlin.activityresult.AppContextActivityResultRegistry
import expo.modules.kotlin.providers.CurrentActivityProvider
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Test
import org.junit.runner.RunWith
import org.robolectric.Robolectric
import org.robolectric.RobolectricTestRunner
import org.robolectric.Shadows.shadowOf
import org.robolectric.annotation.Config

/**
 * Expo registers each module's activity-result launchers once, with the first window, and drops
 * them when that window is destroyed (patches/expo-modules-core@58.1.0.patch keeps one in flight,
 * then drops it once its result is delivered).
 */
@RunWith(RobolectricTestRunner::class)
@Config(sdk = [36], manifest = Config.NONE)
class WindowActivityResultTest {
  class Window : AppCompatActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
      setTheme(androidx.appcompat.R.style.Theme_AppCompat)
      super.onCreate(savedInstanceState)
    }
  }

  private enum class Pick { Image }

  private object PickContract : AppContextActivityResultContract<Pick, Int> {
    override fun createIntent(context: Context, input: Pick) = Intent(Intent.ACTION_GET_CONTENT)

    override fun parseResult(input: Pick, resultCode: Int, intent: Intent?) = resultCode
  }

  @Test
  fun aPickerResultReachesTheSecondWindowAfterTheFirstCloses() {
    val first = Robolectric.buildActivity(Window::class.java).setup()
    val second = Robolectric.buildActivity(Window::class.java).setup()
    var current: Activity = first.get()
    val registry = AppContextActivityResultRegistry(
      object : CurrentActivityProvider {
        override val currentActivity: Activity
          get() = current
      }
    )
    val picker = registry.register("picker", first.get(), PickContract) { _, _ -> }

    current = second.get()
    var result: Int? = null
    picker.launch(Pick.Image) { result = it }
    val requestCode = shadowOf(second.get()).nextStartedActivityForResult.requestCode
    first.pause().stop().destroy()
    registry.dispatchResult(requestCode, Activity.RESULT_OK, null)

    assertEquals(Activity.RESULT_OK, result)

    // The first window's registration is gone with its last result; the next pick from the second
    // window registers again with it.
    assertFalse(registry.dispatchResult(requestCode, Activity.RESULT_OK, null))
    var secondResult: Int? = null
    picker.launch(Pick.Image) { secondResult = it }
    val secondRequestCode = shadowOf(second.get()).nextStartedActivityForResult.requestCode
    registry.dispatchResult(secondRequestCode, Activity.RESULT_CANCELED, null)
    assertEquals(Activity.RESULT_CANCELED, secondResult)
  }
}
