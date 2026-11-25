import {
  EnvironmentId,
  ProviderDriverKind,
  ProviderInstanceId,
  UsageLimitSourceId,
  type ServerProvider,
} from "@t3tools/contracts";
import { collectLimitAccounts, collectLimitPools } from "@t3tools/shared/usageLimits";
import { cursorUsageWindowDetails } from "@t3tools/shared/usageLimitsCopy";
import { describe, expect, it, vi } from "vite-plus/test";
import {
  buildSubscriptionUsageSnapshot,
  createWidgetRefresher,
  WIDGET_REFRESH_INTERVAL,
} from "./subscriptionUsageSnapshot";
import { m } from "../i18n/messages";

const checkedAt = "2026-09-05T12:00:00.000Z";
const now = Date.parse(checkedAt);
const window = {
  id: "session",
  kind: "session",
  label: "5 hours",
  usedPercent: 40,
  resetsAt: "2026-09-05T12:10:00.000Z",
} as const;
const limits = { checkedAt, windows: [window] };
const deepLink = "t3code-dev://settings/usage?tab=limits";
function provider(overrides: Partial<ServerProvider> = {}): ServerProvider {
  return {
    instanceId: ProviderInstanceId.make("codex"),
    driver: ProviderDriverKind.make("codex"),
    enabled: true,
    installed: true,
    version: null,
    status: "ready",
    auth: { status: "authenticated", email: "private@example.com" },
    checkedAt,
    models: [],
    slashCommands: [],
    skills: [],
    usageLimits: limits,
    ...overrides,
  };
}
function presentations(providers: readonly ServerProvider[] = [provider()]) {
  return new Map([
    [
      EnvironmentId.make("env"),
      { entry: { target: { label: "Remote" } }, serverConfig: { providers } },
    ],
  ]);
}

