import {
  CommandId,
  EventId,
  MessageId,
  type OrchestrationV2DomainEvent,
  type StopNoticeDeclaration,
  type ThreadId,
} from "@t3tools/contracts";
import { derivePendingBackgroundWork } from "@t3tools/shared/orchestrationV2PendingBackgroundWork";
import * as DateTime from "effect/DateTime";
import * as Effect from "effect/Effect";
import * as Option from "effect/Option";

import type * as EffectOutbox from "./EffectOutbox.ts";
import type * as ProjectionStore from "./ProjectionStore.ts";
import {
  planStopNotice,
  stopNoticeTriggers,
  type StopNoticeEffect,
  type StopNoticeTriggers,
} from "./StopNoticePlanner.ts";

/**
 * Turns committed lifecycle events into the thread's stop-notice record and
 * its outbox rows. EventSink runs this inside the same transaction as every
 * write, after the write's events reached the projections, so run
 * finalization, provider events, crash recovery and commands all pass through
 * it and a stop is durable before any notifier runs.
 */

export function stopNoticeOutboxEffect(
  threadId: ThreadId,
  effect: StopNoticeEffect,
): EffectOutbox.PendingOrchestrationEffectV2 {
  // One id per thread, episode and operation: every route that asks for this
  // stop shares the row, so a retry or a second request cannot send twice.
  const key = `stop-notice.deliver:${effect.operation}:${threadId}:${effect.episodeId}`;
  return {
    id: `effect:${key}`,
    commandId: CommandId.make(`command:effect:${key}`),
    threadId,
    request:
      effect.operation === "stop"
        ? {
            type: "stop-notice.deliver",
            operation: "stop",
            episodeId: effect.episodeId,
            request: effect.request,
          }
        : {
            type: "stop-notice.deliver",
            operation: "resume",
            episodeId: effect.episodeId,
            request: effect.request,
          },
  };
}

const BACKGROUND_TURN_ITEM_TYPES = ["command_execution", "dynamic_tool", "subagent"] as const;

/** Plans one thread against its committed projection. Null when nothing changes. */
export const planThreadStopNotice = Effect.fnUntraced(function* (input: {
  readonly projectionStore: ProjectionStore.ProjectionStoreV2["Service"];
  readonly effectOutbox: EffectOutbox.EffectOutboxV2["Service"];
  readonly defaultOwner: string | null;
  readonly threadId: ThreadId;
  readonly triggers: StopNoticeTriggers;
  /** Effects committed with these events, which the outbox does not show yet. */
  readonly plannedEffects: ReadonlyArray<EffectOutbox.PendingOrchestrationEffectV2>;
}) {
  const { projectionStore, effectOutbox, threadId, triggers } = input;
  const shell = yield* projectionStore.getThreadRecords(threadId, ["runs"]);
  if (shell.thread.deletedAt !== null) return null;
  const notice = shell.thread.stopNotice ?? null;
  // The episode's own message is enough once an episode is open; only the
  // first evaluation needs every user message to find the latest objective.
  const { messages } = yield* projectionStore.getThreadRecords(
    threadId,
    ["messages"],
    notice === null
      ? { messageRoles: ["user"] }
      : { messageRoles: ["user"], messageIds: [MessageId.make(notice.episodeId)] },
  );
  const records = yield* projectionStore.getThreadRecords(
    threadId,
    ["subagents", "runtimeRequests", "providerThreads", "turnItems"],
    {
      turnItemTypes: [...BACKGROUND_TURN_ITEM_TYPES],
      turnItemStatuses: ["pending", "running", "waiting"],
    },
  );
  const runs = shell.runs;
  const latestRun = runs.toSorted((left, right) => right.ordinal - left.ordinal)[0];
  const pendingBackgroundWork =
    derivePendingBackgroundWork({
      latestRun,
      providerThreads: records.providerThreads,
      turnItems: records.turnItems,
      activeProviderThreadId: shell.thread.activeProviderThreadId,
      runs,
      pullRequests: shell.thread.pullRequests,
    }).length > 0;
  const continuationId =
    latestRun === undefined ? null : `effect:restart-continuation:${latestRun.id}`;
  const pendingRestartContinuation =
    continuationId !== null &&
    (input.plannedEffects.some((effect) => effect.id === continuationId) ||
      Option.exists(
        yield* effectOutbox.get(continuationId),
        (effect) => effect.status === "pending" || effect.status === "running",
      ));
  const now = yield* DateTime.now;
  const planned = planStopNotice({
    projection: {
      thread: shell.thread,
      runs,
      messages,
      subagents: records.subagents,
      runtimeRequests: records.runtimeRequests,
    },
    triggers,
    facts: {
      now: DateTime.formatIso(now),
      defaultOwner: input.defaultOwner,
      pendingBackgroundWork,
      pendingRestartContinuation,
    },
  });
  if (planned === null) return null;
  return {
    thread: { ...shell.thread, stopNotice: planned.notice },
    occurredAt: now,
    effects: planned.effects.map((effect) => stopNoticeOutboxEffect(threadId, effect)),
  };
});

/**
 * The stop-notice events and effects one committed write implies. `eventKey`
 * makes the derived event ids unique: callers pass the write's last sequence.
 */
export const deriveStopNotices = Effect.fnUntraced(function* (input: {
  readonly projectionStore: ProjectionStore.ProjectionStoreV2["Service"];
  readonly effectOutbox: EffectOutbox.EffectOutboxV2["Service"];
  readonly defaultOwner: string | null;
  readonly events: ReadonlyArray<OrchestrationV2DomainEvent>;
  readonly plannedEffects: ReadonlyArray<EffectOutbox.PendingOrchestrationEffectV2>;
  readonly eventKey: string;
  readonly declaration?: { readonly threadId: ThreadId; readonly value: StopNoticeDeclaration };
}) {
  const events: Array<OrchestrationV2DomainEvent> = [];
  const effects: Array<EffectOutbox.PendingOrchestrationEffectV2> = [];
  const threadIds = [...new Set(input.events.map((event) => event.threadId))];
  if (input.declaration !== undefined && !threadIds.includes(input.declaration.threadId)) {
    threadIds.push(input.declaration.threadId);
  }
  for (const threadId of threadIds) {
    const found = stopNoticeTriggers(threadId, input.events);
    const declaration =
      input.declaration?.threadId === threadId ? input.declaration.value : undefined;
    if (found === null && declaration === undefined) continue;
    const triggers: StopNoticeTriggers = {
      ...(found ?? {
        terminalRuns: [],
        pendingRequests: [],
        resolvedRequestIds: new Set(),
        subagentEnded: false,
        objectiveMessages: [],
      }),
      ...(declaration === undefined ? {} : { declaration }),
    };
    const planned = yield* planThreadStopNotice({
      projectionStore: input.projectionStore,
      effectOutbox: input.effectOutbox,
      defaultOwner: input.defaultOwner,
      threadId,
      triggers,
      plannedEffects: [...input.plannedEffects, ...effects],
    });
    if (planned === null) continue;
    events.push({
      id: EventId.make(`event:stop-notice:${input.eventKey}:${threadId}`),
      type: "thread.stop-notice-updated",
      threadId,
      providerInstanceId: planned.thread.providerInstanceId,
      occurredAt: planned.occurredAt,
      payload: planned.thread,
    });
    effects.push(...planned.effects);
  }
  return { events, effects };
});
