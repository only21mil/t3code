import { EnvironmentId, ThreadId, type ScopedThreadRef } from "@t3tools/contracts";
import { expect, it, vi } from "vite-plus/test";
import { render } from "../../test/render";
import { selectThreadRightPanelState, useRightPanelStore } from "../rightPanelStore";
import { useRightPanelSurfaceClose } from "./useRightPanelSurfaceClose";

const fixture = vi.hoisted(() => ({
  confirmed: false,
  dialogs: [] as string[],
  sessions: new Set<string>(),
}));
vi.mock("~/localApi", () => ({
  readLocalApi: () => ({
    dialogs: {
      confirm: async (message: string) => {
        fixture.dialogs.push(message);
        return fixture.confirmed;
      },
    },
  }),
}));
vi.mock("../components/terminal/useThreadTerminalActions", () => ({
  useThreadTerminalActions: () => ({
    closeTerminalSession: (terminalId: string) => fixture.sessions.delete(terminalId),
  }),
}));
vi.mock("../state/session", () => ({
  useEnvironmentScope: () => true,
  readEnvironmentScope: () => true,
}));
// The commands are replaced above; importing their runtime would connect a client.
vi.mock("../state/use-atom-command", () => ({ useAtomCommand: () => async () => undefined }));
vi.mock("../state/preview", () => ({ previewEnvironment: { close: {} } }));

const threadRef: ScopedThreadRef = {
  environmentId: EnvironmentId.make("environment-a"),
  threadId: ThreadId.make("thread-a"),
};
const labels = new Map([
  ["term-1", "build"],
  ["term-2", "server"],
]);

function setup(confirmed: boolean) {
  fixture.confirmed = confirmed;
  fixture.dialogs = [];
  fixture.sessions = new Set(["term-1", "term-2"]);
  useRightPanelStore.setState({ byThreadKey: {} });
  useRightPanelStore.getState().openTerminal(threadRef, "term-1");
  useRightPanelStore.getState().openTerminal(threadRef, "term-2");
  function Harness() {
    const { closeSurface, closeOtherSurfaces, closeSurfacesToRight, closeAllSurfaces } =
      useRightPanelSurfaceClose({ threadRef, terminalLabelsById: labels });
    const first = () => openSurfaces()[0]!;
    return (
      <>
        <button onClick={() => closeSurface(openSurfaces()[1]!)}>Close tab</button>
        <button onClick={() => closeOtherSurfaces(first())}>Close others</button>
        <button onClick={() => closeSurfacesToRight(first())}>Close to the right</button>
        <button onClick={() => closeAllSurfaces()}>Close all</button>
      </>
    );
  }
  return Harness;
}

const openSurfaces = () =>
  selectThreadRightPanelState(useRightPanelStore.getState().byThreadKey, threadRef).surfaces;

it.each([
  { action: "Close tab", dialog: 'Close terminal "server"?' },
  { action: "Close others", dialog: 'Close terminal "server"?' },
  { action: "Close to the right", dialog: 'Close terminal "server"?' },
  { action: "Close all", dialog: "Close 2 terminals?" },
])(
  "$action keeps every terminal when its confirmation is cancelled",
  async ({ action, dialog }) => {
    const Harness = setup(false);
    await using screen = await render(<Harness />);
    await screen.getByRole("button", { name: action }).click();
    expect(fixture.dialogs.map((message) => message.split("\n")[0])).toEqual([dialog]);
    expect(openSurfaces()).toHaveLength(2);
    expect([...fixture.sessions]).toEqual(["term-1", "term-2"]);
  },
);

it("Close all closes every terminal once confirmed", async () => {
  const Harness = setup(true);
  await using screen = await render(<Harness />);
  await screen.getByRole("button", { name: "Close all" }).click();
  expect(fixture.dialogs).toEqual([
    'Close 2 terminals?\nThis stops their running processes and clears their histories: "build", "server".',
  ]);
  expect(openSurfaces()).toEqual([]);
  expect(fixture.sessions.size).toBe(0);
});
