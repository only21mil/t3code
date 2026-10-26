import {
  MessageId,
  NodeId,
  RunId,
  RuntimeRequestId,
  ThreadId,
  type StopNotice,
  type StopNotifierReceipt,
} from "@t3tools/contracts";
import * as DateTime from "effect/DateTime";
import { describe, expect, it } from "vite-plus/test";

import {
  applyStopNotifierReceipt,
  planStopNotice,
  type StopNoticeFacts,
  type StopNoticeMessage,
  type StopNoticeProjection,
  type StopNoticeRun,
  type StopNoticeTriggers,
} from "./StopNoticePlanner.ts";

const threadId = ThreadId.make("thread:stopper");
const parentThreadId = ThreadId.make("thread:parent");
const at = (minute: number) => DateTime.makeUnsafe(Date.UTC(2026, 9, 25, 20, minute));

const message = (
  id: string,
  minute: number,
  extra: Partial<StopNoticeMessage> = {},
): StopNoticeMessage => ({
  id: MessageId.make(id),
  role: "user",
  createdBy: "user",
  createdAt: at(minute),
  ...extra,
});

const run = (
  ordinal: number,
  status: StopNoticeRun["status"],
  extra: Partial<StopNoticeRun> = {},
) => ({ id: RunId.make(`run:${ordinal}`), ordinal, status, ...extra }) satisfies StopNoticeRun;

const projection = (input: Partial<StopNoticeProjection> = {}): StopNoticeProjection => ({
  thread: {
    id: threadId,
    lineage: { parentThreadId: null, relationshipToParent: null, rootThreadId: threadId },
    creationSource: "web",
    stopNotice: null,
  },
  runs: [],
  messages: [message("message:objective", 1)],
  subagents: [],
  runtimeRequests: [],
  ...input,
});

const facts: StopNoticeFacts = {
  now: "2026-10-26T01:30:00.000Z",
  defaultOwner: "genesis",
  pendingBackgroundWork: false,
  pendingRestartContinuation: false,
};

const triggers = (input: Partial<StopNoticeTriggers> = {}): StopNoticeTriggers => ({
  terminalRuns: [],
  pendingRequests: [],
  resolvedRequestIds: new Set(),
  subagentEnded: false,
  objectiveMessages: [],
  ...input,
});

const declaration = (disposition: string) => ({
  disposition,
  owner: "genesis",
  resultPath: "/home/victor/work/lane/RESULT.md",
  requiredAction: "Review the draft diff and amend the brief.",
  runId: RunId.make("run:1"),
  declaredAt: "2026-10-26T01:29:00.000Z",
});

/** Plans a step and folds the notice back onto the thread, as the committed event does. */
function step(state: StopNoticeProjection, stepTriggers: StopNoticeTriggers, stepFacts = facts) {
  const planned = planStopNotice({ projection: state, triggers: stepTriggers, facts: stepFacts });
  const next =
    planned === null
      ? state
      : { ...state, thread: { ...state.thread, stopNotice: planned.notice } };
  return { planned, next };
}

