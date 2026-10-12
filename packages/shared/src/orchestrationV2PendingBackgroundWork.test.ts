import { describe, expect, it } from "vite-plus/test";
import type { OrchestrationV2PendingBackgroundTask } from "@t3tools/contracts";
import {
  backgroundWorkHoldsCompletion,
  deriveLiveSubagents,
  derivePendingBackgroundWork,
  subagentConversationIsLive,
  turnItemUpdateCanEndBackgroundWork,
} from "./orchestrationV2PendingBackgroundWork.ts";

describe("turnItemUpdateCanEndBackgroundWork", () => {
  it.each([
    ["a finished subagent", true, { type: "subagent", status: "completed" }],
    ["a failed background command", true, { type: "command_execution", status: "failed" }],
    ["an idle dynamic tool", true, { type: "dynamic_tool", status: "idle" }],
    ["a running command's output", false, { type: "command_execution", status: "running" }],
    ["a waiting subagent", false, { type: "subagent", status: "waiting" }],
    ["a finished assistant message", false, { type: "assistant_message", status: "completed" }],
  ] as const)("%s: %s", (_case, canEnd, item) => {
    expect(turnItemUpdateCanEndBackgroundWork(item)).toBe(canEnd);
  });
});

describe("backgroundWorkHoldsCompletion", () => {
  const task = (
    taskId: string,
    kind: OrchestrationV2PendingBackgroundTask["kind"],
  ): OrchestrationV2PendingBackgroundTask => ({ taskId, kind });

  it.each([
    ["nothing pending", false, []],
    ["a dev server", false, [task("dev", "command")]],
    ["two long-lived shells", false, [task("web", "command"), task("api", "command")]],
    ["a subagent", true, [task("review", "subagent")]],
    ["a monitor", true, [task("watch", "monitor")]],
    ["a command and a monitor", true, [task("dev", "command"), task("watch", "monitor")]],
    ["a command and a subagent", true, [task("dev", "command"), task("review", "subagent")]],
    // Also what an unknown or missing kind decodes to.
    ["work the provider cannot name", true, [task("opaque", "background_task")]],
  ] as const)("with %s pending, holds completion: %s", (_case, holds, tasks) => {
    expect(backgroundWorkHoldsCompletion(tasks)).toBe(holds);
  });
});

