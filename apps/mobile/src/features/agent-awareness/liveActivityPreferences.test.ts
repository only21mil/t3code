import { beforeEach, vi } from "vite-plus/test";
import { describe, expect, it } from "@effect/vitest";
import * as Effect from "effect/Effect";
import { ManagedRelay } from "@t3tools/client-runtime/relay";
import * as Layer from "effect/Layer";

import { setLiveActivityUpdatesEnabled } from "./liveActivityPreferences";
import { updateAgentAwarenessRegistrationPreferences } from "./remoteRegistration";

vi.mock("./remoteRegistration", () => ({
  updateAgentAwarenessRegistrationPreferences: vi.fn(() => Effect.void),
}));

const layerTest = Layer.succeed(ManagedRelay.ManagedRelayClient, null as never);

describe("liveActivityPreferences", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it.effect("restores the device preference when the relay rejects the update", () => {
    vi.mocked(updateAgentAwarenessRegistrationPreferences).mockImplementationOnce(() =>
      Effect.fail(new Error("relay rejected the registration")),
    );

    return Effect.gen(function* () {
      const exit = yield* Effect.exit(
        setLiveActivityUpdatesEnabled({ enabled: false, previousEnabled: true }),
      );

      expect(exit._tag).toBe("Failure");
      expect(vi.mocked(updateAgentAwarenessRegistrationPreferences).mock.calls).toEqual([
        [{ liveActivitiesEnabled: false }],
        [{ liveActivitiesEnabled: true }],
      ]);
    }).pipe(Effect.provide(layerTest));
  });
});
