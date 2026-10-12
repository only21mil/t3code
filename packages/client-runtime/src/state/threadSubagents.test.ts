import { describe, expect, it } from "vite-plus/test";
import {
  NodeId,
  ProviderDriverKind,
  ProviderInstanceId,
  RunId,
  ThreadId,
  type OrchestrationV2Subagent,
} from "@t3tools/contracts";
import * as DateTime from "effect/DateTime";

import { deriveThreadTurnSubagents, resolveSubagentPillSegment } from "./threadSubagents.ts";

const at = (iso: string) => DateTime.makeUnsafe(iso);

function subagent(
  overrides: Omit<Partial<OrchestrationV2Subagent>, "id"> & { readonly id: string },
): OrchestrationV2Subagent {
  const { id, ...rest } = overrides;
  return {
    id: NodeId.make(id),
    threadId: ThreadId.make("thread-1"),
    runId: RunId.make("run-1"),
    parentNodeId: NodeId.make("node-1"),
    origin: "app_owned",
    createdBy: "agent",
    driver: ProviderDriverKind.make("codex"),
    providerInstanceId: ProviderInstanceId.make("codex"),
    providerThreadId: null,
    childThreadId: ThreadId.make("thread-child"),
    nativeTaskRef: null,
    prompt: "Do the thing",
    title: "Worker",
    model: "gpt-5.4",
    status: "running",
    result: null,
    startedAt: at("2026-06-20T00:00:00.000Z"),
    completedAt: null,
    updatedAt: at("2026-06-20T00:00:01.000Z"),
    ...rest,
  };
}

const run = (id: string, status: "running" | "completed") =>
  ({ id: RunId.make(id), status }) as never;
const activeRun = run("run-1", "running");
const finishedRun = run("run-1", "completed");

