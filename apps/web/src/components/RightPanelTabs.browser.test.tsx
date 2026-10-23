import { compileResolvedKeybindingsConfig } from "@t3tools/shared/keybindings";
import { useState } from "react";
import { describe, expect, it } from "vite-plus/test";
import { userEvent } from "vite-plus/test/browser";

import type { RightPanelSurface } from "~/rightPanelStore";
import { act, render, type Screen } from "../../test/render";
import { RightPanelTabs } from "./RightPanelTabs";

const keybindings = compileResolvedKeybindingsConfig([]);
const noop = () => undefined;

function DeviceTabs() {
  const [surfaces, setSurfaces] = useState<readonly RightPanelSurface[]>([
    { id: "device", kind: "device", title: "Pixel" },
  ]);
  return (
    <RightPanelTabs
      mode="embedded"
      keybindings={keybindings}
      getShortcutContext={() => ({})}
      surfaces={surfaces}
      environmentId={null}
      activeSurfaceId="device"
      pendingSurfaceIds={new Set()}
      previewSessions={{}}
      desktopByTabId={{}}
      terminalLabelsById={new Map()}
      onActivate={noop}
      onRenameDevice={(surfaceId, title) =>
        setSurfaces((current) =>
          current.map((surface) => (surface.id === surfaceId ? { ...surface, title } : surface)),
        )
      }
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
      browserAvailable={false}
      terminalAvailable={false}
      diffAvailable={false}
      filesAvailable={false}
      pullRequestAvailable={false}
      pullRequestsAvailable={false}
      deviceAvailable={false}
    >
      {null}
    </RightPanelTabs>
  );
}

const nameInput = (screen: Screen) =>
  screen.getByRole("textbox", { name: "Device tab name" }).element() as HTMLInputElement;

describe("device tab rename composition", () => {
  it.each([
    { key: "Enter", isComposing: true, keyCode: 13 },
    { key: "Enter", isComposing: false, keyCode: 229 },
    { key: "Escape", isComposing: true, keyCode: 27 },
  ])("keeps editing through a composing $key ($keyCode)", async (composition) => {
    await using screen = await render(<DeviceTabs />);
    await userEvent.dblClick(screen.getByRole("button", { name: "Pixel", exact: true }));
    const input = nameInput(screen);
    await userEvent.fill(input, "日本");

    await act(() => {
      input.dispatchEvent(new KeyboardEvent("keydown", { bubbles: true, ...composition }));
    });
    expect(document.activeElement).toBe(input);

    await userEvent.type(input, "語");
    await userEvent.keyboard("{Enter}");
    await expect.element(screen.getByRole("button", { name: "日本語", exact: true })).toBeVisible();
  });
});
