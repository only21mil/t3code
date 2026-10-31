import { expect, it, vi } from "vite-plus/test";
import { page, userEvent } from "vite-plus/test/browser";

import { act, render } from "../../../test/render";
import { SidebarProvider } from "../ui/sidebar";
import { SettingsSidebarNav } from "./SettingsSidebarNav";

vi.mock("./useAvailableSettingsSearchItems", () => ({
  useAvailableSettingsSearchItems: () => [
    { id: "theme", title: "Theme", to: "/settings/appearance" },
  ],
}));

it("keeps composition Enter and Escape in the search from navigating or clearing", async () => {
  await using screen = await render(
    <SidebarProvider defaultOpen>
      <SettingsSidebarNav pathname="/settings/general" />
    </SidebarProvider>,
    { router: "/settings/general" },
  );
  const search = page.getByRole("combobox", { name: "Search settings" });
  await search.fill("theme");
  await expect.element(page.getByRole("option", { name: /Theme/ })).toBeVisible();

  for (const nativeEvent of [
    { isComposing: true, keyCode: 13 },
    { isComposing: false, keyCode: 229 },
  ]) {
    for (const key of ["Enter", "Escape"]) {
      const event = new KeyboardEvent("keydown", {
        key,
        ...nativeEvent,
        bubbles: true,
        cancelable: true,
      });
      await act(() => search.element().dispatchEvent(event));
      expect(event.defaultPrevented).toBe(false);
      expect(screen.router?.state.location.pathname).toBe("/settings/general");
      await expect.element(search).toHaveValue("theme");
    }
  }

  await userEvent.keyboard("{Enter}");
  await vi.waitFor(() =>
    expect(screen.router?.state.location.pathname).toBe("/settings/appearance"),
  );
});
