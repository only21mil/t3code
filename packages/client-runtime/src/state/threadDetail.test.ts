import {
  EnvironmentId,
  NodeId,
  type OrchestrationV2ShellSnapshot,
  type OrchestrationV2ThreadShell,
  ProviderDriverKind,
  RuntimeRequestId,
  TurnItemId,
  type OrchestrationV2ThreadProjection,
  ThreadId,
  RunId,
  MessageId,
  type ScopedThreadRef,
} from "@t3tools/contracts";
import * as DateTime from "effect/DateTime";
import * as Option from "effect/Option";
import { AsyncResult, Atom, AtomRegistry } from "effect/reactivity";
import { describe, expect, it } from "vite-plus/test";

import {
  v2Projection,
  v2Now,
  v2ShellSnapshot,
  v2ThreadShell,
} from "./orchestrationV2TestFixtures.ts";
import { EMPTY_THREAD_HISTORY_META } from "./threadHistoryMerge.ts";
import { createEnvironmentThreadDetailAtoms } from "./threadDetail.ts";
import { resolveSubagentPillSegment } from "./threadSubagents.ts";
import { createEnvironmentThreadShellAtoms } from "./threadShell.ts";
import type { EnvironmentThreadState } from "./threads.ts";

const ref: ScopedThreadRef = {
  environmentId: EnvironmentId.make("environment-detail"),
  threadId: ThreadId.make(v2Projection.thread.id),
};

const noChildConversations = Atom.make<ReadonlyMap<string, boolean>>(new Map());
const withoutChildConversations = () => noChildConversations;

function threadState(
  partial: Pick<EnvironmentThreadState, "data" | "status" | "error"> &
    Partial<Pick<EnvironmentThreadState, "history">>,
): EnvironmentThreadState {
  return { ...partial, history: partial.history ?? EMPTY_THREAD_HISTORY_META };
}

describe("createEnvironmentThreadDetailAtoms", () => {
  it("adds environment scope while preserving the pristine projection", () => {
    const initial: AsyncResult.AsyncResult<EnvironmentThreadState, never> = AsyncResult.success(
      threadState({
        data: Option.some(v2Projection),
        status: "cached",
        error: Option.none(),
      }),
    );
    const sourceAtom = Atom.make(initial);
    const details = createEnvironmentThreadDetailAtoms(() => sourceAtom, withoutChildConversations);
    const registry = AtomRegistry.make();

    const thread = registry.get(details.threadAtom(ref));
    expect(thread).toEqual({ environmentId: ref.environmentId, projection: v2Projection });
    expect(thread?.projection).toBe(v2Projection);
    expect(registry.get(details.visibleTurnItemsAtom(ref))).toBe(v2Projection.visibleTurnItems);
    expect(registry.get(details.statusAtom(ref))).toBe("cached");
    expect(registry.get(details.historyAtom(ref))).toBe(EMPTY_THREAD_HISTORY_META);

    registry.set(
      sourceAtom,
      AsyncResult.success(
        threadState({
          data: Option.some(v2Projection),
          status: "synchronizing",
          error: Option.none(),
        }),
      ),
    );

    expect(registry.get(details.threadAtom(ref))).toBe(thread);
    expect(registry.get(details.statusAtom(ref))).toBe("synchronizing");

    const progressiveHistory = {
      ...EMPTY_THREAD_HISTORY_META,
      historyCursor: "cursor-1",
      hasMoreHistory: true,
    };
    registry.set(
      sourceAtom,
      AsyncResult.success(
        threadState({
          data: Option.some(v2Projection),
          status: "live",
          error: Option.some("Stream interrupted."),
          history: progressiveHistory,
        }),
      ),
    );

    expect(registry.get(details.threadAtom(ref))).toBe(thread);
    expect(registry.get(details.visibleTurnItemsAtom(ref))).toBe(v2Projection.visibleTurnItems);
    expect(registry.get(details.statusAtom(ref))).toBe("live");
    expect(registry.get(details.errorAtom(ref))).toBe("Stream interrupted.");
    expect(registry.get(details.historyAtom(ref))).toBe(progressiveHistory);

    registry.set(
      sourceAtom,
      AsyncResult.success(
        threadState({
          data: Option.none(),
          status: "deleted",
          error: Option.none(),
        }),
      ),
    );

    expect(registry.get(details.threadAtom(ref))).toBeNull();
    expect(registry.get(details.visibleTurnItemsAtom(ref))).toEqual([]);
    expect(registry.get(details.statusAtom(ref))).toBe("deleted");
    expect(registry.get(details.errorAtom(ref))).toBeNull();
    expect(registry.get(details.historyAtom(ref))).toBe(EMPTY_THREAD_HISTORY_META);
    registry.dispose();
  });
});

