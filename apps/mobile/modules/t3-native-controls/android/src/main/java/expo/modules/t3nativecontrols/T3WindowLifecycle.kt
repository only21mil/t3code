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
  }

  // Windows that have resumed and are not destroyed.
  private val open = mutableListOf<W>()

  // Resumed windows, the one used last at the end.
  private val resumed = mutableListOf<W>()
  private var current: W? = null

  val windows: List<W>
    get() = open.filterNot(isGone)

  fun resumed(window: W): Step<W> {
    if (window !in open) open += window
    use(window)
    return Step.Forward
  }

  fun focused(window: W): Step<W> {
    if (window === current || window !in resumed) return Step.Hold
    use(window)
    return Step.Follow(window)
  }

  fun paused(window: W): Step<W> {
    resumed.remove(window)
    return if (window === current) followLastResumed(whenNone = Step.Forward) else Step.Hold
  }

  /** The caller unloads this window's React root whatever the step. */
  fun destroyed(window: W): Step<W> {
    open.remove(window)
    resumed.remove(window)
    // A window can be gone before its own callback arrives, as when several close at once.
    open.removeAll(isGone)
    resumed.removeAll(isGone)
    return when {
      open.isEmpty() -> {
        current = null
        Step.Forward
      }
      window !== current -> Step.Hold
      // With no window in use, the host stays paused until another window resumes.
      else -> followLastResumed(whenNone = Step.Hold)
    }
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
