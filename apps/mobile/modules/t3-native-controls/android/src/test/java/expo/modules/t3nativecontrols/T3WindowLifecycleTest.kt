package expo.modules.t3nativecontrols

import expo.modules.t3nativecontrols.T3WindowLifecycle.Step
import org.junit.Assert.assertEquals
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
    assertEquals(Step.Forward, lifecycle.resumed("b"))
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
}
