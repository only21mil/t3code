import { act, type ReactNode } from "react";
import { createRoot, type Root } from "react-dom/client";
import { afterEach, expect, it, vi } from "vite-plus/test";

vi.mock("react-native", () => ({
  View: (props: { readonly children?: ReactNode }) => <div>{props.children}</div>,
}));

import { AppWindowContext } from "../../lib/appWindows";
import { OverlayPortal, OverlayPortalHost } from "./OverlayPortal";

const roots: Root[] = [];

afterEach(() => {
  for (const root of roots.splice(0)) act(() => root.unmount());
  document.body.innerHTML = "";
});

// One window's root, as App renders it: its screens, then its overlay host.
function mountWindow(windowId: number, children?: ReactNode) {
  vi.stubGlobal("IS_REACT_ACT_ENVIRONMENT", true);
  const container = document.createElement("div");
  document.body.append(container);
  const root = createRoot(container);
  roots.push(root);
  const render = (next?: ReactNode) =>
    act(() =>
      root.render(
        <AppWindowContext value={windowId}>
          {next}
          <OverlayPortalHost />
        </AppWindowContext>,
      ),
    );
  render(children);
  return { container, render };
}

it("shows a menu only in the window that opened it", () => {
  const left = mountWindow(1, <OverlayPortal>Thread menu</OverlayPortal>);
  const right = mountWindow(2);

  expect(left.container.textContent).toBe("Thread menu");
  expect(right.container.textContent).toBe("");
});

it("keeps each window's menus while the other window opens and closes its own", () => {
  const left = mountWindow(1, <OverlayPortal>Thread menu</OverlayPortal>);
  const right = mountWindow(2, <OverlayPortal>Snooze</OverlayPortal>);

  right.render();

  expect(left.container.textContent).toBe("Thread menu");
  expect(right.container.textContent).toBe("");
});
