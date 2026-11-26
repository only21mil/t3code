package expo.modules.t3nativecontrols

import android.content.Context
import expo.modules.kotlin.AppContext
import expo.modules.kotlin.functions.Queues
import expo.modules.kotlin.modules.Module
import expo.modules.kotlin.modules.ModuleDefinition
import expo.modules.kotlin.viewevent.EventDispatcher
import expo.modules.kotlin.views.ExpoView

class T3WindowStateModule : Module() {
  override fun definition() = ModuleDefinition {
    Name("T3WindowState")

    // NativeWindowObserver.android runs React Native's default Back in the window a press came
    // from, which JS names by the id T3WindowInUse gave it.
    AsyncFunction("runDefaultBack") { jsId: Int ->
      T3Windows.runDefaultBack(jsId)
    }.runOnQueue(Queues.MAIN)

    View(T3WindowStateView::class) {
      Events("onWindowStateChange")
      // NativeWindowObserver.android hears T3WindowInUse before any root mounts, and sets the id
      // once this window's navigation hears links.
      Prop("windowId") { view: T3WindowStateView, id: Int ->
        view.context.hostActivity()?.let { T3Windows.listening(it, id.takeIf { id > 0 }) }
      }
    }
  }
}

/** Tells a React root that the window (activity) it is in closed, once the activity is destroyed. */
class T3WindowStateView(
  context: Context,
  appContext: AppContext
) : ExpoView(context, appContext) {
  private val onWindowStateChange by EventDispatcher()

  override fun onDetachedFromWindow() {
    // The activity removes its views as it is destroyed, before its React root unloads.
    val activity = context.hostActivity()
    if (activity != null && (activity.isFinishing || activity.isDestroyed)) {
      // A finished task's dialogs end with it; a recreated window's move to the window in use.
      onWindowStateChange(mapOf("state" to if (activity.isFinishing) "finished" else "closed"))
    }
    super.onDetachedFromWindow()
  }
}
