package expo.modules.t3nativecontrols

import android.app.Activity
import android.content.Context
import android.content.ContextWrapper
import android.content.Intent
import android.nfc.NfcAdapter
import android.os.Bundle
import android.os.Handler
import android.os.Looper
import android.util.Log
import com.facebook.react.ReactActivity
import com.facebook.react.bridge.ReactContext
import com.facebook.react.common.LifecycleState
import com.facebook.react.defaults.DefaultReactActivityDelegate
import com.facebook.react.modules.core.DefaultHardwareBackBtnHandler
import java.lang.ref.WeakReference

/** The T3 Code windows (activities) open on the one React host, oldest first. */
object T3Windows {
  internal val lifecycle = T3WindowLifecycle<Activity> { it.isDestroyed }

  // React Native runs its default Back once JS declines a press. It acts on the window the press
  // came from, not the one the host serves by then.
  internal val defaultBack = DefaultHardwareBackBtnHandler {
    (lifecycle.defaultBackWindow() as? DefaultHardwareBackBtnHandler)?.invokeDefaultOnBackPressed()
  }

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
  private var pendingFocusLoss: Runnable? = null

  // Each window's root reads its own launch link; ReactContext's activity may be another window.
  override fun getLaunchOptions(): Bundle =
    Bundle().apply {
      putString(LAUNCH_URL_PROP, launchURL(window.intent?.action, window.intent?.dataString))
    }

  override fun onResume() {
    val step = T3Windows.lifecycle.resumed(window)
    super.onResume()
    follow(step)
  }

  override fun onWindowFocusChanged(hasFocus: Boolean) {
    if (hasFocus) {
      cancelFocusLoss()
      follow(T3Windows.lifecycle.focused(window))
      if (T3Windows.lifecycle.focusGained(window)) super.onWindowFocusChanged(true)
      return
    }
    // A tap on the window beside this one gives it focus right after this loss.
    val token = T3Windows.lifecycle.focusToken
    val loss = Runnable {
      pendingFocusLoss = null
      if (!window.isDestroyed && T3Windows.lifecycle.focusLossLands(window, token)) {
        reactDelegate?.onWindowFocusChanged(false)
      }
    }
    cancelFocusLoss()
    pendingFocusLoss = loss
    mainHandler.post(loss)
  }

  /** Until this window's JS can tell a press is its own, Back stays with Android in this window. */
  override fun onBackPressed(): Boolean {
    val id = T3Windows.lifecycle.backPressed(window) ?: return false
    follow(T3Windows.lifecycle.focused(window))
    announceWindowInUse(id)
    return super.onBackPressed()
  }

  /**
   * React Native hands the link to the activity it serves, and JS opens it in the active window.
   * Both move to this window first, even when it is paused beside a resumed one.
   */
  override fun onNewIntent(intent: Intent?): Boolean {
    follow(T3Windows.lifecycle.intentArrived(window))
    T3Windows.lifecycle.jsId(window)?.let(::announceWindowInUse)
    val handled = super.onNewIntent(intent)
    // A paused host keeps the window it paused with, and gave ReactContext that window just now.
    if (reactHost?.lifecycleState != LifecycleState.RESUMED) serveFromContext(window)
    return handled
  }

  override fun onPause() {
    when (val step = T3Windows.lifecycle.paused(window)) {
      T3WindowLifecycle.Step.Forward -> super.onPause()
      T3WindowLifecycle.Step.Pause -> reactHost?.onHostPause()
      else -> follow(step)
    }
  }

  override fun onDestroy() {
    cancelFocusLoss()
    val step = T3Windows.lifecycle.destroyed(window)
    if (step == T3WindowLifecycle.Step.Forward) {
      super.onDestroy()
      // The host may still point at a window that closed while none was in use.
      reactHost?.onHostDestroy()
    } else {
      if (step == T3WindowLifecycle.Step.Pause) reactHost?.onHostPause()
      reactDelegate?.unloadApp()
      follow(step)
    }
  }

  private fun cancelFocusLoss() {
    pendingFocusLoss?.let(mainHandler::removeCallbacks)
    pendingFocusLoss = null
  }

  // Back and opened links reach JS app-wide; JS hears their window first, on the same channel.
  private fun announceWindowInUse(id: Int) {
    reactHost?.currentReactContext?.emitDeviceEvent(WINDOW_IN_USE_EVENT, id)
  }

  private fun follow(step: T3WindowLifecycle.Step<Activity>) {
    val next = (step as? T3WindowLifecycle.Step.Follow)?.window ?: return
    val host = reactHost ?: return
    // Already resumed, the host only moves its activity to the window.
    host.onHostResume(next, T3Windows.defaultBack)
    // The host sets ReactContext's activity, which modules present from, only when it resumes
    // from paused.
    serveFromContext(next)
  }

  private fun serveFromContext(activity: Activity) {
    val context = reactHost?.currentReactContext ?: return
    try {
      reactContextActivity?.set(context, WeakReference(activity))
    } catch (error: ReflectiveOperationException) {
      Log.w(TAG, "Could not move React Native to the window in use", error)
    }
  }
}

/** The link a window was launched with, as React Native's getInitialURL reads it; else null. */
internal fun launchURL(action: String?, data: String?): String? =
  data?.takeIf { action == Intent.ACTION_VIEW || action == NfcAdapter.ACTION_NDEF_DISCOVERED }

// Top level, not a companion: MainActivity's `object : T3WindowReactActivityDelegate(this, ...)`
// would resolve `this` to a companion object.
private const val TAG = "T3Windows"

// App.tsx reads it from the root's initial props.
private const val LAUNCH_URL_PROP = "launchURL"

// NativeWindowObserver.android listens for it.
private const val WINDOW_IN_USE_EVENT = "T3WindowInUse"
private val mainHandler = Handler(Looper.getMainLooper())
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
