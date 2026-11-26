import { expect, it, vi } from "vite-plus/test";

const harness = vi.hoisted(() => ({
  urlListeners: [] as Array<(event: { readonly url: string }) => void>,
  readPayloads: vi.fn(() => []),
}));

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

const { ingestShareLink, startIncomingShareInbox } = await import("./IncomingShareProvider");

// Another share runs after any refresh already running, so the reads it returns count them all.
async function readsOnceDrained() {
  await ingestShareLink("t3code://expo-sharing");
  return harness.readPayloads.mock.calls.length;
}

it("ingests a share handed to one Android window while another stays resumed", async () => {
  const stop = startIncomingShareInbox();
  const reads = await readsOnceDrained();

  // expo-sharing hands the share to the receiving window as a link.
  expect(harness.urlListeners).toHaveLength(1);
  for (const listener of harness.urlListeners) listener({ url: "t3code://expo-sharing" });
  expect(await readsOnceDrained()).toBe(reads + 2);

  // Other links are not share handoffs.
  for (const listener of harness.urlListeners) listener({ url: "t3code://threads/env/thread" });
  expect(await readsOnceDrained()).toBe(reads + 3);
  stop();
  expect(harness.urlListeners).toHaveLength(0);
});

it("ingests a share that opens a new Android window beside a resumed one", async () => {
  const reads = harness.readPayloads.mock.calls.length;
  // The new window's launch link; no link event or return to the foreground reaches the app.
  await ingestShareLink("t3code://expo-sharing");
  expect(harness.readPayloads).toHaveBeenCalledTimes(reads + 1);
  await ingestShareLink("t3code://threads/env/thread");
  expect(harness.readPayloads).toHaveBeenCalledTimes(reads + 1);
});
