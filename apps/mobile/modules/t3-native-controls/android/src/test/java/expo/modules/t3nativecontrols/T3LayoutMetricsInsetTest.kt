package expo.modules.t3nativecontrols

import org.junit.Assert.assertEquals
import org.junit.Test

class T3LayoutMetricsInsetTest {
  @Test
  fun coversAViewOnlyWhereTheInsetReachesIt() {
    assertEquals(63, insetOverlap(inset = 63, offset = 0))
    assertEquals(13, insetOverlap(inset = 63, offset = 50))
    assertEquals(0, insetOverlap(inset = 63, offset = 200))
  }

  // Unfolding: the view already fills the open display while the window still has the cover
  // display's height, so the view overhangs the window's bottom edge by ~1500px.
  @Test
  fun neverCoversAViewOverhangingAStaleWindowByMoreThanTheInset() {
    assertEquals(63, insetOverlap(inset = 63, offset = -1491))
    assertEquals(0, insetOverlap(inset = 0, offset = -336))
  }
}
