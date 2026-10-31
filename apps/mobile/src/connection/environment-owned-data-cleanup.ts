import { Persistence } from "@t3tools/client-runtime/platform";
import * as Effect from "effect/Effect";
import * as Layer from "effect/Layer";

import { clearThreadComposerErrorsForEnvironment } from "../state/thread-composer-error";
import { clearThreadOutboxEnvironment } from "../state/thread-outbox-removal";
import { clearComposerDraftsEnvironment } from "../state/use-composer-drafts";

export const layer = Layer.succeed(
  Persistence.EnvironmentOwnedDataCleanup,
  Persistence.EnvironmentOwnedDataCleanup.of({
    clear: Effect.fn("Persistence.EnvironmentOwnedDataCleanup.clear")(function (environmentId) {
      return Effect.all(
        [
          Effect.tryPromise(() => clearThreadOutboxEnvironment(environmentId)),
          Effect.tryPromise(() => clearComposerDraftsEnvironment(environmentId)),
          Effect.sync(() => clearThreadComposerErrorsForEnvironment(environmentId)),
        ],
        { concurrency: "unbounded", discard: true },
      ).pipe(
        Effect.catch((cause) =>
          Effect.logWarning("Could not clear mobile environment-owned data.", {
            environmentId,
            cause,
          }),
        ),
      );
    }),
  }),
);