describe("subscription widget snapshots", () => {
  it("uses provider data and its observation time without exposing account emails", () => {
    const snapshot = buildSubscriptionUsageSnapshot(
      presentations([provider({ displayName: "private@example.com" })]),
      deepLink,
    );
    expect(snapshot.checkedAt).toBe(now);
    expect(snapshot.providers[0]).toMatchObject({
      name: "Codex",
      windows: [{ remaining: 60 }],
      expiresAt: now + 10 * 60_000,
    });
    expect(snapshot.url).toBe(deepLink);
    expect(JSON.stringify(snapshot)).not.toContain("private@example.com");
  });
  it("splits a pooled window by account without exposing emails", () => {
    const claude = (id: string, overrides: Partial<ServerProvider>) =>
      provider({
        instanceId: ProviderInstanceId.make(id),
        driver: ProviderDriverKind.make("claudeAgent"),
        auth: { status: "authenticated", email: `${id}@example.com` },
        ...overrides,
      });
    const snapshot = buildSubscriptionUsageSnapshot(
      presentations([
        claude("smol", {
          displayName: "smol",
          accentColor: "#4c6ef5",
          usageLimits: {
            checkedAt,
            windows: [{ ...window, usedPercent: 29, windowDurationMins: 300 }],
          },
        }),
        claude("relay", {
          displayName: "relay@example.com",
          usageLimits: {
            checkedAt,
            windows: [{ ...window, id: "seven_day", kind: "weekly", label: "Weekly" }],
          },
        }),
        claude("rex", {
          usageLimits: {
            checkedAt,
            windows: [{ ...window, resetsAt: "2026-09-05T11:50:00.000Z" }],
          },
        }),
      ]),
      deepLink,
    );
    const session = snapshot.providers[0]?.windows.find((w) => w.kind === "session");
    expect(session?.accounts).toStrictEqual([
      { name: "RE", remaining: 60, refill: 0 },
      {
        name: "smol",
        color: "#4c6ef5",
        remaining: 71,
        refill: 29,
        resetsAt: Date.parse(window.resetsAt),
        reset: expect.any(String),
        durationMs: 300 * 60_000,
      },
      { name: "RE2" },
    ]);
    expect(JSON.stringify(snapshot)).not.toContain("example.com");
  });
  it("uses upstream deduplication for a native account also present in a proxy hub", () => {
    const input = new Map([
      [
        EnvironmentId.make("env"),
        {
          entry: { target: { label: "Remote" } },
          serverConfig: {
            providers: [provider()],
            usageLimitSources: [
              {
                id: UsageLimitSourceId.make("hub"),
                kind: "cliproxy" as const,
                label: "Hub",
                checkedAt,
                accounts: [
                  {
                    id: "account",
                    driver: ProviderDriverKind.make("codex"),
                    email: " PRIVATE@example.com ",
                    usageLimits: limits,
                  },
                ],
              },
            ],
          },
        },
      ],
    ]);
    expect(buildSubscriptionUsageSnapshot(input, deepLink).providers[0]?.detail).toBe(
      "Subscription remaining",
    );
    input.get(EnvironmentId.make("env"))!.serverConfig.providers = [];
    const snapshot = buildSubscriptionUsageSnapshot(input, deepLink);
    expect(snapshot.providers[0]?.name).toBe("Codex");
    expect(JSON.stringify(snapshot)).not.toContain("example.com");
  });
  it("bounds OS storage and puts the most constrained windows first", () => {
    const windows = Array.from({ length: 20 }, (_, index) => ({
      ...window,
      id: `${index}`,
      usedPercent: index * 5,
    }));
    const snapshot = buildSubscriptionUsageSnapshot(
      presentations([provider({ usageLimits: { checkedAt, windows } })]),
      deepLink,
    );
    expect(snapshot.providers[0]?.windows).toHaveLength(6);
    expect(snapshot.providers[0]?.totalWindows).toBe(20);
    expect(snapshot.providers[0]?.windows[0]?.remaining).toBe(5);
  });
  it("uses the freshest copy of an account across environments before pooling", () => {
    const input = presentations();
    input.set(EnvironmentId.make("other"), {
      entry: { target: { label: "Other" } },
      serverConfig: {
        providers: [
          provider({
            usageLimits: {
              checkedAt: new Date(now + 60_000).toISOString(),
              windows: [{ ...window, usedPercent: 80 }],
            },
          }),
        ],
      },
    });
    const snapshot = buildSubscriptionUsageSnapshot(input, deepLink);
    expect(snapshot.providers[0]?.detail).toBe("Subscription remaining");
    expect(snapshot.providers[0]?.windows[0]?.remaining).toBe(20);
  });
  it("shows every provider that reports limits, Codex and Claude first", () => {
    const driver = (id: string, overrides: Partial<ServerProvider> = {}) =>
      provider({
        instanceId: ProviderInstanceId.make(id),
        driver: ProviderDriverKind.make(id),
        auth: { status: "authenticated", email: `${id}@example.com` },
        ...overrides,
      });
    const antigravity = driver("antigravity", {
      usageLimits: {
        checkedAt: "2026-09-05T11:00:00.000Z",
        windows: [{ ...window, id: "gemini", label: "Gemini Pro", usedPercent: 70 }],
      },
    });
    const claude = driver("claudeAgent");

    const withoutCodex = buildSubscriptionUsageSnapshot(
      presentations([claude, antigravity]),
      deepLink,
    );
    expect(withoutCodex.providers.map((p) => p.name)).toStrictEqual(["Claude", "Antigravity"]);
    expect(withoutCodex.providers[1]).toMatchObject({
      colors: { light: "#8c7bd1", dark: "#8c7bd1" },
      windows: [{ label: "Gemini Pro", remaining: 30 }],
    });

    const all = buildSubscriptionUsageSnapshot(
      presentations([driver("newAgent"), antigravity, claude, provider()]),
      deepLink,
    );
    expect(all.providers.map((p) => p.name)).toStrictEqual([
      "Codex",
      "Claude",
      "Antigravity",
      "newAgent",
    ]);
    expect(Object.hasOwn(all.providers[3]!, "colors")).toBe(false);
    expect(all.checkedAt).toBe(Date.parse("2026-09-05T11:00:00.000Z"));
  });
  it("leaves out a configured provider that never reports limits or is unavailable", () => {
    const snapshot = buildSubscriptionUsageSnapshot(
      presentations([
        provider(),
        provider({
          instanceId: ProviderInstanceId.make("opencode"),
          driver: ProviderDriverKind.make("opencode"),
          usageLimits: undefined,
        }),
        provider({
          instanceId: ProviderInstanceId.make("cursor"),
          driver: ProviderDriverKind.make("cursor"),
          availability: "unavailable",
        }),
      ]),
      deepLink,
    );
    expect(snapshot.providers.map((p) => p.name)).toStrictEqual(["Codex"]);
  });
  it("hides Cursor's duplicate overall window and labels windows as Limits does", () => {
    const cursor = presentations([
      provider({
        instanceId: ProviderInstanceId.make("cursor"),
        driver: ProviderDriverKind.make("cursor"),
        usageLimits: {
          checkedAt,
          windows: ["totalPercentUsed", "autoPercentUsed", "apiPercentUsed"].map((id) => ({
            ...window,
            id,
            kind: "monthly" as const,
            label: id,
          })),
        },
      }),
    ]);
    const snapshot = buildSubscriptionUsageSnapshot(cursor, deepLink);
    const [pool] = collectLimitPools(collectLimitAccounts(cursor), 0);
    expect(snapshot.providers[0]?.windows.map((w) => w.label)).toStrictEqual(
      ["autoPercentUsed", "apiPercentUsed"].map(
        (id) => cursorUsageWindowDetails(id, pool!, m)?.label,
      ),
    );
    expect(snapshot.providers[0]?.totalWindows).toBe(2);
  });
  it("leads with the part that tells windows of one provider apart", () => {
    const labels = (driver: string, windowLabels: readonly string[]) =>
      buildSubscriptionUsageSnapshot(
        presentations([
          provider({
            instanceId: ProviderInstanceId.make(driver),
            driver: ProviderDriverKind.make(driver),
            usageLimits: {
              checkedAt,
              windows: windowLabels.map((label, index) => ({
                ...window,
                id: `${index}`,
                label,
                usedPercent: 90 - index * 10,
              })),
            },
          }),
        ]),
        deepLink,
      ).providers[0]?.windows.map((w) => w.label);
    expect(
      labels("antigravity", [
        "Gemini · 5-hour",
        "Gemini · Weekly",
        "Claude & GPT (shared) · Weekly",
      ]),
    ).toStrictEqual(["5-hour · Gemini", "Weekly · Gemini", "Claude & GPT (shared) · Weekly"]);
    expect(labels("claudeAgent", ["Session", "Weekly · Sonnet", "Weekly · Opus"])).toStrictEqual([
      "Session",
      "Sonnet · Weekly",
      "Opus · Weekly",
    ]);
  });
});