it("does not notify queue consumers for streaming text or execution nodes", () => {
  const projection = {
    ...v2Projection,
    runs: [
      {
        id: RunId.make("queued-run"),
        threadId: v2Projection.thread.id,
        ordinal: 1,
        providerInstanceId: v2Projection.thread.providerInstanceId,
        modelSelection: v2Projection.thread.modelSelection,
        providerThreadId: null,
        userMessageId: MessageId.make("queued-message"),
        rootNodeId: null,
        activeAttemptId: null,
        status: "queued" as const,
        requestedAt: v2Now,
        startedAt: null,
        completedAt: null,
        checkpointId: null,
        contextHandoffId: null,
      },
    ],
  };
  const source = Atom.make(
    AsyncResult.success(
      threadState({ data: Option.some(projection), status: "live", error: Option.none() }),
    ),
  );
  const details = createEnvironmentThreadDetailAtoms(() => source, withoutChildConversations);
  const registry = AtomRegistry.make();
  const dispose = registry.mount(details.queueWorkflowAtom(ref));
  const before = registry.get(details.queueWorkflowAtom(ref));
  const disposeCount = registry.mount(details.queuedCountAtom(ref));
  expect(registry.get(details.queuedCountAtom(ref))).toBe(1);
  registry.set(
    source,
    AsyncResult.success(
      threadState({
        data: Option.some({
          ...projection,
          nodes: [...v2Projection.nodes],
          turnItems: [...v2Projection.turnItems],
        }),
        status: "live",
        error: Option.none(),
      }),
    ),
  );
  expect(registry.get(details.queueWorkflowAtom(ref))).toBe(before);
  expect(registry.get(details.queuedCountAtom(ref))).toBe(1);
  registry.set(
    source,
    AsyncResult.success(
      threadState({ data: Option.none(), status: "deleted", error: Option.none() }),
    ),
  );
  expect(registry.get(details.queueWorkflowAtom(ref))).toBeNull();
  expect(registry.get(details.queuedCountAtom(ref))).toBe(0);
  disposeCount();
  dispose();
  registry.dispose();
});

it("does not notify the agents pill for unrelated projection updates", () => {
  const projection: OrchestrationV2ThreadProjection = {
    ...v2Projection,
    runs: [
      {
        id: RunId.make("active-run"),
        threadId: v2Projection.thread.id,
        ordinal: 1,
        providerInstanceId: v2Projection.thread.providerInstanceId,
        modelSelection: v2Projection.thread.modelSelection,
        providerThreadId: null,
        userMessageId: MessageId.make("message"),
        rootNodeId: null,
        activeAttemptId: null,
        status: "running" as const,
        requestedAt: v2Now,
        startedAt: v2Now,
        completedAt: null,
        checkpointId: null,
        contextHandoffId: null,
      },
    ],
    subagents: [
      {
        id: NodeId.make("subagent-1"),
        threadId: v2Projection.thread.id,
        runId: RunId.make("active-run"),
        parentNodeId: NodeId.make("root"),
        origin: "app_owned",
        createdBy: "agent",
        driver: ProviderDriverKind.make("codex"),
        providerInstanceId: v2Projection.thread.providerInstanceId,
        providerThreadId: null,
        childThreadId: ThreadId.make("thread-child"),
        nativeTaskRef: null,
        prompt: "Do the thing",
        title: "Worker",
        model: null,
        status: "running",
        result: null,
        startedAt: v2Now,
        completedAt: null,
        updatedAt: v2Now,
      },
    ],
  };
  const source = Atom.make(
    AsyncResult.success(
      threadState({ data: Option.some(projection), status: "live", error: Option.none() }),
    ),
  );
  const details = createEnvironmentThreadDetailAtoms(() => source, withoutChildConversations);
  const registry = AtomRegistry.make();
  const dispose = registry.mount(details.turnSubagentsAtom(ref));
  const before = registry.get(details.turnSubagentsAtom(ref));
  expect(before?.liveCount).toBe(1);
  registry.set(
    source,
    AsyncResult.success(
      threadState({
        data: Option.some({ ...projection, turnItems: [...v2Projection.turnItems] }),
        status: "live",
        error: Option.none(),
      }),
    ),
  );
  expect(registry.get(details.turnSubagentsAtom(ref))).toBe(before);
  dispose();
  registry.dispose();
});

