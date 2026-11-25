import { useIsFocused } from "@react-navigation/native";
import { useEffect, useEffectEvent } from "react";
import { BackHandler } from "react-native";

import { usePaneRole } from "../components/ui/Pane";
import { activeAppWindowId, useAppWindowId, type AppWindowId } from "./appWindows";

/**
 * Whether a Back press belongs to this window. BackHandler is app-wide, so every window's
 * listeners share one list; native code makes the window Back was pressed in the active one
 * before the press reaches JS (NativeWindowObserver.android).
 */
export function isBackForWindow(windowId: AppWindowId): boolean {
  const active = activeAppWindowId();
  return active === null || active === windowId;
}

/** A hardware Back listener that acts only on presses in its own window. */
export function addWindowBackListener(windowId: AppWindowId, onBack: () => boolean) {
  return BackHandler.addEventListener(
    "hardwareBackPress",
    () => isBackForWindow(windowId) && onBack(),
  );
}

/**
 * Android hardware back while `active` and the owning screen is focused.
 * Keyed on those alone, not `onBack`: BackHandler calls the newest listener
 * first, so re-registering per render lets a covered screen consume Back.
 */
export function useHardwareBack(active: boolean, onBack: () => boolean) {
  const windowId = useAppWindowId();
  // The sidebar's route stays unfocused under the page beside it.
  const inSidebar = usePaneRole() === "sidebar";
  const focused = useIsFocused() || inSidebar;
  const handleBack = useEffectEvent(onBack);
  // oxlint-disable-next-line t3code/no-unreasoned-state-sync -- subscribes to BackHandler for the focused screen's lifetime
  useEffect(() => {
    if (!active || !focused) return;
    const subscription = addWindowBackListener(windowId, () => handleBack());
    return () => subscription.remove();
  }, [active, focused, windowId]);
}
