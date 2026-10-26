import * as Context from "effect/Context";
import * as Layer from "effect/Layer";

/**
 * Where stop events go. Set only by whoever starts the server, through
 * `T3CODE_STOP_NOTIFIER` (absolute path of an executable that takes `t3-stop`
 * or `t3-resume` and one JSON object on stdin) and optionally
 * `T3CODE_STOP_NOTIFIER_OWNER`. No client, agent or tool input can choose the
 * command. Unset, the feature is off and threads record nothing.
 */
export interface StopNoticeConfigShape {
  readonly command: string | null;
  readonly defaultOwner: string | null;
}

export class StopNoticeConfig extends Context.Reference<StopNoticeConfigShape>(
  "t3/orchestration-v2/StopNoticeConfig",
  { defaultValue: () => ({ command: null, defaultOwner: null }) },
) {}

export function stopNoticeConfigFromEnv(env: NodeJS.ProcessEnv): StopNoticeConfigShape {
  const command = env.T3CODE_STOP_NOTIFIER?.trim() || null;
  const defaultOwner = env.T3CODE_STOP_NOTIFIER_OWNER?.trim() || null;
  return { command, defaultOwner };
}

export const layerConfigFromEnv = Layer.succeed(
  StopNoticeConfig,
  stopNoticeConfigFromEnv(process.env),
);