describe("deriveThreadTurnSubagents", () => {
  it("returns null when the thread has never spawned an agent", () => {
    expect(deriveThreadTurnSubagents({ runs: [activeRun], subagents: [] })).toBeNull();
  });

  it("scopes the roster to the active run and orders it by start time", () => {
    const turn = deriveThreadTurnSubagents({
      runs: [run("run-0", "completed"), activeRun],
      subagents: [
        subagent({ id: "b", startedAt: at("2026-06-20T00:00:05.000Z") }),
        subagent({ id: "old", runId: RunId.make("run-0"), status: "completed" }),
        subagent({ id: "a", startedAt: at("2026-06-20T00:00:02.000Z") }),
      ],
    });

    expect(turn?.runId).toBe("run-1");
    expect(turn?.subagents.map((entry) => entry.id)).toEqual(["a", "b"]);
    expect(turn?.turnActive).toBe(true);
  });

  it("falls back to the most recently updated agent's run once the turn settles", () => {
    const turn = deriveThreadTurnSubagents({
      runs: [finishedRun, run("run-2", "completed")],
      subagents: [
        subagent({ id: "old", status: "completed", updatedAt: at("2026-06-20T00:00:01.000Z") }),
        subagent({
          id: "recent",
          runId: RunId.make("run-2"),
          status: "completed",
          updatedAt: at("2026-06-20T00:00:09.000Z"),
        }),
      ],
    });

    expect(turn?.runId).toBe("run-2");
    expect(turn?.turnActive).toBe(false);
    expect(turn?.subagents.map((entry) => entry.id)).toEqual(["recent"]);
  });

  it("counts idle as neither working nor done", () => {
    const turn = deriveThreadTurnSubagents({
      runs: [activeRun],
      subagents: [
        subagent({ id: "a", status: "running" }),
        subagent({ id: "b", status: "idle" }),
        subagent({ id: "c", status: "failed" }),
      ],
    });

    expect(turn?.liveCount).toBe(1);
    expect(turn?.settledCount).toBe(1);
    expect(turn?.subagents).toHaveLength(3);
  });
  it("keeps an earlier run's live agent in a newer active run's roster", () => {
    const turn = deriveThreadTurnSubagents({
      runs: [run("run-0", "completed"), activeRun],
      subagents: [
        subagent({ id: "current", status: "completed" }),
        subagent({ id: "older-done", runId: RunId.make("run-0"), status: "completed" }),
        subagent({
          id: "older-live",
          runId: RunId.make("run-0"),
          status: "running",
          startedAt: at("2026-06-19T23:59:00.000Z"),
        }),
        subagent({ id: "older-waiting", runId: RunId.make("run-0"), status: "waiting" }),
        subagent({ id: "older-idle", runId: RunId.make("run-0"), status: "idle" }),
      ],
    });

    expect(turn?.runId).toBe("run-1");
    expect(turn?.subagents.map((entry) => entry.id)).toEqual([
      "older-live",
      "current",
      "older-waiting",
    ]);
    expect(turn?.liveCount).toBe(2);
    expect(turn?.settledCount).toBe(1);
  });

  it("keeps a live agent that has no run", () => {
    const turn = deriveThreadTurnSubagents({
      runs: [activeRun],
      subagents: [
        subagent({ id: "runless-live", runId: null }),
        subagent({ id: "runless-done", runId: null, status: "failed" }),
      ],
    });

    expect(turn?.runId).toBe("run-1");
    expect(turn?.subagents.map((entry) => entry.id)).toEqual(["runless-live"]);
    expect(turn?.liveCount).toBe(1);
  });

  it("adds still-live agents to the newest settled roster", () => {
    const turn = deriveThreadTurnSubagents({
      runs: [run("run-0", "completed"), finishedRun],
      subagents: [
        subagent({
          id: "older-live",
          runId: RunId.make("run-0"),
          origin: "provider_native",
          childThreadId: null,
          updatedAt: at("2026-06-20T00:00:01.000Z"),
        }),
        subagent({
          id: "recent-failed",
          status: "failed",
          startedAt: at("2026-06-20T00:00:03.000Z"),
          updatedAt: at("2026-06-20T00:00:09.000Z"),
        }),
      ],
    });

    expect(turn?.runId).toBe("run-1");
    expect(turn?.turnActive).toBe(false);
    expect(turn?.subagents.map((entry) => entry.id)).toEqual(["older-live", "recent-failed"]);
    expect(turn?.subagents[0]?.childThreadId).toBeNull();
    expect(turn?.liveCount).toBe(1);
    expect(turn?.settledCount).toBe(1);
  });

  it("still drops an earlier run's settled agents", () => {
    const turn = deriveThreadTurnSubagents({
      runs: [run("run-0", "completed"), activeRun],
      subagents: [
        subagent({ id: "older-failed", runId: RunId.make("run-0"), status: "failed" }),
        subagent({ id: "older-interrupted", runId: RunId.make("run-0"), status: "interrupted" }),
      ],
    });

    expect(turn).toBeNull();
  });
});