it("keeps an earlier run's live agent in the agents pill until it settles", () => {
  const run = (id: string, ordinal: number, status: "running" | "completed") => ({
    id: RunId.make(id),
    threadId: v2Projection.thread.id,
    ordinal,
    providerInstanceId: v2Projection.thread.providerInstanceId,
    modelSelection: v2Projection.thread.modelSelection,
    providerThreadId: null,
    userMessageId: MessageId.make(`message-${ordinal}`),
    rootNodeId: null,
    activeAttemptId: null,
    status,
    requestedAt: v2Now,
    startedAt: v2Now,
    completedAt: status === "completed" ? v2Now : null,
    checkpointId: null,
    contextHandoffId: null,
  });
  const olderLive: OrchestrationV2ThreadProjection["subagents"][number] = {
    id: NodeId.make("older-subagent"),
    threadId: v2Projection.thread.id,
    runId: RunId.make("earlier-run"),
    parentNodeId: NodeId.make("root"),
    origin: "app_owned",
    createdBy: "agent",
    driver: ProviderDriverKind.make("codex"),
    providerInstanceId: v2Projection.thread.providerInstanceId,
    providerThreadId: null,
    childThreadId: ThreadId.make("thread-older-child"),
    nativeTaskRef: null,
    prompt: "Keep working",
    title: "Older worker",
    model: null,
    status: "running",
    result: null,
    startedAt: v2Now,
    completedAt: null,
    updatedAt: v2Now,
  };
  const projection: OrchestrationV2ThreadProjection = {
    ...v2Projection,
    runs: [run("earlier-run", 1, "completed"), run("active-run", 2, "running")],
    subagents: [olderLive],
  };
  const source = Atom.make(
    AsyncResult.success(
      threadState({ data: Option.some(projection), status: "live", error: Option.none() }),
    ),
  );
  const details = createEnvironmentThreadDetailAtoms(() => source, withoutChildConversations);
  const registry = AtomRegistry.make();
  const dispose = registry.mount(details.turnSubagentsAtom(ref));
  const before = registry.get(details.turnSubagentsAtom(ref));
  expect(before?.runId).toBe("active-run");
  expect(before?.subagents.map((subagent) => subagent.id)).toEqual(["older-subagent"]);
  expect(before?.liveCount).toBe(1);

  const publish = (next: OrchestrationV2ThreadProjection) =>
    registry.set(
      source,
      AsyncResult.success(
        threadState({ data: Option.some(next), status: "live", error: Option.none() }),
      ),
    );
  publish({ ...projection, turnItems: [...v2Projection.turnItems] });
  expect(registry.get(details.turnSubagentsAtom(ref))).toBe(before);

  publish({ ...projection, subagents: [{ ...olderLive, status: "completed" }] });
  expect(registry.get(details.turnSubagentsAtom(ref))).toBeNull();
  dispose();
  registry.dispose();
});

