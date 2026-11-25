import { type ReactNode, useEffect, useState, useSyncExternalStore } from "react";
import { View } from "react-native";

import { useAppWindowId, type AppWindowId } from "../../lib/appWindows";

// RN Modals move native window focus and close the keyboard. Keep composer menus in-window.
type Entries = ReadonlyMap<number, ReactNode>;

let nextKey = 0;

function allocateKey() {
  return nextKey++;
}
// Each overlay shows in the window whose root rendered it; every window has its own host.
const entries = new Map<number, { readonly windowId: AppWindowId; readonly node: ReactNode }>();
const listeners = new Set<() => void>();
const snapshots = new Map<AppWindowId, Entries>();
const NO_ENTRIES: Entries = new Map();

function emit(windowId: AppWindowId) {
  const next = new Map<number, ReactNode>();
  for (const [key, entry] of entries) {
    if (entry.windowId === windowId) next.set(key, entry.node);
  }
  if (next.size === 0) snapshots.delete(windowId);
  else snapshots.set(windowId, next);
  for (const listener of listeners) {
    listener();
  }
}

function subscribe(listener: () => void) {
  listeners.add(listener);
  return () => {
    listeners.delete(listener);
  };
}

function windowSnapshot(windowId: AppWindowId) {
  return snapshots.get(windowId) ?? NO_ENTRIES;
}

export function OverlayPortal(props: { readonly children: ReactNode }) {
  const [key] = useState(allocateKey);
  const windowId = useAppWindowId();

  // RN has no createPortal, so projecting into the out-of-tree host has to
  // happen after commit. No dependency array: re-project after every render so
  // the host always shows the current content (menus re-render while open —
  // drill-in, theme).
  // oxlint-disable-next-line t3code/no-unreasoned-state-sync -- projects children into the out-of-tree overlay host store after every commit
  useEffect(() => {
    entries.set(key, { windowId, node: props.children });
    emit(windowId);
  });

  // Removal is unmount-only: deleting on every re-projection would move the
  // entry to the end of the map and restack it above overlays opened later.
  // oxlint-disable-next-line t3code/no-unreasoned-state-sync -- removes this entry from the overlay host store on unmount
  useEffect(
    () => () => {
      entries.delete(key);
      emit(windowId);
    },
    [key, windowId],
  );

  return null;
}

export function OverlayPortalHost() {
  const windowId = useAppWindowId();
  const current = useSyncExternalStore(
    subscribe,
    () => windowSnapshot(windowId),
    () => windowSnapshot(windowId),
  );

  if (current.size === 0) {
    return null;
  }
  return (
    <View pointerEvents="box-none" className="absolute inset-0">
      {[...current.entries()].map(([key, node]) => (
        <View key={key} pointerEvents="box-none" className="absolute inset-0">
          {node}
        </View>
      ))}
    </View>
  );
}
