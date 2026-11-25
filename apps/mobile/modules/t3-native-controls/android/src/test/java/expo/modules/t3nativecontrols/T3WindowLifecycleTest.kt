package expo.modules.t3nativecontrols

import expo.modules.t3nativecontrols.T3WindowLifecycle.Step
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Test

class T3WindowLifecycleTest {
  private val gone = mutableSetOf<String>()
  private val lifecycle = T3WindowLifecycle<String> { it in gone }

  @Test
  fun forwardsEveryCallbackOfASingleWindow() {
    assertEquals(Step.Forward, lifecycle.resumed("a"))
    assertEquals(Step.Hold, lifecycle.focused("a"))
    assertEquals(Step.Forward, lifecycle.paused("a"))
    assertEquals(Step.Forward, lifecycle.resumed("a"))
    assertEquals(Step.Forward, lifecycle.paused("a"))
    assertEquals(Step.Forward, lifecycle.destroyed("a"))
  }

  @Test
  fun staysResumedWhileEitherWindowSideBySideIs() {
    lifecycle.resumed("a")
    lifecycle.resumed("b")

    // Only the window React Native serves may pause it; the other one takes over.
    assertEquals(Step.Follow("a"), lifecycle.paused("b"))
    assertEquals(Step.Follow("b"), lifecycle.resumed("b"))
    assertEquals(Step.Hold, lifecycle.paused("a"))
    assertEquals(Step.Forward, lifecycle.paused("b"))
  }

  @Test
  fun servesTheWindowThatGainedFocus() {
    lifecycle.resumed("a")
    lifecycle.resumed("b")

    assertEquals(Step.Follow("a"), lifecycle.focused("a"))
    assertEquals(Step.Hold, lifecycle.focused("a"))
    assertEquals(Step.Hold, lifecycle.paused("b"))
    // A window that is not resumed cannot be the one in use.
    assertEquals(Step.Hold, lifecycle.focused("b"))
    assertEquals(Step.Forward, lifecycle.paused("a"))
  }

  @Test
  fun destroysTheHostOnlyWithTheLastWindow() {
    lifecycle.resumed("a")
    lifecycle.resumed("b")

    assertEquals(Step.Follow("a"), lifecycle.destroyed("b"))
    assertEquals(listOf("a"), lifecycle.windows)
    assertEquals(Step.Forward, lifecycle.paused("a"))
    assertEquals(Step.Forward, lifecycle.destroyed("a"))
  }

  @Test
  fun holdsWhenAWindowClosesWhileNoneIsInUse() {
    lifecycle.resumed("a")
    lifecycle.resumed("b")
    lifecycle.paused("a")
    assertEquals(Step.Forward, lifecycle.paused("b"))

    assertEquals(Step.Hold, lifecycle.destroyed("b"))
    assertEquals(Step.Forward, lifecycle.resumed("a"))
  }

  @Test
  fun treatsWindowsAlreadyGoneAsClosed() {
    lifecycle.resumed("a")
    lifecycle.resumed("b")
    lifecycle.paused("b")
    lifecycle.paused("a")
    gone += "b"

    assertEquals(listOf("a"), lifecycle.windows)
    assertEquals(Step.Forward, lifecycle.destroyed("a"))
  }

  @Test
  fun followsAWindowThatResumesBesideAnother() {
    assertEquals(Step.Forward, lifecycle.resumed("a"))
    // React Native is already resumed, so only Follow moves its context to the new window.
    assertEquals(Step.Follow("b"), lifecycle.resumed("b"))
  }

  @Test
  fun neverFollowsAWindowAlreadyGone() {
    lifecycle.resumed("a")
    lifecycle.resumed("b")
    gone += "a"

    assertEquals(Step.Forward, lifecycle.paused("b"))
  }

  @Test
  fun pausesTheHostWhenTheWindowInUseClosesWhileTheOthersArePaused() {
    lifecycle.resumed("a")
    lifecycle.resumed("b")
    lifecycle.paused("a")

    assertEquals(Step.Pause, lifecycle.destroyed("b"))
    assertNull(lifecycle.current)
  }

  @Test
  fun forgetsTheWindowInUseOnceItIsDestroyed() {
    lifecycle.resumed("a")
    lifecycle.resumed("b")
    lifecycle.paused("a")
    lifecycle.paused("b")

    assertEquals(Step.Hold, lifecycle.destroyed("b"))
    assertNull(lifecycle.current)
  }

  @Test
  fun hearsFocusOnlyWhenTheAppGainsOrLosesIt() {
    lifecycle.resumed("a")
    lifecycle.resumed("b")
    lifecycle.focused("a")
    assertTrue(lifecycle.focusGained("a"))

    // A tap on b: b gains focus, then a's loss is checked.
    val aLoss = lifecycle.focusToken
    lifecycle.focused("b")
    assertFalse(lifecycle.focusGained("b"))
    assertFalse(lifecycle.focusLossLands("a", aLoss))

    assertTrue(lifecycle.focusLossLands("b", lifecycle.focusToken))
    lifecycle.focused("a")
    assertTrue(lifecycle.focusGained("a"))
  }

  // S2
  @Test
  fun aWindowResumingWithoutFocusLeavesTheFocusedOneInUse() {
    lifecycle.resumed("a")
    lifecycle.focused("a")
    lifecycle.focusGained("a")
    // A new window still opens in use, as R2 and R7 rely on.
    assertEquals(Step.Follow("b"), lifecycle.resumed("b"))
    lifecycle.focused("a")
    lifecycle.paused("b")

    // super.onResume() moved the host to b; Follow moves it back to the window with focus.
    assertEquals(Step.Follow("a"), lifecycle.resumed("b"))
    assertEquals("a", lifecycle.current)
    // b still takes over once it gains focus, or once a pauses.
    assertEquals(Step.Follow("b"), lifecycle.focused("b"))
    lifecycle.focused("a")
    assertEquals(Step.Follow("b"), lifecycle.paused("a"))
  }

