import type { EnvironmentId } from "@t3tools/contracts";

export const PROJECTLESS_LOGICAL_KEY_PREFIX = "projectless:";

export function projectlessLogicalKey(environmentId: EnvironmentId): string {
  return `${PROJECTLESS_LOGICAL_KEY_PREFIX}${environmentId}`;
}

export function isProjectlessLogicalKey(key: string): boolean {
  return key.startsWith(PROJECTLESS_LOGICAL_KEY_PREFIX);
}