describe("planStopNotice", () => {
  it("records a declared HOLD-DRAFT as a stop when its run ends with nothing continuing", () => {
    // Old cause: a hold reported only in chat ended the run and nothing sent a notice.
    const declared = step(
      projection({ runs: [run(1, "running")] }),
      triggers({ declaration: declaration("HOLD-DRAFT") }),
    );
    expect(declared.planned?.notice.stop).toBeNull();
    expect(declared.planned?.effects.map((effect) => effect.operation)).toEqual(["resume"]);

    const ended = step(
      { ...declared.next, runs: [run(1, "completed")] },
      triggers({ terminalRuns: [run(1, "completed")] }),
    );
    expect(ended.planned?.notice.stop).toMatchObject({
      disposition: "HOLD-DRAFT",
      source: "explicit",
      trigger: "run_completed",
      owner: "genesis",
      resultPath: "/home/victor/work/lane/RESULT.md",
      requiredAction: "Review the draft diff and amend the brief.",
      opener: null,
    });
    expect(ended.planned?.notice.delivery?.state).toBe("pending");
    expect(ended.planned?.effects).toEqual([
      {
        operation: "stop",
        episodeId: "message:objective",
        request: {
          thread_id: threadId,
          episode_message_id: "message:objective",
          owner: "genesis",
          disposition: "HOLD-DRAFT",
          continuation: "none",
          result_path: "/home/victor/work/lane/RESULT.md",
          required_action: "Review the draft diff and amend the brief.",
        },
      },
    ]);

    // A second terminal event in the same episode (a re-wake, a retry) records nothing new.
    expect(
      step(
        { ...ended.next, runs: [run(1, "completed")] },
        triggers({ terminalRuns: [run(1, "completed")] }),
      ).planned,
    ).toBeNull();
  });

  it("treats an owned child, queued work or a watch as an interim yield, not a stop", () => {
    const base = projection({ runs: [run(1, "completed")] });
    const withChild = step(
      { ...base, subagents: [{ status: "running" }] },
      triggers({ terminalRuns: [run(1, "completed")] }),
    );
    expect(withChild.planned?.notice.stop).toBeNull();
    expect(withChild.planned?.notice.continuation?.kind).toBe("children");
    expect(withChild.planned?.effects.map((effect) => effect.operation)).toEqual(["resume"]);

    const queued = step(
      { ...base, runs: [run(1, "completed"), run(2, "queued")] },
      triggers({ terminalRuns: [run(1, "completed")] }),
    );
    expect(queued.planned?.notice.continuation?.kind).toBe("queued_work");
    expect(queued.planned?.notice.stop).toBeNull();

    const watched = step(base, triggers({ terminalRuns: [run(1, "completed")] }), {
      ...facts,
      pendingBackgroundWork: true,
    });
    expect(watched.planned?.notice.continuation?.kind).toBe("native_event");
    expect(watched.planned?.notice.stop).toBeNull();

    // When the child finishes and the parent's wake run ends, the episode stops once.
    const finished = step(
      {
        ...withChild.next,
        subagents: [{ status: "completed" }],
        runs: [run(1, "completed"), run(2, "completed")],
      },
      triggers({ terminalRuns: [run(2, "completed")] }),
    );
    expect(finished.planned?.notice.stop?.disposition).toBe("UNDECLARED");
    expect(finished.planned?.notice.stop?.requiredAction).toContain("without a stop report");
  });

  it("stops at a pending approval, before any run completes", () => {
    const request = {
      id: RuntimeRequestId.make("request:approve"),
      kind: "command" as const,
      status: "pending" as const,
      createdAt: at(5),
    };
    const waiting = step(
      projection({ runs: [run(1, "waiting")], runtimeRequests: [request] }),
      triggers({ pendingRequests: [request] }),
    );
    expect(waiting.planned?.notice.stop).toMatchObject({
      disposition: "WAITING_APPROVAL",
      trigger: "runtime_request",
      runtimeRequestId: "request:approve",
    });

    // The answer resumes work: a new episode named by the request, allocated once.
    const resumed = step(
      { ...waiting.next, runtimeRequests: [{ ...request, status: "resolved" }] },
      triggers({ resolvedRequestIds: new Set([request.id]) }),
    );
    expect(resumed.planned?.notice.episodeId).toBe("runtime-request:request:approve");
    expect(resumed.planned?.notice.previous?.stop.disposition).toBe("WAITING_APPROVAL");
    expect(resumed.planned?.effects).toEqual([
      {
        operation: "resume",
        episodeId: "runtime-request:request:approve",
        request: {
          thread_id: threadId,
          episode_message_id: "runtime-request:request:approve",
          owner: "genesis",
        },
      },
    ]);
  });

  it("allocates one new episode per accepted message after a hold, never from a replay", () => {
    const held = step(
      projection({ runs: [run(1, "completed")] }),
      triggers({ declaration: declaration("HOLD"), terminalRuns: [run(1, "completed")] }),
    );
    expect(held.planned?.notice.stop?.disposition).toBe("HOLD");

    const answer = message("message:answer", 10);
    const resumed = step(
      {
        ...held.next,
        messages: [...held.next.messages, answer],
        runs: [run(1, "completed"), run(2, "running")],
      },
      triggers({ objectiveMessages: [answer] }),
    );
    expect(resumed.planned?.notice.episodeId).toBe("message:answer");
    expect(resumed.planned?.notice.resume?.previousEpisodeId).toBe("message:objective");
    expect(resumed.planned?.effects.map((effect) => effect.operation)).toEqual(["resume"]);

    // The same message replayed, or an older one updated, opens nothing.
    expect(step(resumed.next, triggers({ objectiveMessages: [answer] })).planned).toBeNull();
    expect(
      step(resumed.next, triggers({ objectiveMessages: [message("message:objective", 1)] }))
        .planned,
    ).toBeNull();

    // A wake is not accepted input.
    const wake = message("message:wake", 12, {
      notification: { source: { kind: "system" }, outcome: "completed", summary: "Wake" },
    });
    expect(step(resumed.next, triggers({ objectiveMessages: [wake] })).planned).toBeNull();

    // DONE after the resumed hold belongs to the new episode and keeps the hold's record.
    const done = step(
      { ...resumed.next, runs: [run(1, "completed"), run(2, "completed")] },
      triggers({ declaration: declaration("DONE"), terminalRuns: [run(2, "completed")] }),
    );
    expect(done.planned?.notice.episodeId).toBe("message:answer");
    expect(done.planned?.notice.stop?.disposition).toBe("DONE");
    expect(done.planned?.notice.previous?.stop.disposition).toBe("HOLD");
  });

  it("hands a delegated child's stop back only through its task binding", () => {
    const child = projection({
      thread: {
        id: threadId,
        lineage: { parentThreadId, relationshipToParent: "subagent", rootThreadId: parentThreadId },
        creationSource: "mcp",
        stopNotice: null,
      },
      runs: [run(1, "completed", { delegatedTaskId: NodeId.make("task:1") })],
    });
    const stopped = step(child, triggers({ terminalRuns: [run(1, "completed")] }));
    expect(stopped.planned?.notice.stop?.opener).toEqual({
      threadId: parentThreadId,
      binding: "delegated_task",
      handbackId: "task:1",
    });
    expect(stopped.planned?.effects.at(-1)?.request).toMatchObject({
      opener_thread_id: parentThreadId,
      handback_id: "task:1",
    });
  });

  it("keeps a launched thread's own notice and records its sender only as evidence", () => {
    const launched = projection({
      messages: [
        message("message:objective", 1, { senderThreadId: parentThreadId, createdBy: "agent" }),
      ],
      runs: [run(1, "failed")],
    });
    const stopped = step(launched, triggers({ terminalRuns: [run(1, "failed")] }));
    expect(stopped.planned?.notice.stop).toMatchObject({
      disposition: "FAILED",
      opener: { threadId: parentThreadId, binding: "sender", handbackId: null },
    });
    const request = stopped.planned?.effects.at(-1)?.request;
    expect(request).not.toHaveProperty("opener_thread_id");
    expect(request).not.toHaveProperty("handback_id");
  });
});

