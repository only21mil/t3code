import { presentComposerBackgroundWork } from "@t3tools/client-runtime/state/thread-execution";
import { RunId, ThreadId, TurnItemId } from "@t3tools/contracts";
import {
  deriveLiveSubagents,
  derivePendingBackgroundWork,
} from "@t3tools/shared/orchestrationV2PendingBackgroundWork";
import { describe, expect, it } from "vite-plus/test";

import type { ComposerBannerStackItem } from "./ComposerBannerStack";
import {
  composeComposerBannerStack,
  composeThreadActivityBanners,
  orderComposerBannerStack,
} from "./composerBannerStack.logic";

const banner = (
  id: string,
  options: Partial<Pick<ComposerBannerStackItem, "priority" | "variant">> = {},
): ComposerBannerStackItem => ({
  id,
  variant: options.variant ?? "default",
  ...(options.priority === undefined ? {} : { priority: options.priority }),
  icon: null,
  title: id,
});

// What the user sees: the front item, and the items tucked behind hover.
const visible = (
  bannerItems: ReadonlyArray<ComposerBannerStackItem>,
  activity: { readonly syncPhase?: string; readonly taskPlan?: string } = {},
) => {
  const { items, activityItem } = composeComposerBannerStack(bannerItems, {
    syncPhase: activity.syncPhase ?? null,
    taskPlan: activity.taskPlan ?? null,
  });
  const [front, ...stacked] = orderComposerBannerStack(items).map((item) => item.id);
  return {
    front,
    stacked,
    taskPlanInline: activity.taskPlan !== undefined && activityItem === null,
  };
};

describe("composeComposerBannerStack", () => {
  it("keeps a working parent's child links in front of its task plan", () => {
    const runs = [{ id: RunId.make("run:parent"), ordinal: 1, status: "running" as const }];
    const work = {
      latestRun: runs[0],
      runs,
      providerThreads: [],
      turnItems: [
        {
          id: TurnItemId.make("item:child"),
          type: "subagent" as const,
          status: "running" as const,
          title: "produce_probe",
          runId: runs[0]!.id,
          childThreadId: ThreadId.make("thread:child"),
        },
      ],
    };
    const strip = presentComposerBackgroundWork({
      threadWorking: true,
      pendingTasks: derivePendingBackgroundWork(work),
      liveSubagents: deriveLiveSubagents(work),
    });
    expect(strip?.presentation.items.map((item) => item.childThreadId)).toEqual(["thread:child"]);

    // ChatView files the strip as activity.
    const bannerItems = [banner("background-work:thread:parent", { priority: "activity" })];
    expect(visible(bannerItems, { taskPlan: "Tasks 0/3" })).toEqual({
      front: "background-work:thread:parent",
      stacked: [],
      taskPlanInline: true,
    });
  });

  it("still leads with the task plan over notices", () => {
    expect(
      visible([banner("branch-mismatch", { variant: "info" })], { taskPlan: "Tasks" }),
    ).toEqual({ front: "composer-activity", stacked: ["branch-mismatch"], taskPlanInline: false });
  });

  it("leads with the sync phase, which is brief", () => {
    expect(
      visible([banner("background-work:t", { priority: "activity" })], {
        syncPhase: "Syncing",
        taskPlan: "Tasks",
      }),
    ).toMatchObject({ front: "composer-activity", stacked: ["background-work:t"] });
  });

  it("adds no row without banners, where the Tasks tab shows instead", () => {
    expect(visible([], { taskPlan: "Tasks" })).toEqual({
      front: undefined,
      stacked: [],
      taskPlanInline: true,
    });
  });

  it("orders activity, then urgent notices, then the rest, keeping each tier's order", () => {
    expect(
      visible([
        banner("info"),
        banner("error", { variant: "error" }),
        banner("goal", { priority: "activity" }),
        banner("urgent", { priority: "urgent" }),
        banner("child", { priority: "activity" }),
      ]),
    ).toEqual({
      front: "goal",
      stacked: ["child", "error", "urgent", "info"],
      taskPlanInline: false,
    });
  });
});

describe("composeThreadActivityBanners", () => {
  // The three activity banners ChatView builds for the open thread.
  const childInput = banner("child-input:thread:asking", { priority: "activity" });
  const goal = { ...banner("goal:thread:parent", { priority: "activity" }), actions: "Clear" };
  const backgroundWork = banner("background-work:thread:parent", { priority: "activity" });

  it("keeps live subagent links in front of a persistent goal", () => {
    const bannerItems = composeThreadActivityBanners({ childInput: null, goal, backgroundWork });
    expect(visible(bannerItems)).toEqual({
      front: "background-work:thread:parent",
      stacked: ["goal:thread:parent"],
      taskPlanInline: false,
    });
    // The goal stays one hover away with its own actions.
    expect(bannerItems.find((item) => item.id === goal.id)).toBe(goal);
  });

  it("keeps the links in front of the goal when there is also a task plan", () => {
    const bannerItems = composeThreadActivityBanners({ childInput: null, goal, backgroundWork });
    expect(visible(bannerItems, { taskPlan: "Tasks 1/4" })).toEqual({
      front: "background-work:thread:parent",
      stacked: ["goal:thread:parent"],
      taskPlanInline: true,
    });
  });

  it("still leads with a subagent's request for input", () => {
    expect(
      visible(composeThreadActivityBanners({ childInput, goal, backgroundWork }), {
        taskPlan: "Tasks",
      }),
    ).toEqual({
      front: "child-input:thread:asking",
      stacked: ["background-work:thread:parent", "goal:thread:parent"],
      taskPlanInline: true,
    });
  });

  it("still leads with the sync phase", () => {
    expect(
      visible(composeThreadActivityBanners({ childInput: null, goal, backgroundWork }), {
        syncPhase: "Syncing",
      }),
    ).toMatchObject({
      front: "composer-activity",
      stacked: ["background-work:thread:parent", "goal:thread:parent"],
    });
  });

  it("shows the goal in front when no subagent is live", () => {
    expect(
      visible(composeThreadActivityBanners({ childInput: null, goal, backgroundWork: null }), {
        taskPlan: "Tasks",
      }),
    ).toEqual({ front: "goal:thread:parent", stacked: [], taskPlanInline: true });
  });
});
