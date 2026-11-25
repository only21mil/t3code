package expo.modules.t3nativecontrols

/**
 * Decides what React Native's one host hears from several windows. Each T3 Code window on Android
 * is an activity of its own, and all of them share the host and its JS runtime, but the host
 * follows a single activity: pausing or destroying any one of them would pause or destroy the
 * app for every window. Here the host stays resumed while any window is, serves the window in
 * use, and is destroyed only with the last window.
 */
class T3WindowLifecycle<W : Any>(private val isGone: (W) -> Boolean) {
  sealed interface Step<out W> {
    /** Pass the callback on to React Native unchanged. */
    data object Forward : Step<Nothing>

    /** Another window keeps React Native as it is. */
    data object Hold : Step<Nothing>

    /** React Native now serves this window instead. */
    data class Follow<W>(val window: W) : Step<W>

    /** No window is resumed any more: React Native pauses without the window it served. */
    data object Pause : Step<Nothing>
  }

  // Windows that have resumed and are not destroyed.
  private val open = mutableListOf<W>()

  // Resumed windows, the one used last at the end.
  private val resumed = mutableListOf<W>()

  /** The window React Native serves. */
  var current: W? = null
    private set

  // Whether React Native is resumed: it pauses exactly once, when the last resumed window goes.
  private var hostResumed = false

  // The window React Native last heard has focus, if the app has it.
  private var focusedWindow: W? = null

  // Counts focus gains, so a loss posted before a newer gain is dropped.
  private var focusGains = 0

  // Each window's id in JS (lib/appWindows), once its JS hears T3WindowInUse.
  private val jsIds = mutableMapOf<W, Int>()

  // The window Back was last pressed in; React Native's default Back acts on it.
  private var backWindow: W? = null

  val windows: List<W>
    get() = open.filterNot(isGone)

  /**
   * Forward, or Follow when React Native is already resumed: it then keeps its context. A window
   * resuming without focus leaves the focused one in use, but a new window opens in use.
   */
  fun resumed(window: W): Step<W> {
    prune()
    val isNew = window !in open
    if (isNew) open += window
    val keep = current?.takeIf { !isNew && it !== window && it === focusedWindow && it in resumed }
    if (keep != null) {
      resumed.remove(window)
      resumed.add(resumed.indexOf(keep), window)
    } else {
      use(window)
    }
    if (!hostResumed) {
      hostResumed = true
      return Step.Forward
    }
    return Step.Follow(keep ?: window)
  }

  fun focused(window: W): Step<W> {
    if (window === current || window !in resumed) return Step.Hold
    use(window)
    return Step.Follow(window)
  }

  /**
   * Whether React Native hears that the app gained focus. Only the window in use, resumed, can
   * gain it; focus moving between windows, as a tap on the other one does, is no change.
   */
  fun focusGained(window: W): Boolean {
    focusGains++
    if (window !== current || window !in resumed || isGone(window)) return false
    val changed = focusedWindow == null
    focusedWindow = window
    return changed
  }

  /** Read on a focus loss; pass it to [focusLossLands] once a gain elsewhere could land. */
  val focusToken: Int
    get() = focusGains

  /** Whether React Native hears this loss: no gain came after it, and the window is still open. */
  fun focusLossLands(window: W, token: Int): Boolean {
    if (token != focusGains || window !== focusedWindow || !isOpen(window)) return false
    focusedWindow = null
    return true
  }

  /** A link reached this window. React Native serves it if it is resumed, even while it is not. */
  fun intentArrived(window: W): Step<W> {
    prune()
    if (window === current || !hostResumed || window !in open) return Step.Hold
    if (window in resumed) use(window) else current = window
    return Step.Follow(window)
  }

  /** This window's JS now hears which window Back and links came from; null when it stops. */
  fun listening(window: W, jsId: Int?) {
    if (jsId == null) jsIds.remove(window) else jsIds[window] = jsId
  }

  /** The window's id in JS, or null while its JS cannot tell yet that Back or a link is its own. */
  fun jsId(window: W): Int? = jsIds[window]

  /** Back was pressed in this window: its [jsId]. */
  fun backPressed(window: W): Int? {
    backWindow = window
    return jsId(window)
  }

  /** Where React Native's default Back acts once JS declines it. */
  fun defaultBackWindow(): W? = backWindow?.takeIf(::isOpen) ?: current

  fun paused(window: W): Step<W> {
    prune()
    resumed.remove(window)
    if (window !== current) return pauseIfNoneResumed()
    return followLastResumed() ?: Step.Forward.also { hostResumed = false }
  }

  /** The caller unloads this window's React root whatever the step. */
  fun destroyed(window: W): Step<W> {
    forget(window)
    val wasCurrent = window === current
    prune()
    return when {
      open.isEmpty() -> {
        current = null
        hostResumed = false
        Step.Forward
      }
      wasCurrent -> {
        current = null
        // With no window in use, the host stays paused until another window resumes.
        followLastResumed() ?: pauseIfNoneResumed()
      }
      else -> pauseIfNoneResumed()
    }
  }

  private fun pauseIfNoneResumed(): Step<W> {
    if (resumed.isNotEmpty() || !hostResumed) return Step.Hold
    hostResumed = false
    return Step.Pause
  }

  private fun isOpen(window: W) = window in open && !isGone(window)

  private fun forget(window: W) {
    open.remove(window)
    resumed.remove(window)
    jsIds.remove(window)
    if (focusedWindow === window) focusedWindow = null
    if (backWindow === window) backWindow = null
  }

  // A window can be gone before its own callback arrives, as when several close at once.
  private fun prune() {
    open.filter(isGone).forEach(::forget)
    resumed.removeAll(isGone)
    if (current?.let(isGone) == true) current = null
  }

  private fun followLastResumed(): Step<W>? {
    val next = resumed.lastOrNull() ?: return null
    use(next)
    return Step.Follow(next)
  }

  private fun use(window: W) {
    resumed.remove(window)
    resumed += window
    current = window
  }
}
