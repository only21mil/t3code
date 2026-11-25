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

    /** React Native now serves this resumed window instead. */
    data class Follow<W>(val window: W) : Step<W>

    /** The window in use closed while resumed and no other is: React Native pauses. */
    data object Pause : Step<Nothing>
  }

  // Windows that have resumed and are not destroyed.
  private val open = mutableListOf<W>()

  // Resumed windows, the one used last at the end.
  private val resumed = mutableListOf<W>()

  /** The window React Native serves. */
  var current: W? = null
    private set

  // Whether React Native last heard that the app has focus.
  private var hasFocus = false

  val windows: List<W>
    get() = open.filterNot(isGone)

  /** Forward, or Follow too when another window is resumed: React Native then keeps its context. */
  fun resumed(window: W): Step<W> {
    prune()
    if (window !in open) open += window
    val besideAnother = resumed.any { it !== window }
    use(window)
    return if (besideAnother) Step.Follow(window) else Step.Forward
  }

  fun focused(window: W): Step<W> {
    if (window === current || window !in resumed) return Step.Hold
    use(window)
    return Step.Follow(window)
  }

  /**
   * Whether React Native hears this focus change. Focus moving between windows, as a tap on the
   * other one does, is no change for the app. Call it for a loss once a gain elsewhere could land.
   */
  fun focusChanged(window: W, gained: Boolean): Boolean {
    if (gained == hasFocus || (!gained && window !== current)) return false
    hasFocus = gained
    return true
  }

  fun paused(window: W): Step<W> {
    prune()
    resumed.remove(window)
    return if (window === current) followLastResumed(whenNone = Step.Forward) else Step.Hold
  }

  /** The caller unloads this window's React root whatever the step. */
  fun destroyed(window: W): Step<W> {
    val wasResumed = window in resumed
    open.remove(window)
    resumed.remove(window)
    val wasCurrent = window === current
    prune()
    return when {
      open.isEmpty() -> {
        current = null
        Step.Forward
      }
      !wasCurrent -> Step.Hold
      else -> {
        current = null
        // With no window in use, the host stays paused until another window resumes.
        followLastResumed(whenNone = if (wasResumed) Step.Pause else Step.Hold)
      }
    }
  }

  // A window can be gone before its own callback arrives, as when several close at once.
  private fun prune() {
    open.removeAll(isGone)
    resumed.removeAll(isGone)
    if (current?.let(isGone) == true) current = null
  }

  private fun followLastResumed(whenNone: Step<W>): Step<W> {
    val next = resumed.lastOrNull() ?: return whenNone
    use(next)
    return Step.Follow(next)
  }

  private fun use(window: W) {
    resumed.remove(window)
    resumed += window
    current = window
  }
}
