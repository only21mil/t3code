import { spawn } from "node:child_process";
import { once } from "node:events";
import { act, type ReactNode, type Ref } from "react";
import { createRoot } from "react-dom/client";
import { expect, it, vi } from "vite-plus/test";

vi.mock("react-native", async () => {
  const { useImperativeHandle, useRef } = await import("react");
  const Slot = ({ children }: { readonly children?: ReactNode }) => <div>{children}</div>;
  return {
    View: Slot,
    ScrollView: Slot,
    Pressable: Slot,
    TextInput: ({
      ref,
      onSubmitEditing,
    }: {
      readonly ref?: Ref<{ clear(): void }>;
      readonly onSubmitEditing: (event: { nativeEvent: { text: string } }) => void;
    }) => {
      const input = useRef<HTMLInputElement>(null);
      // Model the uncontrolled native input: clear() changes its retained text.
      useImperativeHandle(ref, () => ({
        clear: () => {
          input.current!.value = "";
        },
      }));
      return (
        <input
          ref={input}
          onKeyDown={(event) => {
            if (event.key === "Enter") {
              onSubmitEditing({ nativeEvent: { text: event.currentTarget.value } });
            }
          }}
        />
      );
    },
  };
});
vi.mock("../../components/ui/AppText", () => ({
  AppText: ({ children }: { readonly children?: ReactNode }) => <span>{children}</span>,
}));
vi.mock("../settings/appearance/AppearancePreferencesProvider", () => ({
  useAppearancePreferences: () => ({ themeAppearance: "dark", themeId: "pierre-dark" }),
}));
vi.mock("./nativeTerminalModule", () => ({
  resolveNativeTerminalSurfaceView: () => null,
  getNativeTerminalHardwareKeyRevision: () => 0,
}));

import { TerminalSurface } from "./NativeTerminalSurface";

it("submits consecutive fallback commands without carrying the previous command", async () => {
  vi.stubGlobal("IS_REACT_ACT_ENVIRONMENT", true);
  const container = document.createElement("div");
  const root = createRoot(container);
  const repl = spawn(process.execPath, ["--interactive"], { stdio: ["pipe", "pipe", "pipe"] });
  const closed = once(repl, "close");
  let output = "";
  repl.stdout.setEncoding("utf8").on("data", (chunk: string) => (output += chunk));
  repl.stderr.setEncoding("utf8").on("data", (chunk: string) => (output += chunk));
  try {
    act(() => {
      root.render(
        <TerminalSurface
          terminalKey="fallback-repl"
          buffer=""
          isRunning
          onInput={(data) => repl.stdin.write(data)}
          onResize={() => {}}
        />,
      );
    });
    const input = container.querySelector("input")!;
    for (const command of ["6*7", "2*3"]) {
      input.value += command;
      act(() => {
        input.dispatchEvent(new KeyboardEvent("keydown", { key: "Enter", bubbles: true }));
      });
    }
    repl.stdin.end();
    expect((await closed)[0]).toBe(0);
    // A real REPL consumes the CR-delimited input. Retaining the first command
    // changes the second expression from 2*3 (6) to 6*72*3 (1296).
    expect(output).toContain("> 42\n> 6\n");
  } finally {
    repl.stdin.end();
    await closed;
    act(() => root.unmount());
    vi.unstubAllGlobals();
  }
});