describe("applyStopNotifierReceipt", () => {
  const stopped = step(
    projection({ runs: [run(1, "completed")] }),
    triggers({ declaration: declaration("DONE"), terminalRuns: [run(1, "completed")] }),
  ).next.thread.stopNotice as StopNotice;
  const receipt = (input: Partial<StopNotifierReceipt>): StopNotifierReceipt => ({
    operation: "stop",
    episodeId: "message:objective",
    outcome: "recorded",
    notifierState: "WEBHOOK_ACCEPTED",
    deliveryEvidence: "accepted",
    eventId: "a".repeat(64),
    generation: 3,
    recipientRunId: null,
    error: null,
    final: false,
    ...input,
  });
  const apply = (input: Partial<StopNotifierReceipt>, attempt = 1) =>
    applyStopNotifierReceipt({ notice: stopped, receipt: receipt(input), attempt, now: facts.now });

  it("never reads acceptance without a recipient run as delivery", () => {
    expect(apply({})?.delivery?.state).toBe("accepted");
    expect(
      apply({ recipientRunId: "run-7", deliveryEvidence: "recipient_run" })?.delivery,
    ).toMatchObject({ state: "delivered", recipientRunId: "run-7", generation: 3 });
  });

  it("keeps failures, conflicts and an absent notifier visible", () => {
    expect(apply({ notifierState: "CONFLICT" })?.delivery?.state).toBe("rejected");
    expect(apply({ notifierState: "FAILED" })?.delivery?.state).toBe("failed");
    expect(apply({ notifierState: "RECORDED_LOCAL" })?.delivery?.state).toBe("failed");
    expect(
      apply({ outcome: "retry", notifierState: null, error: "boom" }, 2)?.delivery,
    ).toMatchObject({
      state: "pending",
      attempts: 2,
      lastError: "boom",
    });
    expect(apply({ outcome: "retry", final: true })?.delivery?.state).toBe("failed");
    expect(apply({ outcome: "unavailable" })?.delivery?.state).toBe("unavailable");
    expect(apply({ notifierState: "SUPPRESSED_HANDBACK" })?.delivery?.state).toBe("handed_back");
  });

  it("ignores a receipt for an episode the thread no longer tracks", () => {
    expect(apply({ episodeId: "message:elsewhere" })).toBeNull();
  });
});
