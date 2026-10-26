import { DEFAULT_RESOLVED_KEYBINDINGS } from "@t3tools/shared/keybindings";
import { expect, it } from "vite-plus/test";
import { userEvent } from "vite-plus/test/browser";

import { render } from "../../test/render";
import type { ChatComposerHandle } from "./chat/ChatComposer";
import { useChatShortcuts } from "./chat/useChatShortcuts";
import { RightPanelTabs } from "./RightPanelTabs";

const shortcutContext = {
  terminalFocus: false,
  terminalOpen: false,
  previewFocus: false,
  previewOpen: false,
  isWeb: true,
  isDesktop: false,
  modelPickerOpen: false,
};

const noop = () => undefined;

// The chat's type-to-focus beside the empty right panel. `open: false` with the panel still
// mounted is the stretch a closing panel spends in its exit animation.
function Chat(props: { open: boolean; composerKeys: string[]; openedFiles: string[] }) {
  useChatShortcuts({
    enabled: true,
    keybindings: [],
    scriptKeybindings: [],
    getShortcutContext: () => shortcutContext,
    threadFindActive: false,
    // Type-to-focus only calls insertTextAtEnd, so the stand-in composer implements just that.
    composerRef: {
      current: {
        insertTextAtEnd: (key: string) => {
          props.composerKeys.push(key);
          return true;
        },
      } as Partial<ChatComposerHandle> as ChatComposerHandle,
    },
    branchToolbarRef: { current: null },
    closeThreadFind: noop,
    commands: {},
    fallback: () => undefined,
  });
  return (
    <RightPanelTabs
      mode="inline"
      open={props.open}
      keybindings={DEFAULT_RESOLVED_KEYBINDINGS}
      getShortcutContext={() => shortcutContext}
      surfaces={[]}
      environmentId={null}
      activeSurfaceId={null}
      pendingSurfaceIds={new Set()}
      previewSessions={{}}
      desktopByTabId={{}}
      terminalLabelsById={new Map()}
      onActivate={noop}
      onCloseSurface={noop}
      onCloseOtherSurfaces={noop}
      onCloseSurfacesToRight={noop}
      onCloseAllSurfaces={noop}
      onCopyFilePath={noop}
      onAddBrowser={noop}
      onAddBrowserInProfile={noop}
      onAddTerminal={noop}
      onAddDiff={noop}
      onAddFiles={() => props.openedFiles.push("files")}
      onAddPullRequest={noop}
      onAddPullRequests={noop}
      onAddDevice={noop}
      browserAvailable={false}
      terminalAvailable={false}
      diffAvailable={false}
      filesAvailable
      pullRequestAvailable={false}
      pullRequestsAvailable={false}
      deviceAvailable={false}
    >
      content
    </RightPanelTabs>
  );
}

it("hands launcher letters back to the composer once the panel starts closing", async () => {
  const composerKeys: string[] = [];
  const openedFiles: string[] = [];
  const chat = (open: boolean) => (
    <Chat open={open} composerKeys={composerKeys} openedFiles={openedFiles} />
  );
  // router: false because neither the panel nor the chat shortcuts navigate here.
  await using screen = await render(chat(true), { router: false });

  await userEvent.keyboard("f");
  expect(openedFiles).toEqual(["files"]);

  await screen.rerender(chat(false));
  await userEvent.keyboard("f");
  expect(openedFiles).toEqual(["files"]);
  expect(composerKeys).toEqual(["f"]);

  await screen.rerender(chat(true));
  await userEvent.keyboard("f");
  expect(openedFiles).toEqual(["files", "files"]);
  expect(composerKeys).toEqual(["f"]);
});