it("reconciles the agents pill with each child conversation through the app's atoms", () => {
  const run = (id: string, ordinal: number) => ({
    id: RunId.make(id),
    threadId: v2Projection.thread.id,
    ordinal,
    providerInstanceId: v2Projection.thread.providerInstanceId,
    modelSelection: v2Projection.thread.modelSelection,
    providerThreadId: null,
    userMessageId: MessageId.make(`message-${ordinal}`),
    rootNodeId: null,
    activeAttemptId: null,
    status: "completed" as const,
    requestedAt: v2Now,
    startedAt: v2Now,
    completedAt: v2Now,
    checkpointId: null,
    contextHandoffId: null,
  });
  const childThreadId = ThreadId.make("thread-reconciled-child");
  const task: OrchestrationV2ThreadProjection["subagents"][number] = {
    id: NodeId.make("older-task"),
    threadId: v2Projection.thread.id,
    runId: RunId.make("earlier-run"),
    parentNodeId: NodeId.make("root"),
    origin: "app_owned",
    createdBy: "agent",
    driver: ProviderDriverKind.make("codex"),
    providerInstanceId: v2Projection.thread.providerInstanceId,
    providerThreadId: null,
    childThreadId,
    nativeTaskRef: null,
    prompt: "Keep working",
    title: "Older worker",
    model: null,
    status: "running",
    result: null,
    startedAt: v2Now,
    completedAt: null,
    updatedAt: v2Now,
  };
  // The newer run spawned its own agent, so it is the roster's run and the
  // older task only belongs while its child is working.
  const current: OrchestrationV2ThreadProjection["subagents"][number] = {
    ...task,
    id: NodeId.make("current-task"),
    runId: RunId.make("latest-run"),
    childThreadId: ThreadId.make("thread-current-child"),
    status: "completed",
    result: "Done",
    updatedAt: DateTime.add(v2Now, { seconds: 5 }),
  };
  const projection: OrchestrationV2ThreadProjection = {
    ...v2Projection,
    runs: [run("earlier-run", 1), run("latest-run", 2)],
    subagents: [task, current],
  };
  const childShell = (
    status: OrchestrationV2ThreadShell["status"],
    overrides: Partial<OrchestrationV2ThreadShell> = {},
  ): OrchestrationV2ThreadShell => ({
    ...v2ThreadShell,
    id: childThreadId,
    lineage: {
      rootThreadId: v2ThreadShell.id,
      parentThreadId: v2Projection.thread.id,
      relationshipToParent: "subagent",
    },
    latestRunId: RunId.make("child-run"),
    status,
    ...overrides,
  });
  const snapshot = Atom.make<OrchestrationV2ShellSnapshot | null>({
    ...v2ShellSnapshot,
    threads: [v2ThreadShell, childShell("completed")],
  });
  const shells = createEnvironmentThreadShellAtoms({
    catalogValueAtom: Atom.make({ isReady: true, entries: new Map() }),
    snapshotAtom: () => snapshot,
  });
  const source = Atom.make(
    AsyncResult.success(
      threadState({ data: Option.some(projection), status: "live", error: Option.none() }),
    ),
  );
  const details = createEnvironmentThreadDetailAtoms(
    () => source,
    shells.childConversationLiveAtom,
  );
  const registry = AtomRegistry.make();
  const dispose = registry.mount(details.turnSubagentsAtom(ref));
  const pill = () => resolveSubagentPillSegment(registry.get(details.turnSubagentsAtom(ref)));
  const publish = (next: OrchestrationV2ThreadProjection) =>
    registry.set(
      source,
      AsyncResult.success(
        threadState({ data: Option.some(next), status: "live", error: Option.none() }),
      ),
    );
  const setChild = (shell: OrchestrationV2ThreadShell) =>
    registry.set(snapshot, { ...v2ShellSnapshot, threads: [v2ThreadShell, shell] });

  // Task left running, child finished: nothing is working.
  expect(registry.get(details.turnSubagentsAtom(ref))?.subagents.map((s) => s.id)).toEqual([
    "current-task",
  ]);
  expect(pill()).toBeNull();

  // The child starts working again: the pill counts it.
  setChild(childShell("running"));
  const working = registry.get(details.turnSubagentsAtom(ref));
  expect(working?.liveCount).toBe(1);
  expect(pill()?.label).toBe("1/2");

  // Child-only churn and unrelated parent updates keep the same value.
  setChild(childShell("running", { updatedAt: DateTime.add(v2Now, { seconds: 9 }), itemCount: 4 }));
  expect(registry.get(details.turnSubagentsAtom(ref))).toBe(working);
  publish({ ...projection, turnItems: [...v2Projection.turnItems] });
  expect(registry.get(details.turnSubagentsAtom(ref))).toBe(working);

  // The task completes while the child runs a follow-up: still one working.
  publish({
    ...projection,
    subagents: [{ ...task, status: "completed", result: "Old answer" }, current],
  });
  const followUp = registry
    .get(details.turnSubagentsAtom(ref))
    ?.subagents.find((subagent) => subagent.id === task.id);
  expect(followUp?.status).toBe("running");
  expect(followUp?.result).toBeNull();
  expect(pill()?.label).toBe("1/2");

  // The follow-up ends: the earlier task's history leaves the newer roster.
  setChild(childShell("completed"));
  expect(registry.get(details.turnSubagentsAtom(ref))?.subagents.map((s) => s.id)).toEqual([
    "current-task",
  ]);
  expect(pill()).toBeNull();
  dispose();
  registry.dispose();
});