describe("deriveThreadTurnSubagents with child conversation liveness", () => {
  const child = (id: string) => ThreadId.make(id);
  const live = (entries: ReadonlyArray<readonly [string, boolean]>) => new Map(entries);

  it("settles an earlier task left running once its child conversation finished", () => {
    const projection = {
      runs: [run("run-0", "completed"), finishedRun],
      subagents: [
        subagent({ id: "stale", runId: RunId.make("run-0"), childThreadId: child("child-a") }),
        subagent({
          id: "current",
          status: "completed",
          childThreadId: child("child-b"),
          updatedAt: at("2026-06-20T00:00:09.000Z"),
        }),
      ],
    };
    const turn = deriveThreadTurnSubagents(projection, live([["child-a", false]]));

    expect(turn?.subagents.map((entry) => entry.id)).toEqual(["current"]);
    expect(turn?.liveCount).toBe(0);
    expect(resolveSubagentPillSegment(turn)).toBeNull();
  });

  it("shows a stale task in the selected run as idle rather than working", () => {
    const turn = deriveThreadTurnSubagents(
      {
        runs: [activeRun],
        subagents: [subagent({ id: "stale", childThreadId: child("child-a") })],
      },
      live([["child-a", false]]),
    );

    expect(turn?.subagents.map((entry) => entry.status)).toEqual(["idle"]);
    expect(turn?.liveCount).toBe(0);
    expect(resolveSubagentPillSegment(turn)?.label).toBe("1 idle");
  });

  it("shows a running follow-up on a completed task without its old output", () => {
    const projection = {
      runs: [run("run-0", "completed"), finishedRun],
      subagents: [
        subagent({
          id: "earlier",
          runId: RunId.make("run-0"),
          status: "completed",
          childThreadId: child("child-a"),
          progress: "Old progress",
          result: "Old result",
          completedAt: at("2026-06-20T00:00:04.000Z"),
        }),
        subagent({
          id: "current",
          status: "completed",
          childThreadId: child("child-b"),
          startedAt: at("2026-06-20T00:00:05.000Z"),
          updatedAt: at("2026-06-20T00:00:09.000Z"),
        }),
      ],
    };

    expect(deriveThreadTurnSubagents(projection)?.subagents.map((entry) => entry.id)).toEqual([
      "current",
    ]);
    const turn = deriveThreadTurnSubagents(projection, live([["child-a", true]]));
    expect(turn?.subagents.map((entry) => entry.id)).toEqual(["earlier", "current"]);
    const row = turn?.subagents[0];
    expect(row?.id).toBe("earlier");
    expect(row?.status).toBe("running");
    expect(row?.childThreadId).toBe("child-a");
    expect(row?.result).toBeNull();
    expect(row?.progress).toBeUndefined();
    expect(row?.startedAt).toBeNull();
    expect(row?.completedAt).toBeNull();
    expect(resolveSubagentPillSegment(turn)?.label).toBe("1/2");
    expect(projection.subagents[0]?.result).toBe("Old result");
  });

  it("counts one live conversation once when several tasks share the child", () => {
    const turn = deriveThreadTurnSubagents(
      {
        runs: [activeRun],
        subagents: [
          subagent({
            id: "first",
            status: "completed",
            result: "First answer",
            childThreadId: child("child-a"),
            startedAt: at("2026-06-20T00:00:01.000Z"),
          }),
          subagent({
            id: "second",
            childThreadId: child("child-a"),
            progress: "Second progress",
            startedAt: at("2026-06-20T00:00:02.000Z"),
          }),
          subagent({
            id: "third",
            childThreadId: child("child-a"),
            startedAt: at("2026-06-20T00:00:03.000Z"),
          }),
        ],
      },
      live([["child-a", true]]),
    );

    expect(turn?.subagents.map((entry) => [entry.id, entry.status])).toEqual([
      ["first", "completed"],
      ["second", "idle"],
      ["third", "running"],
    ]);
    expect(turn?.subagents[0]?.result).toBe("First answer");
    expect(turn?.liveCount).toBe(1);
    expect(resolveSubagentPillSegment(turn)?.label).toBe("1/3");
  });

  it("gives a shared child's live work to the newest task when none is marked active", () => {
    const turn = deriveThreadTurnSubagents(
      {
        runs: [finishedRun],
        subagents: [
          subagent({
            id: "first",
            status: "completed",
            childThreadId: child("child-a"),
            startedAt: at("2026-06-20T00:00:01.000Z"),
          }),
          subagent({
            id: "second",
            status: "failed",
            childThreadId: child("child-a"),
            startedAt: at("2026-06-20T00:00:02.000Z"),
          }),
        ],
      },
      live([["child-a", true]]),
    );

    expect(turn?.subagents.map((entry) => [entry.id, entry.status])).toEqual([
      ["first", "completed"],
      ["second", "running"],
    ]);
    expect(turn?.liveCount).toBe(1);
  });

  it("keeps task status for native, linkless and never-run children", () => {
    const turn = deriveThreadTurnSubagents(
      {
        runs: [activeRun],
        subagents: [
          subagent({ id: "native", origin: "provider_native", childThreadId: null }),
          subagent({ id: "never-ran", childThreadId: child("child-new") }),
          subagent({ id: "runless", runId: null, childThreadId: child("child-unknown") }),
          subagent({ id: "failed", status: "failed", childThreadId: child("child-gone") }),
          subagent({ id: "interrupted", status: "interrupted", childThreadId: child("child-a") }),
        ],
      },
      live([["child-a", false]]),
    );

    expect(turn?.subagents.map((entry) => [entry.id, entry.status])).toEqual([
      ["failed", "failed"],
      ["interrupted", "interrupted"],
      ["native", "running"],
      ["never-ran", "running"],
      ["runless", "running"],
    ]);
    expect(turn?.liveCount).toBe(3);
    expect(turn?.settledCount).toBe(2);
  });

  it("keeps an earlier run's terminal history out of a later roster", () => {
    const turn = deriveThreadTurnSubagents(
      {
        runs: [run("run-0", "completed"), activeRun],
        subagents: [
          subagent({
            id: "older-done",
            runId: RunId.make("run-0"),
            status: "completed",
            childThreadId: child("child-a"),
          }),
          subagent({ id: "current", childThreadId: child("child-b") }),
        ],
      },
      live([
        ["child-a", false],
        ["child-b", true],
      ]),
    );

    expect(turn?.subagents.map((entry) => entry.id)).toEqual(["current"]);
    expect(turn?.liveCount).toBe(1);
  });
});

