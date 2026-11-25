import { act, use, useEffect, type ReactNode } from "react";
import { createRoot, type Root } from "react-dom/client";
import { afterEach, expect, it, vi } from "vite-plus/test";

import { AppWindowContext } from "../lib/appWindows";
import type { NativeLayoutMetrics } from "../lib/reserved-regions";

// Each Android window's T3LayoutMetrics view measures its own root: side by side, unequal panes.
const paneWidths = new Map([
  [1, 360],
  [2, 680],
]);

function paneMetrics(width: number): NativeLayoutMetrics {
  return {
    width,
    height: 900,
    hasHinge: false,
    horizontalSizeClass: width >= 600 ? "regular" : "compact",
    verticalBarEdge: "none",
    safeArea: { top: 24, bottom: 0, left: 0, right: 0 },
    reservedRegions: [],
  };
}

vi.mock("expo", () => ({
  requireOptionalNativeModule: (name: string) => (name === "T3LayoutMetrics" ? {} : null),
  requireNativeView: () =>
    function FakeLayoutMetricsView(props: {
      readonly onMetricsChange?: (event: { nativeEvent: NativeLayoutMetrics }) => void;
    }) {
      const windowId = use(AppWindowContext);
      const onMetricsChange = props.onMetricsChange;
      useEffect(() => {
        onMetricsChange?.({ nativeEvent: paneMetrics(paneWidths.get(windowId) ?? 0) });
      }, [onMetricsChange, windowId]);
      return null;
    },
}));
vi.mock("react-native", () => ({ Platform: { OS: "android" } }));
vi.mock("./NativeLayoutObserver", () => import("./NativeLayoutObserver.android"));

const { NativeLayoutMetricsProvider, useNativeLayoutMetrics, firstNativeLayoutMetrics } =
  await import("./native-layout-metrics");

const roots: Root[] = [];

afterEach(() => {
  for (const root of roots.splice(0)) act(() => root.unmount());
  document.body.innerHTML = "";
});

function WindowWidth() {
  return <>{useNativeLayoutMetrics()?.width ?? "none"}</>;
}

function mountWindow(windowId: number, children: ReactNode) {
  vi.stubGlobal("IS_REACT_ACT_ENVIRONMENT", true);
  const container = document.createElement("div");
  document.body.append(container);
  const root = createRoot(container);
  roots.push(root);
  act(() =>
    root.render(
      <AppWindowContext value={windowId}>
        <NativeLayoutMetricsProvider>{children}</NativeLayoutMetricsProvider>
      </AppWindowContext>,
    ),
  );
  return container;
}

it("gives each Android window its own width", async () => {
  const left = mountWindow(1, <WindowWidth />);
  const right = mountWindow(2, <WindowWidth />);

  expect(left.textContent).toBe("360");
  expect(right.textContent).toBe("680");
  expect((await firstNativeLayoutMetrics(1, 0))?.width).toBe(360);
  expect((await firstNativeLayoutMetrics(2, 0))?.width).toBe(680);
});
