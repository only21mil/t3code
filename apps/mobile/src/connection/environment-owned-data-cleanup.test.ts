import { Persistence } from "@t3tools/client-runtime/platform";
import { EnvironmentId } from "@t3tools/contracts";
import { describe, it } from "@effect/vitest";
import * as Effect from "effect/Effect";
import { vi } from "vite-plus/test";

const harness = vi.hoisted(() => ({
  clearOutbox: vi.fn<(environmentId: string) => Promise<void>>(),
  clearDrafts: vi.fn<(environmentId: string) => Promise<void>>(),
  clearComposerErrors: vi.fn(),
}));

vi.mock("../state/thread-outbox-removal", () => ({
  clearThreadOutboxEnvironment: harness.clearOutbox,
}));
vi.mock("../state/use-composer-drafts", () => ({
  clearComposerDraftsEnvironment: harness.clearDrafts,
}));
vi.mock("../state/thread-composer-error", () => ({
  clearThreadComposerErrorsForEnvironment: harness.clearComposerErrors,
}));

import * as EnvironmentOwnedDataCleanup from "./environment-owned-data-cleanup";

const ENVIRONMENT_ID = EnvironmentId.make("environment-1");

describe("EnvironmentOwnedDataCleanup", () => {
  it.effect("succeeds when a clear rejects", () =>
    Effect.gen(function* () {
      harness.clearOutbox.mockRejectedValue(new Error("Some queued messages could not be read."));
      harness.clearDrafts.mockResolvedValue();

      const cleanup = yield* Persistence.EnvironmentOwnedDataCleanup;
      yield* cleanup.clear(ENVIRONMENT_ID);
    }).pipe(Effect.provide(EnvironmentOwnedDataCleanup.layer)),
  );
});
