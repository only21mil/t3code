import {
  PreviewReportStatusInput,
  type DesktopPreviewTabState,
  type ScopedThreadRef,
  type ThreadId,
} from "@t3tools/contracts";
import * as Option from "effect/Option";
import * as Schema from "effect/Schema";
import { useEffect, useEffectEvent, useRef } from "react";

import {
  flushPendingFaviconsForThread,
  recordFaviconForThread,
  useFaviconProjectRefForThread,
} from "~/browserFaviconStore";
import { useBrowserPointerStore } from "~/browser/browserPointerStore";
import { applyPreviewDesktopState, type DesktopPreviewOverlay } from "~/previewStateStore";
import { previewEnvironment } from "~/state/preview";
import { usePreparedConnection } from "~/state/session";
import { useAtomCommand } from "~/state/use-atom-command";

import { previewBridge } from "./previewBridge";

function originOf(url: string): string | null {
  try {
    return new URL(url).origin;
  } catch {
    return null;
  }
}

/**
 * Webview lifetime is owned by ElectronBrowserHost.
 */
export function usePreviewBridge(input: {
  threadRef: ScopedThreadRef;
  tabId: string;
  runtimeTabId: string;
  serverDriven?: boolean;
}): void {
  const { threadRef, tabId, runtimeTabId, serverDriven = false } = input;
  const clearBrowserPointer = useBrowserPointerStore((state) => state.clear);
  const reportStatus = useAtomCommand(previewEnvironment.reportStatus, "preview status report");
  // Callers pass a fresh threadRef each render; rebuilding it from its ids keeps the ref
  // stable for the effects.
  const { environmentId, threadId } = threadRef;
  const stableThreadRef: ScopedThreadRef = { environmentId, threadId };
  const projectRef = useFaviconProjectRefForThread(stableThreadRef);
  const preparedConnection = usePreparedConnection(stableThreadRef.environmentId);
  const environmentHostname = Option.isSome(preparedConnection)
    ? new URL(preparedConnection.value.httpBaseUrl).hostname
    : undefined;

  const lastReported = useRef<PreviewReportStatusInput | null>(null);
  const lastDesktopNavStatus = useRef<DesktopPreviewTabState["navStatus"] | null>(null);
  const handleStateChange = useEffectEvent(
    (changedTabId: string, state: DesktopPreviewTabState): void => {
      if (changedTabId !== runtimeTabId) return;
      if (shouldClearBrowserPointer(lastDesktopNavStatus.current, state.navStatus)) {
        clearBrowserPointer(runtimeTabId);
      }
      lastDesktopNavStatus.current = state.navStatus;
      applyPreviewDesktopState(stableThreadRef, tabId, projectDesktopState(state));
      if (state.favicon) {
        recordFaviconForThread(stableThreadRef, state.favicon, projectRef, environmentHostname);
      }
      const reported = buildReportInput({
        threadId: stableThreadRef.threadId,
        tabId,
        state,
        lastReported: lastReported.current,
      });
      if (!reported || serverDriven) return;
      lastReported.current = reported;
      void reportStatus({
        environmentId: stableThreadRef.environmentId,
        input: reported,
      });
    },
  );
  useEffect(() => {
    if (!previewBridge || typeof window === "undefined") return;
    lastReported.current = null;
    lastDesktopNavStatus.current = null;
    return previewBridge.onStateChange(handleStateChange);
  }, [
    // oxlint-disable-next-line react/exhaustive-effect-dependencies -- A different tab or thread starts its status reports and pointer tracking from scratch.
    runtimeTabId,
    stableThreadRef,
    tabId,
  ]);
  useEffect(() => {
    if (!projectRef) return;
    flushPendingFaviconsForThread(stableThreadRef, projectRef, environmentHostname);
  }, [environmentHostname, projectRef, stableThreadRef]);
}

function shouldClearBrowserPointer(
  previous: DesktopPreviewTabState["navStatus"] | null,
  current: DesktopPreviewTabState["navStatus"],
): boolean {
  if (!previous) return false;
  if (current.kind === "Loading" && previous.kind !== "Loading") return true;
  if (current.kind === "Idle" || previous.kind === "Idle") return false;
  return current.url !== previous.url;
}

export function projectDesktopState(state: DesktopPreviewTabState): DesktopPreviewOverlay {
  const navOrigin = state.navStatus.kind === "Idle" ? null : originOf(state.navStatus.url);
  return {
    hasWebContents: state.webContentsId !== null,
    canGoBack: state.canGoBack,
    canGoForward: state.canGoForward,
    loading: state.navStatus.kind === "Loading",
    zoomFactor: state.zoomFactor,
    pictureInPicture: state.pictureInPicture,
    colorScheme: state.colorScheme,
    audioMuted: state.audioMuted,
    audible: state.audible,
    controller: state.controller,
    favicon: state.favicon && originOf(state.favicon.pageUrl) === navOrigin ? state.favicon : null,
  };
}

const sameReport = Schema.toEquivalence(PreviewReportStatusInput);

export function buildReportInput(args: {
  readonly threadId: ThreadId;
  readonly tabId: string;
  readonly state: DesktopPreviewTabState;
  readonly lastReported: PreviewReportStatusInput | null;
}): PreviewReportStatusInput | null {
  const { threadId, tabId, state, lastReported } = args;
  const status = state.navStatus;
  if (status.kind === "Idle") return null;

  const base = {
    threadId,
    tabId,
    canGoBack: state.canGoBack,
    canGoForward: state.canGoForward,
  };
  if (status.kind === "LoadFailed") {
    return {
      ...base,
      navStatus: {
        _tag: "LoadFailed",
        url: status.url,
        title: status.title,
        code: status.code,
        description: status.description,
      },
    };
  }
  const input: PreviewReportStatusInput = {
    ...base,
    navStatus: { _tag: status.kind, url: status.url, title: status.title },
  };
  return lastReported && sameReport(input, lastReported) ? null : input;
}
