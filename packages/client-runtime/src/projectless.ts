import type { EnvironmentId } from "@t3tools/contracts";

const PROJECTLESS_LOGICAL_KEY_PREFIX = "projectless:";

export function projectlessLogicalKey(environmentId: EnvironmentId): string {
  return `${PROJECTLESS_LOGICAL_KEY_PREFIX}${environmentId}`;
}
