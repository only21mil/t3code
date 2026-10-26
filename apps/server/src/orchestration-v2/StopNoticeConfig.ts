import { STOP_NOTICE_FALLBACK_OWNER } from "@t3tools/contracts";
import * as Context from "effect/Context";
import * as Effect from "effect/Effect";
import * as Layer from "effect/Layer";
import * as Path from "effect/Path";

import * as ServerConfig from "../config.ts";

/**
 * Where stop events go. Set only by whoever starts the server, through
 * `T3CODE_STOP_NOTIFIER` (absolute path of an executable that takes `t3-stop`
 * or `t3-resume` and one JSON object on stdin) and optionally
 * `T3CODE_STOP_NOTIFIER_OWNER`. No client, agent or tool input can choose the
 * command. Unset, the feature is off and threads record nothing.
 */
export interface StopNoticeConfigShape {
  readonly command: string | null;
  /** The server's owner, else the Sats fallback the notifier resolves on. Never null when on. */
  readonly defaultOwner: string | null;
  /** Server-owned directory for the stop records of stops that name no result path. */
  readonly nativeRecordDir: string | null;
}

export class StopNoticeConfig extends Context.Reference<StopNoticeConfigShape>(
  "t3/orchestration-v2/StopNoticeConfig",
  { defaultValue: () => ({ command: null, defaultOwner: null, nativeRecordDir: null }) },
) {}

export function stopNoticeConfigFromEnv(
  env: NodeJS.ProcessEnv,
  nativeRecordDir: string,
): StopNoticeConfigShape {
  const command = env.T3CODE_STOP_NOTIFIER?.trim() || null;
  const defaultOwner = env.T3CODE_STOP_NOTIFIER_OWNER?.trim() || STOP_NOTICE_FALLBACK_OWNER;
  return { command, defaultOwner, nativeRecordDir };
}

export const layerConfigFromEnv = Layer.effect(
  StopNoticeConfig,
  Effect.gen(function* () {
    const { stateDir } = yield* ServerConfig.ServerConfig;
    const path = yield* Path.Path;
    return stopNoticeConfigFromEnv(process.env, path.join(stateDir, "stop-notices"));
  }),
);
