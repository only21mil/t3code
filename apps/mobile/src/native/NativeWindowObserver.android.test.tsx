import { act } from "react";
import { createRoot, type Root } from "react-dom/client";
import { afterEach, expect, it, vi } from "vite-plus/test";

// React Native's BackHandler and device events: one app-wide list each, as every window shares.
const native = vi.hoisted(() => {
  const backListeners: Array<() => boolean> = [];
  const eventListeners = new Map<string, Array<(payload: number) => void>>();
  return {
    backListeners,
    windowIds: [] as number[],
    runDefaultBack: vi.fn(async (_windowId: number) => {}),
    emit: (event: string, payload: number) => {
      for (const listener of eventListeners.get(event) ?? []) listener(payload);
    },
    addListener: (event: string, listener: (payload: number) => void) => {
      eventListeners.set(event, [...(eventListeners.get(event) ?? []), listener]);
    },
    // Newest listener first, until one takes the press.
    press: () => backListeners.some((listener) => listener()),
  };
});

vi.mock("react-native", () => ({
  BackHandler: {
    addEventListener: (_event: "hardwareBackPress", listener: () => boolean) => {
      native.backListeners.unshift(listener);
      return { remove: () => {} };
    },
  },
  DeviceEventEmitter: { addListener: native.addListener },
}));
vi.mock("expo", () => ({
  requireOptionalNativeModule: (name: string) =>
    name === "T3WindowState" ? { runDefaultBack: native.runDefaultBack } : null,
  requireNativeView: () =>
    function FakeWindowStateView(props: { readonly windowId: number }) {
      native.windowIds.push(props.windowId);
      return null;
    },
}));

import {
  activeAppWindowId,
  AppWindowContext,
  closeAppWindow,
  registerAppWindow,
} from "../lib/appWindows";
import { NativeWindowObserver } from "./NativeWindowObserver.android";

const roots: Root[] = [];

afterEach(() => {
  for (const root of roots.splice(0)) act(() => root.unmount());
  for (const windowId of [1, 2]) closeAppWindow(windowId);
  native.windowIds.length = 0;
  native.runDefaultBack.mockClear();
});

it("runs each declined Back press's default action in the window it came from", () => {
  // Native code names each press's window right before the press.
  native.emit("T3WindowInUse", 1);
  expect(native.press()).toBe(true);
  native.emit("T3WindowInUse", 2);
  expect(native.press()).toBe(true);
  expect(native.runDefaultBack.mock.calls).toEqual([[1], [2]]);

  // Window 1 closes in JS between its press and the default action: native code drops it there.
  native.emit("T3WindowInUse", 1);
  closeAppWindow(1);
  native.press();
  expect(native.runDefaultBack).toHaveBeenLastCalledWith(1);
});

it("registers a new window behind the one in use until native code serves it", () => {
  native.emit("T3WindowInUse", 1);
  registerAppWindow(2);
  expect(activeAppWindowId()).toBe(1);

  native.emit("T3WindowInUse", 2);
  expect(activeAppWindowId()).toBe(2);
});

it("tells native code a window's id only once its navigation hears links", () => {
  vi.stubGlobal("IS_REACT_ACT_ENVIRONMENT", true);
  const root = createRoot(document.createElement("div"));
  roots.push(root);
  const render = (hearsLinks: boolean) =>
    act(() =>
      root.render(
        <AppWindowContext value={2}>
          <NativeWindowObserver hearsLinks={hearsLinks} onChange={() => {}} />
        </AppWindowContext>,
      ),
    );

  // Until then, native code holds a link that reaches this window.
  render(false);
  expect(native.windowIds.at(-1)).toBe(0);
  render(true);
  expect(native.windowIds.at(-1)).toBe(2);
});
