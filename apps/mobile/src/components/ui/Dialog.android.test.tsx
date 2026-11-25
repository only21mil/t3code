import { act, type ReactNode } from "react";
import { createRoot, type Root } from "react-dom/client";
import { afterEach, expect, it, vi } from "vite-plus/test";

// Every click handler a button was rendered with, so a test can deliver a
// native event that was dispatched against an older render.
const renderedClicks = vi.hoisted(() => [] as Array<() => void>);

vi.mock("@expo/ui/jetpack-compose", () => {
  const Slot = (props: { readonly children?: ReactNode }) => <div>{props.children}</div>;
  const Button = (props: { readonly children?: ReactNode; readonly onClick?: () => void }) => {
    if (props.onClick) renderedClicks.push(props.onClick);
    return <button onClick={props.onClick}>{props.children}</button>;
  };
  return {
    AlertDialog: Object.assign(Slot, {
      Title: Slot,
      Text: Slot,
      DismissButton: Slot,
      ConfirmButton: Slot,
    }),
    Button,
    OutlinedButton: Button,
    Column: Slot,
    FlowRow: Slot,
    Icon: () => null,
    OutlinedTextField: Object.assign(Slot, { Label: Slot, Placeholder: Slot }),
    Text: Slot,
    useNativeState: (value: unknown) => ({ get: () => value }),
  };
});
vi.mock("./NativeThemeHost.android", () => ({
  NativeThemeHost: (props: { readonly children?: ReactNode }) => <div>{props.children}</div>,
}));
vi.mock("../../features/settings/appearance/AppearancePreferencesProvider", () => ({
  useAppearancePreferences: () => ({ themeVariables: {} }),
}));
vi.mock("../../features/settings/appearance/useScaledTextRole", () => ({
  useScaledTextRole: () => ({}),
}));
vi.mock("../../lib/mobileTheme", () => ({ themeColorWithContrast: () => "#ffffff" }));

import { activateAppWindow, AppWindowContext, closeAppWindow } from "../../lib/appWindows";
import * as Dialog from "./Dialog.android";

const roots: Root[] = [];

// A window's root: Hosts mounted without a window share the default id.
function mountHost(windowId = 0) {
  vi.stubGlobal("IS_REACT_ACT_ENVIRONMENT", true);
  const container = document.createElement("div");
  document.body.append(container);
  const root = createRoot(container);
  roots.push(root);
  act(() =>
    root.render(
      <AppWindowContext value={windowId}>
        <Dialog.Host />
      </AppWindowContext>,
    ),
  );
  return { root, container };
}

afterEach(() => {
  for (const root of roots.splice(0)) act(() => root.unmount());
  for (const windowId of [1, 2]) act(() => closeAppWindow(windowId));
  renderedClicks.length = 0;
  document.body.innerHTML = "";
});

it("keeps presenting dialogs after an older root's Host unmounts", () => {
  // Android activity replacement mounts the new root before the old one stops.
  const previous = mountHost();
  const current = mountHost();
  roots.splice(roots.indexOf(previous.root), 1);
  act(() => previous.root.unmount());

  act(() => Dialog.alert("Saved", undefined, [{ text: "OK" }]));

  expect(current.container.textContent).toContain("Saved");
});

it("presents a dialog requested before any Host mounted", () => {
  Dialog.alert("Could not import shared content", undefined, [{ text: "Dismiss" }]);

  const { container } = mountHost();

  expect(container.textContent).toContain("Could not import shared content");
});

it("keeps a dialog raised while the activity is replaced", () => {
  const previous = mountHost();
  act(() => Dialog.alert("Shared content imported", undefined, [{ text: "OK" }]));
  const current = mountHost();
  roots.splice(roots.indexOf(previous.root), 1);
  act(() => previous.root.unmount());

  expect(current.container.textContent).toContain("Shared content imported");
});