describe("subscription widget expiry", () => {
  const maxAgeDeadline = now + 15 * 60_000;
  function single(resetsAt: string) {
    return buildSubscriptionUsageSnapshot(
      presentations([provider({ usageLimits: { checkedAt, windows: [{ ...window, resetsAt }] } })]),
      deepLink,
    ).providers[0];
  }

  it.each(["2026-09-05T11:50:00.000Z", checkedAt])(
    "keeps usage whose reset at %s already happened when observed",
    (resetsAt) => {
      expect(single(resetsAt)).toMatchObject({
        detail: "Subscription remaining",
        expiresAt: maxAgeDeadline,
        windows: [{ remaining: 60, reset: expect.stringMatching(/^Reset /) }],
      });
    },
  );

  it.each([
    { resetAccount: 1, expiresAt: maxAgeDeadline, label: /^Reset / },
    { resetAccount: 0, expiresAt: now + 2 * 60_000, label: /^Next reset / },
  ])(
    "compares a pooled reset with its own account's observation (account $resetAccount)",
    ({ resetAccount, expiresAt, label }) => {
      // Account 0 was observed at 12:00, account 1 at 12:05; the pooled reset is at 12:02.
      const snapshot = buildSubscriptionUsageSnapshot(
        presentations(
          [checkedAt, "2026-09-05T12:05:00.000Z"].map((accountCheckedAt, index) =>
            provider({
              instanceId: ProviderInstanceId.make(`codex-${index}`),
              auth: { status: "authenticated", email: `account-${index}@example.com` },
              usageLimits: {
                checkedAt: accountCheckedAt,
                windows: [
                  {
                    ...window,
                    resetsAt:
                      index === resetAccount
                        ? "2026-09-05T12:02:00.000Z"
                        : "2026-09-05T13:00:00.000Z",
                  },
                ],
              },
            }),
          ),
        ),
        deepLink,
      );
      expect(snapshot.providers[0]).toMatchObject({
        detail: "2 accounts · pooled",
        expiresAt,
        windows: [{ remaining: 60, reset: expect.stringMatching(label) }],
      });
    },
  );
});

describe("widget refresh probes", () => {
  it("does not overlap a slow probe even after the refresh interval", async () => {
    let finish!: () => void;
    const probe = vi.fn(
      () =>
        new Promise<void>((resolve) => {
          finish = resolve;
        }),
    );
    const refresh = createWidgetRefresher(probe);
    const first = refresh(["one", "one"], now);
    await refresh(["one"], now + WIDGET_REFRESH_INTERVAL);
    expect(probe).toHaveBeenCalledTimes(1);
    finish();
    await first;
  });
});
