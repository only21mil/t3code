import { expect, it, vi } from "vite-plus/test";

const harness = vi.hoisted(() => {
  let onRead: (() => void) | null = null;
  return {
    urlListeners: [] as Array<(event: { readonly url: string }) => void>,
    readPayloads: vi.fn(() => {
      onRead?.();
      return [];
    }),
    /** Resolves when the inbox next reads the native share handoff. */
    nextRead: () =>
      new Promise<void>((resolve) => {
        onRead = resolve;
      }),
  };
});

vi.mock("react-native", () => ({
  Platform: { OS: "android" },
  Linking: {
    addEventListener: (_type: "url", listener: (event: { readonly url: string }) => void) => {
      harness.urlListeners.push(listener);
      return {
        remove: () => harness.urlListeners.splice(harness.urlListeners.indexOf(listener), 1),
      };
    },
  },
}));
vi.mock("expo-sharing", () => ({
  getSharedPayloads: harness.readPayloads,
  getResolvedSharedPayloadsAsync: async () => [],
  clearSharedPayloads: () => {},
}));
vi.mock("expo-constants", () => ({ default: { expoConfig: null } }));
vi.mock("expo-crypto", () => ({}));
// Side by side, the other window stays resumed: the app never returns to the foreground.
vi.mock("../../lib/appState", () => ({ subscribeAppActive: () => () => {} }));
vi.mock("./incoming-share-storage", () => ({
  loadIncomingShareDrafts: async () => [],
  writeIncomingShareDraft: async () => {},
  removeIncomingShareDraft: async () => {},
}));
vi.mock("../../components/ui/Dialog", () => ({ alert: () => {} }));
vi.mock("../../lib/rootNavigation", () => ({ rootNavigationRef: { isReady: () => false } }));
vi.mock("../../lib/composerImages", () => ({ persistComposerAttachmentFile: async () => "" }));
vi.mock("../threads/incomingShareImport", () => ({ makeIncomingShareImports: () => ({}) }));
vi.mock("../../state/use-composer-drafts", () => ({
  getComposerDraftSnapshot: () => null,
  mergeComposerDraftContent: () => {},
  scheduleUnusedComposerAttachmentCleanup: () => {},
  undoComposerDraftMerge: () => {},
}));
vi.mock("../../state/server", () => ({ serverEnvironment: {} }));
vi.mock("@react-navigation/native", () => ({ CommonActions: {} }));
vi.mock("../layout/workspace/workspace-detail-selection", () => ({
  selectWorkspaceDetail: () => ({}),
}));

const { startIncomingShareInbox } = await import("./IncomingShareProvider");

it("ingests a share handed to one Android window while another stays resumed", async () => {
  const loaded = harness.nextRead();
  const stop = startIncomingShareInbox();
  await loaded;

  // expo-sharing hands the share to the receiving window as a link.
  expect(harness.urlListeners).toHaveLength(1);
  const ingested = harness.nextRead();
  for (const listener of harness.urlListeners) listener({ url: "t3code://expo-sharing" });
  await ingested;
  expect(harness.readPayloads).toHaveBeenCalledTimes(2);

  // Other links are not share handoffs.
  for (const listener of harness.urlListeners) listener({ url: "t3code://threads/env/thread" });
  expect(harness.readPayloads).toHaveBeenCalledTimes(2);
  stop();
  expect(harness.urlListeners).toHaveLength(0);
});