describe("derivePendingBackgroundWork", () => {
  it("returns empty while the latest run is not settled", () => {
    const tasks = derivePendingBackgroundWork({
      latestRun: { id: "run-1" as never, ordinal: 1, status: "running" },
      providerThreads: [
        {
          id: "pt-1" as never,
          pendingBackgroundTasks: [{ taskId: "bg-1", description: "sleep 20", kind: "command" }],
        },
      ],
      turnItems: [
        {
          id: "item-1" as never,
          type: "command_execution",
          status: "running",
          title: "npm test",
          nativeItemRef: null,
          input: "npm test",
        },
      ],
    });
    expect(tasks).toEqual([]);
  });

  it("does not keep a settled parent waiting for an idle child", () => {
    expect(
      derivePendingBackgroundWork({
        latestRun: { id: "run-1" as never, ordinal: 1, status: "completed" },
        providerThreads: [],
        turnItems: [{ id: "idle-child", type: "subagent", status: "idle", title: "Review" }],
      }),
    ).toEqual([]);
  });

  it("returns pending work when the latest run is waiting (post-success, pre-checkpoint)", () => {
    const tasks = derivePendingBackgroundWork({
      latestRun: { id: "run-1" as never, ordinal: 1, status: "waiting" },
      providerThreads: [{ id: "pt-1" as never }],
      turnItems: [
        {
          id: "item-1" as never,
          type: "command_execution",
          status: "running",
          title: "npm test",
          nativeItemRef: { nativeId: "cmd-1" },
          input: "npm test",
        },
      ],
    });
    expect(tasks).toEqual([{ taskId: "cmd-1", description: "npm test", kind: "command" }]);
  });

  it("still returns empty when the latest run is running even with background items", () => {
    const tasks = derivePendingBackgroundWork({
      latestRun: { id: "run-1" as never, ordinal: 1, status: "running" },
      providerThreads: [
        {
          id: "pt-1" as never,
          pendingBackgroundTasks: [{ taskId: "bg-1", description: "sleep 20", kind: "command" }],
        },
      ],
      turnItems: [
        {
          id: "item-1" as never,
          type: "subagent",
          status: "running",
          title: "review",
          nativeItemRef: { nativeId: "sub-1" },
          prompt: "review",
        },
      ],
    });
    expect(tasks).toEqual([]);
  });

  it("excludes rolled_back items when the latest run is waiting", () => {
    const tasks = derivePendingBackgroundWork({
      latestRun: { id: "run-2" as never, ordinal: 2, status: "waiting" },
      providerThreads: [{ id: "pt-1" as never }],
      runs: [
        { id: "run-1" as never, ordinal: 1, status: "rolled_back" },
        { id: "run-2" as never, ordinal: 2, status: "waiting" },
      ],
      turnItems: [
        {
          id: "item-old" as never,
          type: "command_execution",
          status: "running",
          title: "from rolled-back run",
          runId: "run-1",
          nativeItemRef: { nativeId: "cmd-old" },
          input: "sleep 99",
        },
        {
          id: "item-new" as never,
          type: "command_execution",
          status: "running",
          title: "still pending",
          runId: "run-2",
          nativeItemRef: { nativeId: "cmd-new" },
          input: "npm test",
        },
      ],
    });
    expect(tasks).toEqual([
      {
        taskId: "cmd-new",
        description: "still pending",
        kind: "command",
      },
    ]);
  });

  it("returns the provider-thread roster after settlement", () => {
    const tasks = derivePendingBackgroundWork({
      latestRun: { id: "run-1" as never, ordinal: 1, status: "completed" },
      providerThreads: [
        {
          id: "pt-1" as never,
          pendingBackgroundTasks: [
            { taskId: "bg-1", description: "Run Codex review", kind: "command" },
          ],
        },
      ],
      turnItems: [],
      activeProviderThreadId: "pt-1",
    });
    expect(tasks).toEqual([{ taskId: "bg-1", description: "Run Codex review", kind: "command" }]);
  });

  it("includes nonterminal turn items and excludes completed ones", () => {
    const tasks = derivePendingBackgroundWork({
      latestRun: { id: "run-1" as never, ordinal: 1, status: "completed" },
      providerThreads: [{ id: "pt-1" as never }],
      turnItems: [
        {
          id: "item-1" as never,
          type: "command_execution",
          status: "running",
          title: "npm test",
          nativeItemRef: { nativeId: "cmd-1" },
          input: "npm test",
        },
        {
          id: "item-2" as never,
          type: "command_execution",
          status: "completed",
          title: "done",
          nativeItemRef: { nativeId: "cmd-2" },
          input: "echo done",
        },
      ],
    });
    expect(tasks).toEqual([{ taskId: "cmd-1", description: "npm test", kind: "command" }]);
  });

  it("trims normalized background-work descriptions", () => {
    const base = {
      latestRun: { id: "run-1" as never, ordinal: 1, status: "completed" as const },
      providerThreads: [
        {
          id: "pt-1" as never,
          pendingBackgroundTasks: [
            {
              taskId: "native-task",
              description: "  native background work  ",
              kind: "background_task" as const,
            },
          ],
        },
      ],
    };
    expect(
      derivePendingBackgroundWork({
        ...base,
        turnItems: [
          {
            id: "item-command" as never,
            type: "command_execution",
            status: "running",
            title: "  npm test  ",
            nativeItemRef: null,
          },
          {
            id: "item-tool" as never,
            type: "dynamic_tool",
            status: "running",
            title: null,
            nativeItemRef: null,
            toolName: "  browser.search  ",
          } as never,
        ],
      }),
    ).toEqual([
      {
        taskId: "native-task",
        description: "native background work",
        kind: "background_task",
      },
      {
        taskId: "item-command",
        description: "npm test",
        kind: "command",
      },
      {
        taskId: "item-tool",
        description: "browser.search",
        kind: "background_task",
      },
    ]);
  });

  it("dedupes roster entries against turn items by native task id", () => {
    const tasks = derivePendingBackgroundWork({
      latestRun: { id: "run-1" as never, ordinal: 1, status: "completed" },
      providerThreads: [
        {
          id: "pt-1" as never,
          pendingBackgroundTasks: [
            { taskId: "task-9", description: "Agent review", kind: "background_task" },
          ],
        },
      ],
      turnItems: [
        {
          id: "item-sub" as never,
          type: "subagent",
          status: "running",
          title: "Agent review",
          nativeItemRef: { nativeId: "task-9" },
          prompt: "review the plan",
        },
      ],
    });
    expect(tasks).toEqual([
      { taskId: "task-9", description: "Agent review", kind: "background_task" },
    ]);
  });

  it("excludes Grok persistent monitors", () => {
    const tasks = derivePendingBackgroundWork({
      latestRun: { id: "run-1" as never, ordinal: 1, status: "completed" },
      providerThreads: [{ id: "pt-1" as never }],
      turnItems: [
        {
          id: "item-1" as never,
          type: "dynamic_tool",
          status: "running",
          title: "monitor logs",
          nativeItemRef: { nativeId: "mon-1" },
          input: { persistent: true, command: "tail -f" },
        },
        {
          id: "item-2" as never,
          type: "dynamic_tool",
          status: "running",
          title: "finite monitor",
          nativeItemRef: { nativeId: "mon-2" },
          input: { persistent: false, command: "sleep 5" },
        },
      ],
    });
    expect(tasks).toEqual([
      { taskId: "mon-2", description: "finite monitor", kind: "background_task" },
    ]);
  });

  it("returns multiple tasks with stable ordering from insertion", () => {
    const tasks = derivePendingBackgroundWork({
      latestRun: { id: "run-1" as never, ordinal: 1, status: "completed" },
      providerThreads: [
        {
          id: "pt-1" as never,
          pendingBackgroundTasks: [
            { taskId: "bg-1", description: "first", kind: "command" },
            { taskId: "bg-2", description: "second", kind: "command" },
          ],
        },
      ],
      turnItems: [
        {
          id: "item-1" as never,
          type: "command_execution",
          status: "running",
          title: "third",
          nativeItemRef: { nativeId: "cmd-3" },
          input: "third",
        },
      ],
    });
    expect(tasks.map((task) => task.taskId)).toEqual(["bg-1", "bg-2", "cmd-3"]);
  });

  it("excludes turn items owned by a rolled_back run", () => {
    const tasks = derivePendingBackgroundWork({
      latestRun: { id: "run-1" as never, ordinal: 1, status: "rolled_back" },
      providerThreads: [{ id: "pt-1" as never }],
      runs: [{ id: "run-1" as never, ordinal: 1, status: "rolled_back" }],
      turnItems: [
        {
          id: "item-1" as never,
          type: "command_execution",
          status: "running",
          title: "abandoned",
          runId: "run-1",
          nativeItemRef: { nativeId: "cmd-1" },
          input: "sleep 99",
        },
      ],
    });
    expect(tasks).toEqual([]);
  });

  it("returns empty when the latest run is rolled_back even with a nonempty roster", () => {
    const tasks = derivePendingBackgroundWork({
      latestRun: { id: "run-1" as never, ordinal: 1, status: "rolled_back" },
      providerThreads: [
        {
          id: "pt-1" as never,
          pendingBackgroundTasks: [{ taskId: "bg-1", description: "sleep 20", kind: "command" }],
        },
      ],
      turnItems: [
        {
          id: "item-1" as never,
          type: "command_execution",
          status: "running",
          title: "abandoned",
          runId: "run-1",
          nativeItemRef: { nativeId: "cmd-1" },
          input: "sleep 99",
        },
      ],
    });
    expect(tasks).toEqual([]);
  });

  it("excludes an older rolled_back nonterminal item when the latest run is completed", () => {
    const tasks = derivePendingBackgroundWork({
      latestRun: { id: "run-2" as never, ordinal: 2, status: "completed" },
      providerThreads: [{ id: "pt-1" as never }],
      runs: [
        { id: "run-1" as never, ordinal: 1, status: "rolled_back" },
        { id: "run-2" as never, ordinal: 2, status: "completed" },
      ],
      turnItems: [
        {
          id: "item-old" as never,
          type: "command_execution",
          status: "running",
          title: "from rolled-back run",
          runId: "run-1",
          nativeItemRef: { nativeId: "cmd-old" },
          input: "sleep 99",
        },
        {
          id: "item-new" as never,
          type: "command_execution",
          status: "running",
          title: "still pending",
          runId: "run-2",
          nativeItemRef: { nativeId: "cmd-new" },
          input: "npm test",
        },
      ],
    });
    expect(tasks).toEqual([
      {
        taskId: "cmd-new",
        description: "still pending",
        kind: "command",
      },
    ]);
  });

  it("does not reclassify an older active run as background work", () => {
    const tasks = derivePendingBackgroundWork({
      latestRun: { id: "run-2" as never, ordinal: 2, status: "cancelled" },
      providerThreads: [
        {
          id: "pt-1" as never,
          pendingBackgroundTasks: [{ taskId: "provider-task", kind: "background_task" }],
        },
      ],
      runs: [
        { id: "run-1" as never, ordinal: 1, status: "running" },
        { id: "run-2" as never, ordinal: 2, status: "cancelled" },
      ],
      turnItems: [
        {
          id: "item-active" as never,
          type: "command_execution",
          status: "running",
          title: "foreground work",
          runId: "run-1",
          nativeItemRef: { nativeId: "cmd-active" },
          input: "vp check",
        },
      ],
    });

    expect(tasks).toEqual([]);
  });

  it("includes items with a null run id even when runs list has rolled_back rows", () => {
    const tasks = derivePendingBackgroundWork({
      latestRun: { id: "run-1" as never, ordinal: 1, status: "completed" },
      providerThreads: [{ id: "pt-1" as never }],
      runs: [{ id: "run-1" as never, ordinal: 1, status: "rolled_back" }],
      turnItems: [
        {
          id: "item-null-run" as never,
          type: "command_execution",
          status: "running",
          title: "orphan item",
          runId: null,
          nativeItemRef: { nativeId: "cmd-null" },
          input: "echo orphan",
        },
      ],
    });
    expect(tasks).toEqual([
      {
        taskId: "cmd-null",
        description: "orphan item",
        kind: "command",
      },
    ]);
  });
});

