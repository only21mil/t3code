import type { EnvironmentId } from "@t3tools/contracts";
import * as Context from "effect/Context";
import * as Effect from "effect/Effect";
import * as Layer from "effect/Layer";

import { ServerEnvironmentIdentity } from "./ServerEnvironment.ts";

/**
 * This server's environment id for features that name it in durable records,
 * such as relay hops. Null where no identity is installed, so those features
 * refuse instead of recording a guess.
 */
export class LocalEnvironmentId extends Context.Reference<{
  readonly get: Effect.Effect<EnvironmentId | null>;
}>("t3/environment/LocalEnvironmentId", {
  defaultValue: () => ({ get: Effect.succeed(null) }),
}) {}

export const layer = Layer.effect(
  LocalEnvironmentId,
  Effect.gen(function* () {
    const identity = yield* ServerEnvironmentIdentity;
    return { get: identity.getEnvironmentId };
  }),
);
