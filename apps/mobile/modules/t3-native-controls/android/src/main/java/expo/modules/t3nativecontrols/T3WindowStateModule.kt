package expo.modules.t3nativecontrols

import android.content.Context
import expo.modules.kotlin.AppContext
import expo.modules.kotlin.modules.Module
import expo.modules.kotlin.modules.ModuleDefinition
import expo.modules.kotlin.viewevent.EventDispatcher
import expo.modules.kotlin.views.ExpoView

class T3WindowStateModule : Module() {
  override fun definition() = ModuleDefinition {
    Name("T3WindowState")

    View(T3WindowStateView::class) {
      Events("onWindowStateChange")
      Prop("windowId") { view: T3WindowStateView, id: Int ->
        view.context.hostActivity()?.let { T3Windows.appWindowIds[it] = id }
      }
    }
  }
}

/**
 * Tells a React root about the window (activity) it is in: in use when the window gains focus,
 * as a tap does side by side, and closed once the activity is destroyed.
 */
class T3WindowStateView(
  context: Context,
  appContext: AppContext
) : ExpoView(context, appContext) {
  private val onWindowStateChange by EventDispatcher()

  override fun onAttachedToWindow() {
    super.onAttachedToWindow()
    // A window opens in use, as its React root assumes when it mounts.
    onWindowStateChange(mapOf("state" to "active"))
  }

  override fun onWindowFocusChanged(hasWindowFocus: Boolean) {
    super.onWindowFocusChanged(hasWindowFocus)
    if (hasWindowFocus) onWindowStateChange(mapOf("state" to "active"))
  }

  override fun onDetachedFromWindow() {
    // The activity removes its views as it is destroyed, before its React root unloads.
    val activity = context.hostActivity()
    if (activity != null && (activity.isFinishing || activity.isDestroyed)) {
      onWindowStateChange(mapOf("state" to "closed"))
    }
    super.onDetachedFromWindow()
  }
}