describe("derivePendingBackgroundWork kinds", () => {
  it("keeps the roster's kinds and names turn items by their type", () => {
    const tasks = derivePendingBackgroundWork({
      latestRun: { id: "run-1" as never, ordinal: 1, status: "completed" },
      providerThreads: [
        {
          id: "pt-1" as never,
          pendingBackgroundTasks: [
            { taskId: "bash", kind: "command" },
            { taskId: "watch", kind: "monitor" },
            { taskId: "workflow", kind: "background_task" },
          ],
        },
      ],
      turnItems: [
        {
          id: "item-sub" as never,
          type: "subagent",
          status: "running",
          title: "Review src/math.ts",
          nativeItemRef: { nativeId: "sub" },
          childThreadId: "thread:child" as never,
        },
        {
          id: "item-cmd" as never,
          type: "command_execution",
          status: "running",
          title: null,
          nativeItemRef: { nativeId: "cmd" },
          input: "npm test",
        },
      ],
    });
    expect(tasks).toEqual([
      { taskId: "bash", kind: "command" },
      { taskId: "watch", kind: "monitor" },
      { taskId: "workflow", kind: "background_task" },
      {
        taskId: "sub",
        description: "Review src/math.ts",
        kind: "subagent",
        childThreadId: "thread:child",
      },
      { taskId: "cmd", description: "npm test", kind: "command" },
    ]);
  });

  describe("pull request watches", () => {
    const watch = {
      startedAt: "2026-10-05T00:00:00.000Z",
      headSha: null,
      failedChecks: [],
      passed: false,
      passedChecks: [],
      remarksThrough: "2026-10-05T00:00:00.000Z",
      remarkIds: [],
      conflicting: false,
      wakes: 0,
    };
    const link = (
      number: number,
      extra: { source?: "agent" | "stack-dismissed"; watched?: boolean },
    ) => ({
      host: "github.com",
      repository: "acme/app",
      number,
      url: `https://github.com/acme/app/pull/${number}`,
      source: extra.source ?? "agent",
      ...(extra.watched === false ? {} : { watch }),
    });
    const pullRequests = [
      link(1, {}),
      link(2, { watched: false }),
      link(3, { source: "stack-dismissed" }),
    ];

    it("keeps a settled run waiting on each visible watch, as a monitor", () => {
      const tasks = derivePendingBackgroundWork({
        latestRun: { id: "run-1" as never, ordinal: 1, status: "completed" },
        providerThreads: [],
        turnItems: [],
        pullRequests,
      });
      expect(tasks).toEqual([
        {
          taskId: "pull-request-watch:github.com/acme/app#1",
          description: "Watching pull request #1",
          kind: "monitor",
        },
      ]);
      expect(backgroundWorkHoldsCompletion(tasks)).toBe(true);
    });

    it("keeps a thread that never ran waiting on its watch", () => {
      expect(
        derivePendingBackgroundWork({
          latestRun: null,
          providerThreads: [],
          turnItems: [],
          pullRequests,
        }).map((task) => task.taskId),
      ).toEqual(["pull-request-watch:github.com/acme/app#1"]);
    });

    it("lists no watch while a run is active", () => {
      expect(
        derivePendingBackgroundWork({
          latestRun: { id: "run-1" as never, ordinal: 1, status: "running" },
          providerThreads: [],
          turnItems: [],
          pullRequests,
        }),
      ).toEqual([]);
    });
  });
});

