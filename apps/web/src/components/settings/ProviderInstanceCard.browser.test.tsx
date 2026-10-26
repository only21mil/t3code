import { describe, expect, it, vi } from "vite-plus/test";
import { userEvent } from "vite-plus/test/browser";

import { render, type Screen } from "../../../test/render";
import { ProviderEnvironmentSection } from "./ProviderInstanceCard";

async function commit(screen: Screen, label: string, value: string) {
  const input = screen.getByRole("textbox", { name: label, exact: true });
  await userEvent.clear(input);
  await userEvent.type(input, `${value}{Enter}`);
}

describe("ProviderEnvironmentSection", () => {
  it("explains an invalid name and saves held edits once it is fixed", async () => {
    const onChange = vi.fn();
    await using screen = await render(
      <ProviderEnvironmentSection
        environment={[{ name: "SAVED", value: "one", sensitive: false }]}
        onChange={onChange}
      />,
    );

    await userEvent.click(screen.getByRole("button", { name: "Add variable" }));
    await commit(screen, "Environment variable name 2", "2BAD");
    const name = screen.getByRole("textbox", { name: "Environment variable name 2", exact: true });
    await expect.element(name).toHaveAttribute("aria-invalid", "true");
    await expect
      .element(name)
      .toHaveAccessibleDescription(
        "Use only letters, numbers, and underscores, not starting with a number. Variables won't save until this is fixed.",
      );

    await commit(screen, "Environment variable value 1", "two");
    expect(onChange).not.toHaveBeenCalled();
    await expect
      .element(screen.getByRole("textbox", { name: "Environment variable value 1", exact: true }))
      .toHaveValue("two");

    await commit(screen, "Environment variable name 2", "GOOD");
    await expect.element(name).not.toHaveAttribute("aria-invalid");
    expect(onChange).toHaveBeenLastCalledWith([
      { name: "SAVED", value: "two", sensitive: false, valueRedacted: false },
      { name: "GOOD", value: "", sensitive: true },
    ]);
  });
});
