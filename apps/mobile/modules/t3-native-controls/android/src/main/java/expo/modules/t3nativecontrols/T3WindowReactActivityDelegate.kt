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
import com.facebook.react.ReactApplication
import com.facebook.react.ReactHost
import com.facebook.react.bridge.Arguments
import com.facebook.react.bridge.ReactContext
import com.facebook.react.common.LifecycleState
import com.facebook.react.defaults.DefaultReactActivityDelegate
import com.facebook.react.modules.core.DefaultHardwareBackBtnHandler
import java.lang.ref.WeakReference

/** The T3 Code windows (activities) open on the one React host, oldest first. */
object T3Windows {
  internal val lifecycle = T3WindowLifecycle<Activity, String> { it.isDestroyed }

  val activities: List<Activity>
    get() = lifecycle.windows

  /**
   * A window's JS id arrived (T3WindowState). A link it held meanwhile goes straight to that
   * window's JS: native listeners heard its intent already, and the window in use stays.
   */
  internal fun listening(window: Activity, jsId: Int?) {
    val host = (window.application as? ReactApplication)?.reactHost ?: return
    val held = lifecycle.listening(window, jsId)
    lifecycle.inUse(window)?.let(host::announceWindowInUse)
    if (held != null && jsId != null) {
      val link = Arguments.createMap().apply {
        putInt("windowId", jsId)
        putString("url", held)
      }
      host.currentReactContext?.emitDeviceEvent(WINDOW_LINK_EVENT, link)
    }
  }

  /** JS declined a Back press from the window with this JS id; it closed if none has it now. */
  internal fun runDefaultBack(jsId: Int) {
    val window = lifecycle.defaultBackWindow(jsId) as? DefaultHardwareBackBtnHandler
    window?.invokeDefaultOnBackPressed()
  }
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
    reactHost?.announceWindowInUse(id)
    return super.onBackPressed()
  }

  /**
   * React Native hands the link to the activity it serves, and JS opens it in the active window.
   * Both move to this window first, even when it is paused beside a resumed one. Before this
   * window's JS can take a link, the window holds it (T3Windows.listening delivers it).
   */
  override fun onNewIntent(intent: Intent?): Boolean {
    val host = reactHost
    if (host == null || intent == null) return super.onNewIntent(intent)
    val link = launchURL(intent.action, intent.dataString)
    if (link != null && T3Windows.lifecycle.holdsLink(window, link)) {
      // Other listeners still hear the intent; only its link waits for this window's JS.
      host.currentReactContext?.onNewIntent(window, intent)
    } else {
      host.deliverLink(window, intent)
    }
    return true
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

  // JS activates a window only once the host serves it, not on every native focus.
  private fun follow(step: T3WindowLifecycle.Step<Activity>) {
    val host = reactHost ?: return
    host.follow(step)
    T3Windows.lifecycle.servedAfter(step, window)?.let(host::announceWindowInUse)
  }
}

// Back and opened links reach JS app-wide; JS hears their window first, on the same channel.
private fun ReactHost.announceWindowInUse(id: Int) {
  currentReactContext?.emitDeviceEvent(WINDOW_IN_USE_EVENT, id)
}

private fun ReactHost.follow(step: T3WindowLifecycle.Step<Activity>) {
  val next = (step as? T3WindowLifecycle.Step.Follow)?.window ?: return
  // Already resumed, the host only moves its activity to the window.
  onHostResume(next, next as? DefaultHardwareBackBtnHandler)
  // The host sets ReactContext's activity, which modules present from, only when it resumes
  // from paused.
  serveFromContext(next)
}

private fun ReactHost.deliverLink(window: Activity, intent: Intent) {
  follow(T3Windows.lifecycle.intentArrived(window))
  T3Windows.lifecycle.jsId(window)?.let(::announceWindowInUse)
  onNewIntent(intent)
  // A paused host keeps the window it paused with, and gave ReactContext that window just now.
  if (lifecycleState != LifecycleState.RESUMED) serveFromContext(window)
}

private fun ReactHost.serveFromContext(activity: Activity) {
  val context = currentReactContext ?: return
  try {
    reactContextActivity?.set(context, WeakReference(activity))
  } catch (error: ReflectiveOperationException) {
    Log.w(TAG, "Could not move React Native to the window in use", error)
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

// NativeWindowObserver.android listens for them.
private const val WINDOW_IN_USE_EVENT = "T3WindowInUse"
private const val WINDOW_LINK_EVENT = "T3WindowLink"
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
