package expo.modules.t3nativecontrols

import android.app.Activity
import android.content.Context
import android.content.ContextWrapper
import android.util.Log
import com.facebook.react.ReactActivity
import com.facebook.react.bridge.ReactContext
import com.facebook.react.defaults.DefaultReactActivityDelegate
import com.facebook.react.modules.core.DefaultHardwareBackBtnHandler
import java.lang.ref.WeakReference

/** The T3 Code windows (activities) open on the one React host, oldest first. */
object T3Windows {
  internal val lifecycle = T3WindowLifecycle<Activity> { it.isDestroyed }

  val activities: List<Activity>
    get() = lifecycle.windows
}

/**
 * MainActivity's delegate; withAndroidMultipleWindows installs it. React Native hears each
 * window's lifecycle through [T3WindowLifecycle] instead of directly.
 */
open class T3WindowReactActivityDelegate(
  private val window: ReactActivity,
  mainComponentName: String,
  fabricEnabled: Boolean
) : DefaultReactActivityDelegate(window, mainComponentName, fabricEnabled) {
  override fun onResume() {
    T3Windows.lifecycle.resumed(window)
    super.onResume()
  }

  override fun onWindowFocusChanged(hasFocus: Boolean) {
    if (hasFocus) follow(T3Windows.lifecycle.focused(window))
    super.onWindowFocusChanged(hasFocus)
  }

  override fun onPause() {
    val step = T3Windows.lifecycle.paused(window)
    if (step == T3WindowLifecycle.Step.Forward) super.onPause() else follow(step)
  }

  override fun onDestroy() {
    val step = T3Windows.lifecycle.destroyed(window)
    if (step == T3WindowLifecycle.Step.Forward) {
      super.onDestroy()
      // The host may still point at a window that closed while none was in use.
      reactHost?.onHostDestroy()
    } else {
      reactDelegate?.unloadApp()
      follow(step)
    }
  }

  private fun follow(step: T3WindowLifecycle.Step<Activity>) {
    val next = (step as? T3WindowLifecycle.Step.Follow)?.window ?: return
    val host = reactHost ?: return
    // Already resumed, the host only moves its activity and back handler to the window.
    host.onHostResume(next, next as? DefaultHardwareBackBtnHandler)
    // ReactContext keeps its own activity, which modules present from; the host sets it only
    // when it resumes from paused.
    host.currentReactContext?.let { context ->
      try {
        reactContextActivity?.set(context, WeakReference(next))
      } catch (error: ReflectiveOperationException) {
        Log.w(TAG, "Could not move React Native to the window in use", error)
      }
    }
  }
}

// Top level, not a companion: MainActivity's `object : T3WindowReactActivityDelegate(this, ...)`
// would resolve `this` to a companion object.
private const val TAG = "T3Windows"
private val reactContextActivity =
  runCatching {
    ReactContext::class.java.getDeclaredField("mCurrentActivity").apply { isAccessible = true }
  }.onFailure { Log.w(TAG, "ReactContext has no activity field", it) }.getOrNull()

/** The activity a view's React root is mounted in; ThemedReactContext wraps it. */
internal fun Context.hostActivity(): Activity? {
  var context: Context? = this
  while (context is ContextWrapper) {
    if (context is Activity) return context
    context = context.baseContext
  }
  return null
}
