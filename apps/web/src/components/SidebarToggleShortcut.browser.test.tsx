import { compileResolvedKeybindingsConfig } from "@t3tools/shared/keybindings";
import { describe, expect, it, vi } from "vite-plus/test";
import { page, userEvent } from "vite-plus/test/browser";

import { render } from "../../test/render";
import { primaryServerKeybindingsAtom } from "../state/server";

const keybindings = compileResolvedKeybindingsConfig([
  { key: "mod+b", command: "sidebar.toggle", when: "!terminalFocus" },
]);

vi.mock(import("@effect/atom-react"), async (original) => ({
  ...(await original()),
  useAtomValue: ((atom: unknown) =>
    atom === primaryServerKeybindingsAtom ? keybindings : null) as never,
}));

import { SidebarControl } from "./AppSidebarLayout";
import { SidebarProvider } from "./ui/sidebar";

describe("sidebar toggle shortcut", () => {
  // Ctrl+B is tmux's default prefix, so `!terminalFocus` has to hand it to the shell.
  it("leaves the key to a focused terminal when its rule excludes terminal focus", async () => {
    await page.viewport(1280, 900);
    using _platform = vi.spyOn(navigator, "platform", "get").mockReturnValue("Linux x86_64");
    await using screen = await render(
      <SidebarProvider>
        <SidebarControl />
        <div data-terminal-owner="drawer">
          <textarea aria-label="Terminal input" />
        </div>
      </SidebarProvider>,
    );
    const toggle = screen.getByRole("button", { name: "Toggle main sidebar" });

    await userEvent.keyboard("{Control>}b{/Control}");
    await expect.element(toggle).toHaveAttribute("aria-pressed", "false");

    const terminalKeys: KeyboardEvent[] = [];
    const terminal = screen.getByRole("textbox", { name: "Terminal input" });
    terminal.element().addEventListener("keydown", (event) => {
      if (event.key === "b") terminalKeys.push(event);
    });
    await userEvent.click(terminal);
    await userEvent.keyboard("{Control>}b{/Control}");

    expect(terminalKeys.map((event) => event.defaultPrevented)).toEqual([false]);
    await expect.element(toggle).toHaveAttribute("aria-pressed", "false");
  });
});