it.each([
  {
    kind: "alert",
    present: (onClose: () => void) =>
      Dialog.alert("Older", undefined, [{ text: "OK" }], { onDismiss: onClose }),
  },
  {
    kind: "confirm",
    present: (onClose: () => void) =>
      Dialog.confirm({
        title: "Remove project",
        confirmText: "Remove",
        onConfirm: () => {},
        onCancel: onClose,
      }),
  },
  {
    kind: "text-input",
    present: (onClose: () => void) =>
      Dialog.prompt({
        title: "Rename",
        initialValue: "",
        confirmText: "Save",
        onConfirm: () => {},
        onCancel: onClose,
      }),
  },
])("tells a replaced $kind it was closed without an answer", ({ present }) => {
  mountHost();
  const onClose = vi.fn();
  act(() => present(onClose));
  act(() => Dialog.alert("Newer", undefined, [{ text: "OK" }]));

  expect(onClose).toHaveBeenCalledOnce();
});

it.each([
  { action: "confirm", clickIndex: -1 },
  { action: "cancel", clickIndex: -2 },
])("ignores a late $action click from a replaced confirmation", ({ clickIndex }) => {
  const { container } = mountHost();
  const onConfirm = vi.fn();
  const onCancel = vi.fn();
  act(() =>
    Dialog.confirm({ title: "Remove project", confirmText: "Remove", onConfirm, onCancel }),
  );
  const lateClick = renderedClicks.at(clickIndex)!;
  act(() => Dialog.alert("Newer", undefined, [{ text: "OK" }]));

  act(() => lateClick());

  expect(onConfirm).not.toHaveBeenCalled();
  expect(onCancel).toHaveBeenCalledOnce();
  expect(container.textContent).toContain("Newer");
});

it("ignores a late action from a dialog that a newer one replaced", () => {
  const { container } = mountHost();
  const olderAction = vi.fn();
  act(() => Dialog.alert("Older", undefined, [{ text: "OK", onPress: olderAction }]));
  const olderClick = renderedClicks.at(-1)!;
  act(() => Dialog.alert("Newer", undefined, [{ text: "OK" }]));

  act(() => olderClick());

  expect(olderAction).toHaveBeenCalledOnce();
  expect(container.textContent).toContain("Newer");
});

it("presents a dialog only in the window it was raised in", () => {
  const left = mountHost(1);
  const right = mountHost(2);
  act(() => activateAppWindow(2));
  act(() => activateAppWindow(1));

  act(() => Dialog.confirm({ title: "Delete thread", confirmText: "Delete", onConfirm: () => {} }));
  // The other window coming into use leaves the dialog where it was raised.
  act(() => activateAppWindow(2));

  expect(left.container.textContent).toContain("Delete thread");
  expect(right.container.textContent).not.toContain("Delete thread");
});

it("replaces a dialog raised in one window with one raised in the other", () => {
  const left = mountHost(1);
  const right = mountHost(2);
  act(() => activateAppWindow(1));
  const onCancel = vi.fn();
  act(() =>
    Dialog.confirm({
      title: "Delete thread",
      confirmText: "Delete",
      onConfirm: () => {},
      onCancel,
    }),
  );

  act(() => activateAppWindow(2));
  act(() => Dialog.alert("Copied", undefined, [{ text: "OK" }]));

  expect(onCancel).toHaveBeenCalledOnce();
  expect(left.container.textContent).toBe("");
  expect(right.container.textContent).toContain("Copied");
});

it("moves a dialog to the window in use once its own window closes", () => {
  const replaced = mountHost(1);
  act(() => activateAppWindow(1));
  act(() => Dialog.alert("Shared content imported", undefined, [{ text: "OK" }]));
  const replacement = mountHost(2);
  act(() => activateAppWindow(2));
  expect(replacement.container.textContent).toBe("");

  roots.splice(roots.indexOf(replaced.root), 1);
  act(() => replaced.root.unmount());
  act(() => closeAppWindow(1));

  expect(replacement.container.textContent).toContain("Shared content imported");
});