it("keeps worktree and pending requests stable during output updates, then reflects resolution", () => {
  const projection: OrchestrationV2ThreadProjection = {
    ...v2Projection,
    thread: { ...v2Projection.thread, worktreePath: "/workspace/task" },
    runtimeRequests: [
      {
        id: RuntimeRequestId.make("approval"),
        nodeId: NodeId.make("approval-node"),
        providerTurnId: null,
        nativeRequestRef: null,
        kind: "command",
        status: "pending",
        responseCapability: { type: "not_resumable", reason: "Provider exited" },
        createdAt: v2Now,
        resolvedAt: null,
      },
    ],
  };
  const source = Atom.make(
    AsyncResult.success(
      threadState({ data: Option.some(projection), status: "live", error: Option.none() }),
    ),
  );
  const details = createEnvironmentThreadDetailAtoms(() => source, withoutChildConversations);
  const registry = AtomRegistry.make();
  const dispose = registry.mount(details.pendingRequestsAtom(ref));
  const before = registry.get(details.pendingRequestsAtom(ref));
  expect(before?.approvals).toHaveLength(1);
  const streaming: OrchestrationV2ThreadProjection = {
    ...projection,
    turnItems: [
      {
        id: TurnItemId.make("output"),
        threadId: projection.thread.id,
        runId: null,
        nodeId: null,
        providerThreadId: null,
        providerTurnId: null,
        nativeItemRef: null,
        parentItemId: null,
        ordinal: 1,
        status: "running",
        title: null,
        startedAt: v2Now,
        completedAt: null,
        updatedAt: v2Now,
        type: "command_execution",
        input: "pwd",
        output: "new output",
        exitCode: undefined,
      },
    ],
  };
  registry.set(
    source,
    AsyncResult.success(
      threadState({ data: Option.some(streaming), status: "live", error: Option.none() }),
    ),
  );
  expect(registry.get(details.pendingRequestsAtom(ref))).toBe(before);
  expect(registry.get(details.worktreePathAtom(ref))).toBe("/workspace/task");
  registry.set(
    source,
    AsyncResult.success(
      threadState({
        data: Option.some({
          ...streaming,
          thread: { ...projection.thread, worktreePath: "/workspace/moved" },
          runtimeRequests: projection.runtimeRequests.map((request) => ({
            ...request,
            status: "resolved",
            resolvedAt: v2Now,
          })),
        }),
        status: "live",
        error: Option.none(),
      }),
    ),
  );
  expect(registry.get(details.pendingRequestsAtom(ref))?.approvals).toEqual([]);
  expect(registry.get(details.worktreePathAtom(ref))).toBe("/workspace/moved");
  dispose();
  registry.dispose();
});
