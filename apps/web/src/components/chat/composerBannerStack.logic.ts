import type { ReactNode } from "react";

import type { ComposerBannerStackContent, ComposerBannerStackItem } from "./ComposerBannerStack";

export type ComposerBannerStackEntry = ComposerBannerStackItem | ComposerBannerStackContent;

type PrioritizedEntry = Pick<ComposerBannerStackEntry, "variant" | "priority">;

function bannerPriority(item: PrioritizedEntry) {
  if (item.priority === "activity") {
    return 0;
  }
  if (item.priority === "urgent" || item.variant === "error" || item.variant === "warning") {
    return 1;
  }
  return 2;
}

/**
 * Display order, front-most first; the stack tucks the rest behind hover.
 * Activity stays attached. Urgency and severity only order the notices behind it.
 */
export function orderComposerBannerStack<Entry extends PrioritizedEntry>(
  items: ReadonlyArray<Entry>,
): ReadonlyArray<Entry> {
  return items.toSorted((a, b) => bannerPriority(a) - bannerPriority(b));
}

/**
 * The thread's own activity banners, in stack order. A subagent waiting on the
 * user leads. Live subagent links come before a /goal: the goal stays up for
 * its whole lifetime and would keep the links behind the stack, while the goal
 * stays one hover away with its actions.
 */
export function composeThreadActivityBanners(banners: {
  readonly childInput: ComposerBannerStackItem | null;
  readonly goal: ComposerBannerStackItem | null;
  readonly backgroundWork: ComposerBannerStackItem | null;
}): ReadonlyArray<ComposerBannerStackItem> {
  return [banners.childInput, banners.backgroundWork, banners.goal].filter((item) => item !== null);
}

/**
 * Adds the composer's own activity row to its banner stack. The sync phase
 * leads it. The task plan leads only when no banner is activity, such as
 * subagents at work: it would hide their links behind the stack, so it stays
 * on its inline Tasks badge instead. `activityItem` is null when the row did
 * not join the stack.
 */
export function composeComposerBannerStack(
  bannerItems: ReadonlyArray<ComposerBannerStackItem>,
  activity: { readonly syncPhase: ReactNode | null; readonly taskPlan: ReactNode | null },
): {
  readonly items: ReadonlyArray<ComposerBannerStackEntry>;
  readonly activityItem: ComposerBannerStackContent | null;
} {
  const content =
    bannerItems.length === 0
      ? null
      : (activity.syncPhase ??
        (bannerItems.some((item) => item.priority === "activity") ? null : activity.taskPlan));
  if (content === null) {
    return { items: bannerItems, activityItem: null };
  }
  const activityItem: ComposerBannerStackContent = {
    id: "composer-activity",
    variant: "default",
    priority: "activity",
    content,
  };
  return { items: [activityItem, ...bannerItems], activityItem };
}