describe("deriveLiveSubagents", () => {
  const run = (id: string, ordinal: number, status: "running" | "waiting" | "rolled_back") => ({
    id: id as never,
    ordinal,
    status,
  });
  const subagentItem = (
    id: string,
    status: "running" | "waiting" | "pending" | "completed" | "failed" | "interrupted",
    options: { runId?: string; childThreadId?: string; nativeId?: string } = {},
  ) => ({
    id: id as never,
    type: "subagent" as const,
    status,
    title: `Review ${id}`,
    runId: (options.runId ?? "run-2") as never,
    nativeItemRef: options.nativeId === undefined ? null : { nativeId: options.nativeId },
    ...(options.childThreadId === undefined
      ? {}
      : { childThreadId: options.childThreadId as never }),
  });
  const runningParent = {
    latestRun: run("run-2", 2, "running"),
    runs: [run("run-1", 1, "waiting"), run("run-2", 2, "running")],
    providerThreads: [],
  };

  it("names a working parent's live child, which the post-settlement list leaves out", () => {
    const input = {
      ...runningParent,
      turnItems: [subagentItem("a", "running", { childThreadId: "thread:a" })],
    };
    expect(derivePendingBackgroundWork(input)).toEqual([]);
    expect(deriveLiveSubagents(input)).toEqual([
      { taskId: "a", description: "Review a", kind: "subagent", childThreadId: "thread:a" },
    ]);
  });

  it("keeps a child launched by an earlier turn while a newer turn works", () => {
    expect(
      deriveLiveSubagents({
        ...runningParent,
        turnItems: [
          subagentItem("old", "waiting", { runId: "run-1", childThreadId: "thread:old" }),
        ],
      }).map((task) => task.taskId),
    ).toEqual(["old"]);
  });

  it("leaves finished, failed and interrupted children to the relationship history", () => {
    expect(
      deriveLiveSubagents({
        ...runningParent,
        turnItems: [
          subagentItem("done", "completed", { childThreadId: "thread:done" }),
          subagentItem("failed", "failed", { childThreadId: "thread:failed" }),
          subagentItem("stopped", "interrupted", { childThreadId: "thread:stopped" }),
          subagentItem("queued", "pending", { childThreadId: "thread:queued" }),
        ],
      }).map((task) => task.taskId),
    ).toEqual(["queued"]);
  });

  it("trusts the child conversation over its task status", () => {
    const tasks = deriveLiveSubagents({
      ...runningParent,
      turnItems: [
        // The task finished, but a follow-up is running in the child.
        subagentItem("follow-up", "completed", { childThreadId: "thread:follow-up" }),
        // The task was left running, but its child finished.
        subagentItem("stale", "running", { childThreadId: "thread:stale" }),
        // No shell for this child, so the task status stands.
        subagentItem("unknown", "running", { childThreadId: "thread:unknown" }),
      ],
      childConversationLive: new Map([
        ["thread:follow-up", true],
        ["thread:stale", false],
      ]),
    });
    expect(tasks.map((task) => task.taskId)).toEqual(["follow-up", "unknown"]);
  });

  it("drops children of rolled-back turns, and the roster when the latest turn rolled back", () => {
    expect(
      deriveLiveSubagents({
        latestRun: run("run-2", 2, "rolled_back"),
        runs: [run("run-1", 1, "waiting"), run("run-2", 2, "rolled_back")],
        providerThreads: [
          {
            id: "pt-1" as never,
            pendingBackgroundTasks: [{ taskId: "native", kind: "subagent" }],
          },
        ],
        turnItems: [
          subagentItem("abandoned", "running", { runId: "run-2" }),
          subagentItem("earlier", "running", { runId: "run-1" }),
        ],
      }).map((task) => task.taskId),
    ).toEqual(["earlier"]);
  });

  it("names native roster subagents once, and only subagents", () => {
    const tasks = deriveLiveSubagents({
      ...runningParent,
      activeProviderThreadId: "pt-1",
      providerThreads: [
        {
          id: "pt-1" as never,
          pendingBackgroundTasks: [
            { taskId: "native-1", description: "  Explore the repo ", kind: "subagent" },
            { taskId: "dev", description: "vp run dev", kind: "command" },
            { taskId: "watch", kind: "monitor" },
          ],
        },
        {
          id: "pt-old" as never,
          pendingBackgroundTasks: [{ taskId: "other-thread", kind: "subagent" }],
        },
      ],
      turnItems: [
        subagentItem("item-1", "running", { nativeId: "native-1" }),
        {
          id: "cmd" as never,
          type: "command_execution",
          status: "running",
          title: "npm test",
          input: "npm test",
        },
      ],
    });
    expect(tasks).toEqual([
      { taskId: "native-1", description: "Explore the repo", kind: "subagent" },
    ]);
  });

  it("names a child thread once when several items point at it", () => {
    expect(
      deriveLiveSubagents({
        ...runningParent,
        turnItems: [
          subagentItem("first", "running", { runId: "run-1", childThreadId: "thread:a" }),
          subagentItem("again", "running", { childThreadId: "thread:a" }),
        ],
      }).map((task) => task.taskId),
    ).toEqual(["first"]);
  });
});

describe("subagentConversationIsLive", () => {
  it.each([
    ["an active run", true, { activityRunStatus: "running", latestRunId: "r", status: "running" }],
    ["a waiting run", true, { activityRunStatus: "waiting", latestRunId: "r", status: "waiting" }],
    ["a queued follow-up", true, { activityRunStatus: null, latestRunId: "r", status: "queued" }],
    ["a completed run", false, { activityRunStatus: null, latestRunId: "r", status: "completed" }],
    ["a failed run", false, { latestRunId: "r", status: "failed" }],
    ["no run yet", null, { activityRunStatus: null, latestRunId: null, status: "idle" }],
  ] as const)("%s: %s", (_case, live, shell) => {
    expect(subagentConversationIsLive(shell as never)).toBe(live);
  });
});
