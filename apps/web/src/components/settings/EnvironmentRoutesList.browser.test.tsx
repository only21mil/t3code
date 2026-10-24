import {
  BearerConnectionProfile,
  BearerConnectionTarget,
  type ConnectionRoute,
  entryWithRoutes,
} from "@t3tools/client-runtime/connection";
import { EnvironmentId } from "@t3tools/contracts";
import * as Option from "effect/Option";
import { describe, expect, it, vi } from "vite-plus/test";
import { userEvent } from "vite-plus/test/browser";

import type { EnvironmentPresentation } from "~/state/environments";

import { render } from "../../../test/render";
import { EnvironmentRoutesList } from "./EnvironmentRoutesList";
import "~/index.css";

vi.mock("~/connection/catalog", () => ({
  environmentCatalog: { reorderRoutes: "reorderRoutes", removeRoute: "removeRoute" },
}));
vi.mock("~/state/session", async () => {
  const { none } = await import("effect/Option");
  return { usePreparedConnection: () => none() };
});
vi.mock("~/state/use-atom-command", () => ({
  useAtomCommand: () => () => Promise.resolve({ _tag: "Success", value: undefined }),
}));

const ENVIRONMENT_ID = EnvironmentId.make("environment-1");

function direct(id: string, httpBaseUrl: string): ConnectionRoute {
  return {
    target: new BearerConnectionTarget({
      environmentId: ENVIRONMENT_ID,
      label: "Desk",
      connectionId: id,
    }),
    profile: Option.some(
      new BearerConnectionProfile({
        connectionId: id,
        environmentId: ENVIRONMENT_ID,
        label: "Desk",
        httpBaseUrl,
        wsBaseUrl: httpBaseUrl.replace(/^http/, "ws"),
      }),
    ),
  };
}

const LAN = direct("lan", "http://192.168.1.10:3773/");
const TAILNET = direct("tailnet", "https://desk.tail1234.ts.net/");
const PUBLIC = direct("public", "https://desk.example.com/");

function environment(routes: ReadonlyArray<ConnectionRoute>): EnvironmentPresentation {
  const [first] = routes;
  return {
    environmentId: ENVIRONMENT_ID,
    label: "Desk",
    displayUrl: null,
    relayManaged: false,
    entry: entryWithRoutes(
      { target: first!.target, profile: first!.profile, enabled: true },
      routes,
    ),
    connection: { phase: "available", error: null, traceId: null },
    serverConfig: null,
  };
}

describe("EnvironmentRoutesList", () => {
  it("shows a route added after a reorder has saved", async () => {
    const list = (routes: ReadonlyArray<ConnectionRoute>) => (
      <EnvironmentRoutesList environment={environment(routes)} onAddRoute={() => {}} />
    );
    await using screen = await render(list([LAN, TAILNET]));

    await userEvent.click(screen.getByRole("button", { name: "Reorder LAN, position 1" }));
    await userEvent.keyboard("[Space]");
    await userEvent.keyboard("[ArrowDown]");
    await userEvent.keyboard("[Space]");
    await expect
      .element(screen.getByRole("button", { name: "Reorder Tailscale, position 1" }))
      .toBeVisible();

    await screen.rerender(list([TAILNET, LAN]));
    await screen.rerender(list([TAILNET, PUBLIC]));

    await expect
      .element(screen.getByRole("button", { name: "Reorder desk.example.com, position 2" }))
      .toBeVisible();
  });
});
