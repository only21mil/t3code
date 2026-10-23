import type { ComponentProps } from "react";
import { expect, it, vi } from "vite-plus/test";
import { userEvent } from "vite-plus/test/browser";
import { DEFAULT_RESOLVED_KEYBINDINGS } from "@t3tools/shared/keybindings";

import { render } from "../../test/render";
import { RightPanelTabs } from "./RightPanelTabs";

vi.mock("~/browser/browserDefaults", () => ({ useBrowserDefaults: () => ({ profiles: [] }) }));

const noop = () => undefined;
const browserTab = { id: "browser:tab-1", kind: "preview", resourceId: "tab-1" } as const;

function Panel(props: Partial<ComponentProps<typeof RightPanelTabs>>) {
  return (
    <RightPanelTabs
      mode="inline"
      open
      keybindings={DEFAULT_RESOLVED_KEYBINDINGS}
      getShortcutContext={() => ({
        terminalFocus: false,
        terminalOpen: false,
        previewFocus: false,
        previewOpen: true,
        isWeb: true,
        isDesktop: false,
      })}
      surfaces={[browserTab]}
      environmentId={null}
      activeSurfaceId={browserTab.id}
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
      onAddFiles={noop}
      onAddPullRequest={noop}
      onAddPullRequests={noop}
      onAddDevice={noop}
      browserAvailable
      terminalAvailable
      diffAvailable
      filesAvailable
      pullRequestAvailable={false}
      pullRequestsAvailable={false}
      deviceAvailable={false}
      {...props}
    >
      browser
    </RightPanelTabs>
  );
}

// An agent closing the last browser tab leaves the panel open on the launcher, as
// rightPanelStore's browser reconciliation does. The person never touched the panel.
const lastBrowserTabGone = { surfaces: [], activeSurfaceId: null } as const;

// router: false because nothing here navigates.
const options = { router: false } as const;

it("keeps typing at the caret when the last browser tab closes under it", async () => {
  await using screen = await render(
    <>
      <textarea aria-label="Composer" defaultValue="Rename greet" />
      <Panel />
    </>,
    options,
  );
  const composer = screen.getByRole("textbox", { name: "Composer" });
  await userEvent.click(composer);
  const editor = composer.element() as HTMLTextAreaElement;
  editor.setSelectionRange("Rename ".length, "Rename ".length);

  await screen.rerender(
    <>
      <textarea aria-label="Composer" defaultValue="Rename greet" />
      <Panel {...lastBrowserTabGone} />
    </>,
  );
  await expect.element(screen.getByLabelText("Open a surface")).toBeInTheDocument();
  await userEvent.keyboard("the ");

  await expect.element(composer).toHaveFocus();
  await expect.element(composer).toHaveValue("Rename the greet");
});

it("still focuses the launcher when nothing is being typed", async () => {
  await using screen = await render(<Panel />, options);

  await screen.rerender(<Panel {...lastBrowserTabGone} />);

  await expect.element(screen.getByLabelText("Open a surface")).toHaveFocus();
});
