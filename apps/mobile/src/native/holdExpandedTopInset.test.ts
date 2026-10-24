import { describe, expect, it } from "vite-plus/test";

import { holdExpandedTopInset } from "./holdExpandedTopInset";

describe("holdExpandedTopInset", () => {
  it("keeps the expanded bar's inset while it minimizes, and drops it when the window resizes", () => {
    const unfolded = { width: 669, height: 951 };
    // Top insets the Duo's Home reported while its bar minimized mid-drag.
    const held = [82, 61, 46, 78].reduce(
      (current, top) => holdExpandedTopInset(current, { ...unfolded, top }),
      { ...unfolded, top: 0 },
    );
    expect(held.top).toBe(82);
    expect(holdExpandedTopInset(held, { width: 466, height: 678, top: 54 }).top).toBe(54);
  });
});
