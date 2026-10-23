import { describe, expect, it, vi } from "vite-plus/test";
import { page, userEvent } from "vite-plus/test/browser";

import { render } from "../../../test/render";
import { SidebarProvider } from "../ui/sidebar";
import { SettingsSidebarNav } from "./SettingsSidebarNav";

// Chromium marks keys inside a composition with isComposing; Safari sends the key that
// commits it after compositionend, with only keyCode 229.
describe.each([
  { name: "isComposing", init: { isComposing: true } },
  { name: "keyCode 229", init: { keyCode: 229 } },
])("settings search during IME composition ($name)", ({ init }) => {
  it("leaves composing keys to the IME", async () => {
    await using screen = await render(
      <SidebarProvider>
        <SettingsSidebarNav pathname="/settings/general" />
      </SidebarProvider>,
      { router: "/settings/general" },
    );
    const search = page.getByRole("combobox", { name: "Search settings" });
    await userEvent.type(search, "theme");
    const firstResult = page.getByRole("option").first();
    await expect.element(firstResult).toHaveAttribute("aria-selected", "true");

    for (const key of ["ArrowDown", "Escape", "Enter"]) {
      search
        .element()
        .dispatchEvent(
          new KeyboardEvent("keydown", { key, bubbles: true, cancelable: true, ...init }),
        );
    }

    await expect.element(search).toHaveValue("theme");
    await expect.element(firstResult).toHaveAttribute("aria-selected", "true");
    expect(screen.router?.state.location.pathname).toBe("/settings/general");

    await userEvent.keyboard("{Enter}");

    await expect.element(search).toHaveValue("");
    await vi.waitFor(() =>
      expect(screen.router?.state.location.pathname).toBe("/settings/appearance"),
    );
  });
});