  // S9
  @Test
  fun dropsAFocusLossThatANewerGainOvertook() {
    lifecycle.resumed("a")
    lifecycle.focused("a")
    assertTrue(lifecycle.focusGained("a"))

    // A popup takes a's focus and gives it back before the posted loss runs.
    val loss = lifecycle.focusToken
    assertFalse(lifecycle.focusGained("a"))
    assertFalse(lifecycle.focusLossLands("a", loss))
    // A later loss still reaches React Native.
    assertTrue(lifecycle.focusLossLands("a", lifecycle.focusToken))
  }

  // S9
  @Test
  fun aClosedWindowNeverBlurs() {
    lifecycle.resumed("a")
    lifecycle.focused("a")
    lifecycle.focusGained("a")
    lifecycle.resumed("b")
    lifecycle.focused("a")
    val destroying = lifecycle.focusToken
    lifecycle.destroyed("a")
    assertFalse(lifecycle.focusLossLands("a", destroying))

    lifecycle.focusGained("b")
    // Gone before its own callbacks run, as when several windows close at once.
    val closing = lifecycle.focusToken
    gone += "b"
    assertFalse(lifecycle.focusLossLands("b", closing))
  }

  // S9
  @Test
  fun aPausedWindowCannotClaimFocus() {
    lifecycle.resumed("a")
    lifecycle.resumed("b")
    lifecycle.paused("b")

    assertFalse(lifecycle.focusGained("b"))
    assertTrue(lifecycle.focusGained("a"))
  }

  // S9
  @Test
  fun hearsFocusAgainOnceTheFocusedWindowCloses() {
    lifecycle.resumed("a")
    lifecycle.resumed("b")
    lifecycle.focused("b")
    assertTrue(lifecycle.focusGained("b"))

    lifecycle.destroyed("b")
    lifecycle.focused("a")
    assertTrue(lifecycle.focusGained("a"))

    // Home pauses the last window before its focus loss arrives.
    val loss = lifecycle.focusToken
    lifecycle.paused("a")
    assertTrue(lifecycle.focusLossLands("a", loss))
    lifecycle.resumed("a")
    assertTrue(lifecycle.focusGained("a"))
  }

  // S8, first trace: a and b resumed, b in use, b gone, then a pauses.
  @Test
  fun pausesTheHostWhenTheLastResumedWindowPausesAfterTheOneInUseWentAway() {
    lifecycle.resumed("a")
    lifecycle.resumed("b")
    gone += "b"

    assertEquals(Step.Pause, lifecycle.paused("a"))
    assertEquals(Step.Hold, lifecycle.destroyed("b"))
    assertEquals(Step.Forward, lifecycle.resumed("a"))
  }

  // S8, second trace: a, b and c open, a and b resumed, b in use, b gone, then a closes.
  @Test
  fun pausesTheHostWhenTheLastResumedWindowClosesAfterTheOneInUseWentAway() {
    lifecycle.resumed("a")
    lifecycle.resumed("b")
    lifecycle.resumed("c")
    lifecycle.paused("c")
    assertEquals("b", lifecycle.current)
    gone += "b"

    assertEquals(Step.Pause, lifecycle.destroyed("a"))
    // Exactly one pause: nothing after it pauses again.
    assertEquals(Step.Hold, lifecycle.destroyed("b"))
    assertEquals(Step.Forward, lifecycle.resumed("c"))
  }

  // S4
  @Test
  fun servesThePausedWindowALinkReaches() {
    lifecycle.resumed("a")
    lifecycle.resumed("b")
    lifecycle.paused("a")
    lifecycle.paused("b")
    // A paused host stays paused; the window resumes it right after the link.
    assertEquals(Step.Hold, lifecycle.intentArrived("a"))
    assertEquals(Step.Forward, lifecycle.resumed("a"))
    lifecycle.resumed("b")
    lifecycle.paused("a")

    // With b resumed, React Native and its context move to a before the link reaches them.
    assertEquals(Step.Follow("a"), lifecycle.intentArrived("a"))
    assertEquals("a", lifecycle.current)
    // a resumes next, as the link brings it forward; b's later focus takes the host back.
    assertEquals(Step.Follow("a"), lifecycle.resumed("a"))
    assertEquals(Step.Follow("b"), lifecycle.focused("b"))
  }

  // S6
  @Test
  fun keepsBackNativeUntilTheWindowsJsListens() {
    lifecycle.resumed("a")
    lifecycle.listening("a", 1)
    lifecycle.resumed("b")

    assertNull(lifecycle.backPressed("b"))
    assertEquals(1, lifecycle.backPressed("a"))
    lifecycle.listening("b", 2)
    assertEquals(2, lifecycle.backPressed("b"))
  }

  // S7
  @Test
  fun runsTheDefaultBackInTheWindowBackWasPressedIn() {
    lifecycle.resumed("a")
    lifecycle.resumed("b")
    lifecycle.focused("a")
    lifecycle.backPressed("a")

    // b takes the host over while JS decides; the default Back still belongs to a.
    lifecycle.focused("b")
    assertEquals("a", lifecycle.defaultBackWindow())
    lifecycle.destroyed("a")
    assertEquals("b", lifecycle.defaultBackWindow())
  }
}
