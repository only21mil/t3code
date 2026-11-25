import * as NodeModule from "node:module";
import * as NodePath from "node:path";
import { act, use, type RefObject } from "react";
import { createRoot, type Root } from "react-dom/client";
import { afterEach, expect, it, vi } from "vite-plus/test";

// React Native's BackHandler: one app-wide list, newest listener first, until one returns true.
const backHandler = vi.hoisted(() => {
  const listeners: Array<() => boolean> = [];
  return {
    addEventListener(_event: "hardwareBackPress", listener: () => boolean) {
      listeners.unshift(listener);
      return { remove: () => void listeners.splice(listeners.indexOf(listener), 1) };
    },
    press: () => listeners.some((listener) => listener()),
  };
});
vi.mock("react-native", () => ({ BackHandler: backHandler }));
vi.mock("@react-navigation/native", () => ({ useIsFocused: () => true }));

import { activateAppWindow, AppWindowContext, closeAppWindow } from "./appWindows";
import { addWindowBackListener, isBackForWindow, useHardwareBack } from "./backHandler";

// The patched container hook (patches/@react-navigation__native@7.5.1.patch).
const navigationRoot = NodePath.dirname(
  NodeModule.createRequire(import.meta.url).resolve("@react-navigation/native/package.json"),
);
const { useBackButton } = (await import(
  NodePath.join(navigationRoot, "lib/module/useBackButton.native.js")
)) as {
  useBackButton(
    ref: RefObject<{ canGoBack(): boolean; goBack(): void } | null>,
    shouldHandleBackButton?: () => boolean,
  ): void;
};

const roots: Root[] = [];

afterEach(() => {
  for (const root of roots.splice(0)) act(() => root.unmount());
  closeAppWindow(1);
  closeAppWindow(2);
});

function fakeContainer() {
  return { canGoBack: () => true, goBack: vi.fn<() => void>() };
}

// One window's root: its navigation container and a screen with a hardware Back handler.
function WindowRoot(props: {
  readonly container: ReturnType<typeof fakeContainer>;
  readonly onScreenBack: () => boolean;
}) {
  const ref = { current: props.container };
  return (
    <>
      <ContainerBack containerRef={ref} />
      <ScreenBack onBack={props.onScreenBack} />
    </>
  );
}

function ContainerBack(props: {
  readonly containerRef: RefObject<ReturnType<typeof fakeContainer>>;
}) {
  const windowId = use(AppWindowContext);
  useBackButton(props.containerRef, () => isBackForWindow(windowId));
  return null;
}

function ScreenBack(props: { readonly onBack: () => boolean }) {
  useHardwareBack(true, props.onBack);
  return null;
}

function mountWindow(windowId: number, onScreenBack: () => boolean = () => false) {
  const container = fakeContainer();
  const root = createRoot(document.createElement("div"));
  roots.push(root);
  act(() =>
    root.render(
      <AppWindowContext value={windowId}>
        <WindowRoot container={container} onScreenBack={onScreenBack} />
      </AppWindowContext>,
    ),
  );
  activateAppWindow(windowId);
  return container;
}

it("pops only the stack of the window Back was pressed in", () => {
  vi.stubGlobal("IS_REACT_ACT_ENVIRONMENT", true);
  const first = mountWindow(1);
  // The newer window's listeners run first.
  const second = mountWindow(2);

  activateAppWindow(1);
  expect(backHandler.press()).toBe(true);
  expect(first.goBack).toHaveBeenCalledTimes(1);
  expect(second.goBack).not.toHaveBeenCalled();

  activateAppWindow(2);
  expect(backHandler.press()).toBe(true);
  expect(first.goBack).toHaveBeenCalledTimes(1);
  expect(second.goBack).toHaveBeenCalledTimes(1);
});

it("gives a screen's Back handler only presses in its own window", () => {
  vi.stubGlobal("IS_REACT_ACT_ENVIRONMENT", true);
  const firstScreen = vi.fn(() => true);
  const secondScreen = vi.fn(() => true);
  const first = mountWindow(1, firstScreen);
  mountWindow(2, secondScreen);

  activateAppWindow(1);
  backHandler.press();
  expect(firstScreen).toHaveBeenCalledTimes(1);
  expect(secondScreen).not.toHaveBeenCalled();
  expect(first.goBack).not.toHaveBeenCalled();
});

it("leaves presses in another window to that window's listeners", () => {
  const listener = vi.fn(() => true);
  const subscription = addWindowBackListener(1, listener);
  activateAppWindow(1);
  activateAppWindow(2);

  expect(backHandler.press()).toBe(false);
  expect(listener).not.toHaveBeenCalled();
  subscription.remove();
});