describe("resolveSubagentPillSegment", () => {
  it("shows how many of the turn's agents are still working", () => {
    const turn = deriveThreadTurnSubagents({
      runs: [activeRun],
      subagents: [
        subagent({ id: "a", status: "running" }),
        subagent({ id: "b", status: "waiting" }),
        subagent({ id: "c", status: "completed" }),
      ],
    });

    expect(resolveSubagentPillSegment(turn)).toEqual({
      label: "2/3",
      accessibilityLabel: "2 of 3 agents working",
    });
  });

  it("reports the finished roster while the turn is still running", () => {
    const turn = deriveThreadTurnSubagents({
      runs: [activeRun],
      subagents: [subagent({ id: "a", status: "completed" })],
    });

    expect(resolveSubagentPillSegment(turn)).toEqual({
      label: "1 done",
      accessibilityLabel: "1 agent done",
    });
  });

  it("hides itself once the turn is over and nothing is working", () => {
    const turn = deriveThreadTurnSubagents({
      runs: [finishedRun],
      subagents: [subagent({ id: "a", status: "completed" })],
    });

    expect(resolveSubagentPillSegment(turn)).toBeNull();
    expect(resolveSubagentPillSegment(null)).toBeNull();
  });

  it("stays visible after the turn ends while an agent is still working", () => {
    const turn = deriveThreadTurnSubagents({
      runs: [finishedRun],
      subagents: [subagent({ id: "a", status: "running" })],
    });

    expect(resolveSubagentPillSegment(turn)?.label).toBe("1/1");
  });

  it("counts an earlier run's live agent in the pill and keeps it after settling", () => {
    const projection = {
      runs: [run("run-0", "completed"), run("run-1", "running")],
      subagents: [
        subagent({ id: "older-live", runId: RunId.make("run-0") }),
        subagent({
          id: "current",
          status: "completed",
          updatedAt: at("2026-06-20T00:00:09.000Z"),
        }),
      ],
    };

    expect(resolveSubagentPillSegment(deriveThreadTurnSubagents(projection))?.label).toBe("1/2");
    expect(
      resolveSubagentPillSegment(
        deriveThreadTurnSubagents({
          ...projection,
          runs: [run("run-0", "completed"), finishedRun],
        }),
      )?.label,
    ).toBe("1/2");
  });

  it("does not call failed or stopped agents done", () => {
    const turn = deriveThreadTurnSubagents({
      runs: [activeRun],
      subagents: [
        subagent({ id: "a", status: "completed" }),
        subagent({ id: "b", status: "failed" }),
        subagent({ id: "c", status: "interrupted" }),
        subagent({ id: "d", status: "cancelled" }),
        subagent({ id: "e", status: "idle" }),
      ],
    });

    expect(resolveSubagentPillSegment(turn)).toEqual({
      label: "1 done · 1 failed · 2 stopped · 1 idle",
      accessibilityLabel: "1 agent done, 1 failed, 2 stopped, 1 idle",
    });
  });

  it("names a lone failed agent as failed", () => {
    const turn = deriveThreadTurnSubagents({
      runs: [activeRun],
      subagents: [subagent({ id: "a", status: "failed" })],
    });

    expect(resolveSubagentPillSegment(turn)).toEqual({
      label: "1 failed",
      accessibilityLabel: "1 agent failed",
    });
  });
});
