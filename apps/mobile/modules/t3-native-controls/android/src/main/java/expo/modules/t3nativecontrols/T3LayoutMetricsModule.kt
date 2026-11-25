package expo.modules.t3nativecontrols

import android.content.Context
import android.view.WindowInsets
import androidx.core.view.WindowInsetsCompat
import expo.modules.kotlin.AppContext
import expo.modules.kotlin.modules.Module
import expo.modules.kotlin.modules.ModuleDefinition
import expo.modules.kotlin.viewevent.EventDispatcher
import expo.modules.kotlin.views.ExpoView

class T3LayoutMetricsModule : Module() {
  override fun definition() = ModuleDefinition {
    Name("T3LayoutMetrics")

    View(T3LayoutMetricsView::class) {
      Events("onMetricsChange")
    }
  }
}

/**
 * Reports the size and safe area of the React root it fills, as the iOS LayoutMetrics view does.
 * React Native Android keeps one window size for every window, so side by side each root needs
 * its own. The fold has its own observer (AndroidHingeObserver), so no hinge is reported here.
 */
class T3LayoutMetricsView(
  context: Context,
  appContext: AppContext
) : ExpoView(context, appContext) {
  private val onMetricsChange by EventDispatcher()
  private var lastMetrics: Map<String, Any>? = null

  override fun onAttachedToWindow() {
    super.onAttachedToWindow()
    lastMetrics = null
    requestApplyInsets()
    publishMetrics()
  }

  override fun onSizeChanged(width: Int, height: Int, oldWidth: Int, oldHeight: Int) {
    super.onSizeChanged(width, height, oldWidth, oldHeight)
    publishMetrics()
  }

  override fun onApplyWindowInsets(insets: WindowInsets): WindowInsets {
    publishMetrics()
    return super.onApplyWindowInsets(insets)
  }

  private fun publishMetrics() {
    if (width <= 0 || height <= 0) return
    val density = resources.displayMetrics.density
    val widthDp = width / density
    val metrics = mapOf(
      "width" to widthDp.toDouble(),
      "height" to (height / density).toDouble(),
      "hasHinge" to false,
      // Material's window size classes: medium from 600dp.
      "horizontalSizeClass" to if (widthDp >= REGULAR_MIN_WIDTH_DP) "regular" else "compact",
      "verticalBarEdge" to "none",
      "safeArea" to safeArea(density),
      "reservedRegions" to emptyList<Any>()
    )
    if (metrics == lastMetrics) return
    lastMetrics = metrics
    onMetricsChange(metrics)
  }

  // The window's system bars and cutout, where they overlap this view.
  private fun safeArea(density: Float): Map<String, Double> {
    val insets = rootWindowInsets?.let {
      WindowInsetsCompat.toWindowInsetsCompat(it, this).getInsets(
        WindowInsetsCompat.Type.systemBars() or WindowInsetsCompat.Type.displayCutout()
      )
    }
    val location = IntArray(2).also(::getLocationInWindow)
    val root = rootView
    fun edge(
      inset: Int?,
      offset: Int
    ) = ((inset ?: 0) - offset).coerceAtLeast(0) / density.toDouble()
    return mapOf(
      "top" to edge(insets?.top, location[1]),
      "bottom" to edge(insets?.bottom, root.height - location[1] - height),
      "left" to edge(insets?.left, location[0]),
      "right" to edge(insets?.right, root.width - location[0] - width)
    )
  }
}

private const val REGULAR_MIN_WIDTH_DP = 600f
