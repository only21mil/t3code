import type {
  OrchestrationV2AppThread,
  OrchestrationV2ConversationMessage,
  OrchestrationV2DomainEvent,
  OrchestrationV2Run,
  OrchestrationV2RuntimeRequest,
  OrchestrationV2Subagent,
  RuntimeRequestId,
  StopContinuation,
  StopNativeRecord,
  StopNotice,
  StopNoticeDeclaration,
  StopNoticeDelivery,
  StopNoticeOpener,
  StopNoticeStop,
  StopNotifierReceipt,
  StopNotifierResumeRequest,
  StopNotifierStopRequest,
  StopTrigger,
  ThreadId,
} from "@t3tools/contracts";
import { STOP_NOTICE_FALLBACK_OWNER } from "@t3tools/contracts";
import * as DateTime from "effect/DateTime";
import { threadRelayContentSha256 } from "@t3tools/shared/threadRelay";

/**
 * Decides, inside the command that ends a run or opens a question, whether the
 * thread's work episode stopped. The orchestrator commits the result with that
 * command, so a stop is durably recorded before any notifier is invoked, and an
 * explicit `t3_stop_report` and native finalization resolve to the same episode
 * and the same outbox row. Nothing here polls or waits: every evaluation is
 * driven by a committed lifecycle event.
 */

export type StopNoticeEffect =
  | {
      readonly operation: "stop";
      readonly episodeId: string;
      readonly request: StopNotifierStopRequest;
      readonly nativeRecord?: StopNativeRecord | undefined;
    }
  | {
      readonly operation: "resume";
      readonly episodeId: string;
      readonly request: StopNotifierResumeRequest;
    };

export type StopNoticeRun = Pick<
  OrchestrationV2Run,
  "id" | "ordinal" | "status" | "delegatedCompletion" | "delegatedTaskId"
>;
export type StopNoticeMessage = Pick<
  OrchestrationV2ConversationMessage,
  | "id"
  | "role"
  | "notification"
  | "delegatedCompletion"
  | "createdBy"
  | "createdAt"
  | "senderThreadId"
>;
export type StopNoticeRuntimeRequest = Pick<
  OrchestrationV2RuntimeRequest,
  "id" | "kind" | "status" | "createdAt"
>;

export interface StopNoticeProjection {
  readonly thread: Pick<
    OrchestrationV2AppThread,
    "id" | "lineage" | "creationSource" | "limitRecovery" | "stopNotice"
  >;
  readonly runs: ReadonlyArray<StopNoticeRun>;
  /** User-role messages; the planner reads episode messages and their senders. */
  readonly messages: ReadonlyArray<StopNoticeMessage>;
  readonly subagents: ReadonlyArray<Pick<OrchestrationV2Subagent, "status">>;
  readonly runtimeRequests: ReadonlyArray<StopNoticeRuntimeRequest>;
}

export interface StopNoticeFacts {
  readonly now: string;
  readonly defaultOwner: string | null;
  /**
   * Server-owned directory for native stop records. Null leaves a stop with no
   * declared path without one, which the notifier refuses.
   */
  readonly nativeRecordDir: string | null;
  /** Post-turn background work, pull request watches and the like still wake this thread. */
  readonly pendingBackgroundWork: boolean;
  /** A restart continuation will carry the last run's work. */
  readonly pendingRestartContinuation: boolean;
}

export interface StopNoticeTriggers {
  readonly terminalRuns: ReadonlyArray<StopNoticeRun>;
  readonly pendingRequests: ReadonlyArray<StopNoticeRuntimeRequest>;
  readonly resolvedRequestIds: ReadonlySet<RuntimeRequestId>;
  readonly subagentEnded: boolean;
  readonly objectiveMessages: ReadonlyArray<StopNoticeMessage>;
  readonly declaration?: StopNoticeDeclaration | undefined;
}

const TERMINAL_RUN_TRIGGERS: Partial<Record<OrchestrationV2Run["status"], StopTrigger>> = {
  completed: "run_completed",
  failed: "run_failed",
  interrupted: "run_interrupted",
  cancelled: "run_cancelled",
};
const RUNNING_RUN_STATUSES = new Set<OrchestrationV2Run["status"]>([
  "starting",
  "running",
  "waiting",
]);
const QUEUED_RUN_STATUSES = new Set<OrchestrationV2Run["status"]>(["preparing", "queued"]);
const ACTIVE_SUBAGENT_STATUSES = new Set<OrchestrationV2Subagent["status"]>([
  "pending",
  "running",
  "waiting",
]);
const TERMINAL_SUBAGENT_STATUSES = new Set<OrchestrationV2Subagent["status"]>([
  "completed",
  "failed",
  "cancelled",
  "interrupted",
]);

/** A message that starts or resumes accepted work. Wakes and server continuations never do. */
export function isObjectiveMessage(message: StopNoticeMessage): boolean {
  return (
    message.role === "user" &&
    message.notification === undefined &&
    message.delegatedCompletion === undefined &&
    message.createdBy !== "system"
  );
}

/** A pending request only a person can answer. Dynamic tool calls are answered by the client. */
function waitingDisposition(request: Pick<StopNoticeRuntimeRequest, "kind">): string | null {
  if (request.kind === "dynamic_tool_call") return null;
  if (
    request.kind === "user_input" ||
    request.kind === "auth_refresh" ||
    request.kind === "mcp-elicitation"
  ) {
    return "WAITING_INPUT";
  }
  return "WAITING_APPROVAL";
}

/** The lifecycle events in one command that can end or reopen an episode. */
export function stopNoticeTriggers(
  threadId: ThreadId,
  events: ReadonlyArray<OrchestrationV2DomainEvent>,
): StopNoticeTriggers | null {
  const terminalRuns: Array<StopNoticeRun> = [];
  const pendingRequests: Array<StopNoticeRuntimeRequest> = [];
  const resolvedRequestIds = new Set<RuntimeRequestId>();
  const objectiveMessages: Array<StopNoticeMessage> = [];
  let subagentEnded = false;
  for (const event of events) {
    if (event.threadId !== threadId) continue;
    switch (event.type) {
      case "run.updated":
        if (TERMINAL_RUN_TRIGGERS[event.payload.status] !== undefined) {
          terminalRuns.push(event.payload);
        }
        break;
      case "runtime-request.updated":
        if (event.payload.status === "pending" && waitingDisposition(event.payload) !== null) {
          pendingRequests.push(event.payload);
        } else if (event.payload.status === "resolved") {
          resolvedRequestIds.add(event.payload.id);
        }
        break;
      case "subagent.updated":
        if (TERMINAL_SUBAGENT_STATUSES.has(event.payload.status)) subagentEnded = true;
        break;
      case "message.updated":
        if (isObjectiveMessage(event.payload)) objectiveMessages.push(event.payload);
        break;
    }
  }
  return terminalRuns.length === 0 &&
    pendingRequests.length === 0 &&
    resolvedRequestIds.size === 0 &&
    objectiveMessages.length === 0 &&
    !subagentEnded
    ? null
    : { terminalRuns, pendingRequests, resolvedRequestIds, subagentEnded, objectiveMessages };
}

const epoch = (iso: string) => Date.parse(iso);
const messageIso = (message: StopNoticeMessage) => DateTime.formatIso(message.createdAt);

function latestObjectiveMessage(
  messages: ReadonlyArray<StopNoticeMessage>,
): StopNoticeMessage | undefined {
  return messages
    .filter(isObjectiveMessage)
    .toSorted((left, right) => epoch(messageIso(right)) - epoch(messageIso(left)))[0];
}

function openEpisode(input: {
  readonly episodeId: string;
  readonly origin: StopNotice["episodeOrigin"];
  readonly startedAt: string;
  readonly before: StopNotice | null;
  readonly now: string;
}): StopNotice {
  const { before } = input;
  const previous =
    before?.stop != null && before.delivery !== null
      ? { episodeId: before.episodeId, stop: before.stop, delivery: before.delivery }
      : (before?.previous ?? null);
  return {
    episodeId: input.episodeId,
    episodeOrigin: input.origin,
    episodeStartedAt: input.startedAt,
    continuation: null,
    declaration: null,
    stop: null,
    delivery: null,
    resume: {
      previousEpisodeId: before?.episodeId ?? null,
      state: "pending",
      attempts: 0,
      generation: null,
      lastError: null,
      updatedAt: input.now,
    },
    previous,
  };
}

function defaultRequiredAction(disposition: string): string | null {
  switch (disposition) {
    case "DONE":
      return null;
    case "WAITING_INPUT":
      return "Answer the pending question in this thread.";
    case "WAITING_APPROVAL":
      return "Decide the pending approval in this thread.";
    case "FAILED":
      return "The run failed. Read the thread's last error and decide whether to rerun.";
    case "CANCELED":
      return "The run was stopped before it finished. Decide whether to resume it.";
    case "UNDECLARED":
      return "The run ended without a stop report. Read the thread's last message.";
    default:
      return "Read the thread's stop report and act on it.";
  }
}

function continuationOf(
  projection: StopNoticeProjection,
  facts: StopNoticeFacts,
): StopContinuation {
  if (projection.subagents.some((subagent) => ACTIVE_SUBAGENT_STATUSES.has(subagent.status))) {
    return "children";
  }
  if (
    facts.pendingRestartContinuation ||
    projection.runs.some((run) => QUEUED_RUN_STATUSES.has(run.status))
  ) {
    return "queued_work";
  }
  if (
    facts.pendingBackgroundWork ||
    projection.thread.limitRecovery?.autoResume === true ||
    projection.runs.some(
      (run) =>
        run.delegatedCompletion?.disposition === "open" &&
        run.delegatedCompletion.delivery !== null,
    )
  ) {
    return "native_event";
  }
  return "none";
}

function openerOf(
  projection: StopNoticeProjection,
  notice: StopNotice,
  latestRun: StopNoticeRun | undefined,
): StopNoticeOpener | null {
  const lineage = projection.thread.lineage;
  if (lineage.relationshipToParent === "subagent" && lineage.parentThreadId !== null) {
    return {
      threadId: lineage.parentThreadId,
      binding: "delegated_task",
      handbackId: latestRun?.delegatedTaskId ?? null,
    };
  }
  if (notice.episodeOrigin !== "message") return null;
  const episodeMessage = projection.messages.find((message) => message.id === notice.episodeId);
  if (episodeMessage?.senderThreadId === undefined) return null;
  return { threadId: episodeMessage.senderThreadId, binding: "sender", handbackId: null };
}

const shortHash = (value: string) => threadRelayContentSha256(value).slice(0, 32);

/** One file per thread and episode, so a replayed stop rewrites the same path. */
export function nativeStopRecordPath(directory: string, threadId: ThreadId, episodeId: string) {
  return `${directory.replace(/[\\/]+$/u, "")}/${shortHash(threadId)}/${shortHash(episodeId)}.json`;
}

function nativeStopRecord(
  path: string,
  threadId: ThreadId,
  notice: StopNotice,
  stop: StopNoticeStop,
): StopNativeRecord {
  return {
    path,
    body: {
      schema: "t3-native-stop-record/v1",
      note: "T3 wrote this record because the thread stopped without naming a result path. It is not the agent's RESULT and does not say the work is done. Read the thread's transcript for the work itself.",
      threadId,
      episodeId: notice.episodeId,
      episodeOrigin: notice.episodeOrigin,
      disposition: stop.disposition,
      source: stop.source,
      trigger: stop.trigger,
      runId: stop.runId,
      runtimeRequestId: stop.runtimeRequestId,
      owner: stop.owner,
      requiredAction: stop.requiredAction,
      opener: stop.opener,
      stoppedAt: stop.stoppedAt,
      transcript: {
        threadId,
        runId: stop.runId,
        read: `t3_thread_read {"threadId":${JSON.stringify(threadId)}}`,
      },
    },
  };
}

function resumeEffect(threadId: ThreadId, notice: StopNotice, owner: string): StopNoticeEffect {
  return {
    operation: "resume",
    episodeId: notice.episodeId,
    request: { thread_id: threadId, episode_message_id: notice.episodeId, owner },
  };
}

/**
 * Next stop-notice state for one committed command, or null when nothing
 * changes. Resume effects come before the stop they precede: both run in one
 * per-thread lane, so the notifier binds the episode before its stop arrives.
 */
export function planStopNotice(input: {
  readonly projection: StopNoticeProjection;
  readonly triggers: StopNoticeTriggers;
  readonly facts: StopNoticeFacts;
}): { readonly notice: StopNotice; readonly effects: ReadonlyArray<StopNoticeEffect> } | null {
  const { projection, triggers, facts } = input;
  const thread = projection.thread;
  // A provider-native subagent's conversation belongs to its provider and its parent.
  if (thread.lineage.relationshipToParent === "subagent" && thread.creationSource === "provider") {
    return null;
  }
  const before = thread.stopNotice ?? null;
  const effects: Array<StopNoticeEffect> = [];
  const owner = triggers.declaration?.owner ?? facts.defaultOwner ?? STOP_NOTICE_FALLBACK_OWNER;

  let notice = before;
  const newest = latestObjectiveMessage(triggers.objectiveMessages);
  // Messages accepted in the same millisecond are ordered by arrival; the
  // episode just left is never reopened by an update to its own message.
  if (
    newest !== undefined &&
    newest.id !== notice?.episodeId &&
    newest.id !== notice?.resume?.previousEpisodeId &&
    (notice === null || epoch(messageIso(newest)) >= epoch(notice.episodeStartedAt))
  ) {
    notice = openEpisode({
      episodeId: newest.id,
      origin: "message",
      startedAt: messageIso(newest),
      before: notice,
      now: facts.now,
    });
    effects.push(resumeEffect(thread.id, notice, owner));
  } else if (
    notice?.stop?.runtimeRequestId != null &&
    triggers.resolvedRequestIds.has(notice.stop.runtimeRequestId)
  ) {
    notice = openEpisode({
      episodeId: `runtime-request:${notice.stop.runtimeRequestId}`,
      origin: "runtime_request",
      startedAt: facts.now,
      before: notice,
      now: facts.now,
    });
    effects.push(resumeEffect(thread.id, notice, owner));
  } else if (notice === null) {
    const episode = latestObjectiveMessage(projection.messages);
    if (episode === undefined) return null;
    notice = openEpisode({
      episodeId: episode.id,
      origin: "message",
      startedAt: messageIso(episode),
      before: null,
      now: facts.now,
    });
    effects.push(resumeEffect(thread.id, notice, owner));
  }

  if (triggers.declaration !== undefined && notice.stop === null) {
    notice = { ...notice, declaration: triggers.declaration };
  }

  if (notice.stop === null) {
    const latestRun = projection.runs.toSorted((left, right) => right.ordinal - left.ordinal)[0];
    const pendingRequest = projection.runtimeRequests
      .filter((request) => request.status === "pending" && waitingDisposition(request) !== null)
      .toSorted(
        (left, right) =>
          DateTime.toEpochMillis(right.createdAt) - DateTime.toEpochMillis(left.createdAt),
      )[0];
    const running = projection.runs.some((run) => RUNNING_RUN_STATUSES.has(run.status));
    const continuation = continuationOf(projection, facts);
    let stopped: { disposition: string; trigger: StopTrigger } | null = null;
    if (pendingRequest !== undefined) {
      if (continuation === "none") {
        stopped = {
          disposition: waitingDisposition(pendingRequest) ?? "WAITING_INPUT",
          trigger: "runtime_request",
        };
      }
    } else if (!running && latestRun !== undefined) {
      const trigger = TERMINAL_RUN_TRIGGERS[latestRun.status];
      if (trigger !== undefined && continuation === "none") {
        const nativeDisposition =
          latestRun.status === "failed"
            ? "FAILED"
            : latestRun.status === "completed"
              ? "UNDECLARED"
              : "CANCELED";
        stopped = {
          disposition: notice.declaration?.disposition ?? nativeDisposition,
          trigger,
        };
      }
    }

    if (stopped !== null) {
      const declaration = notice.declaration;
      const opener = openerOf(projection, notice, latestRun);
      // Only a native delegate hands its stop back; a launched or messaged
      // thread reports for itself, so its sender is not part of the request.
      const handback = opener?.binding === "delegated_task" ? opener : null;
      const requiredAction =
        declaration?.requiredAction ?? defaultRequiredAction(stopped.disposition);
      const recordPath =
        declaration?.resultPath == null && facts.nativeRecordDir !== null
          ? nativeStopRecordPath(facts.nativeRecordDir, thread.id, notice.episodeId)
          : null;
      const stop: StopNoticeStop = {
        disposition: stopped.disposition,
        source: declaration === null ? "native" : "explicit",
        trigger: stopped.trigger,
        runId: latestRun?.id ?? null,
        runtimeRequestId: pendingRequest?.id ?? null,
        owner: declaration?.owner ?? facts.defaultOwner ?? STOP_NOTICE_FALLBACK_OWNER,
        resultPath: declaration?.resultPath ?? recordPath,
        resultOrigin:
          declaration?.resultPath != null
            ? "declared"
            : recordPath === null
              ? null
              : "native_record",
        requiredAction,
        opener,
        stoppedAt: facts.now,
      };
      const delivery: StopNoticeDelivery = {
        state: "pending",
        attempts: 0,
        notifierState: null,
        deliveryEvidence: null,
        eventId: null,
        generation: null,
        recipientRunId: null,
        lastError: null,
        updatedAt: facts.now,
      };
      notice = {
        ...notice,
        continuation: { kind: "none", runId: stop.runId, evaluatedAt: facts.now },
        stop,
        delivery,
      };
      effects.push({
        operation: "stop",
        episodeId: notice.episodeId,
        request: {
          thread_id: thread.id,
          episode_message_id: notice.episodeId,
          owner: stop.owner,
          disposition: stop.disposition,
          continuation: "none",
          result_path: stop.resultPath,
          required_action: stop.requiredAction,
          ...(handback === null ? {} : { opener_thread_id: handback.threadId }),
          ...(handback?.handbackId == null ? {} : { handback_id: handback.handbackId }),
        },
        ...(recordPath === null
          ? {}
          : { nativeRecord: nativeStopRecord(recordPath, thread.id, notice, stop) }),
      });
    } else if (
      triggers.terminalRuns.length > 0 &&
      (notice.continuation?.kind !== continuation ||
        notice.continuation.runId !== (latestRun?.id ?? null))
    ) {
      // A run ended while owned work carries on: an interim yield, recorded as
      // evidence and never sent.
      const kind: StopContinuation =
        continuation === "none" && (running || pendingRequest !== undefined)
          ? "queued_work"
          : continuation;
      notice = {
        ...notice,
        continuation: { kind, runId: latestRun?.id ?? null, evaluatedAt: facts.now },
      };
    }
  }

  return notice === before && effects.length === 0 ? null : { notice, effects };
}

function deliveryStateOf(receipt: StopNotifierReceipt): StopNoticeDelivery["state"] {
  if (receipt.outcome === "unavailable") return "unavailable";
  if (receipt.outcome === "retry") return receipt.final ? "failed" : "pending";
  switch (receipt.notifierState) {
    case "SUPPRESSED_HANDBACK":
      return "handed_back";
    case "WEBHOOK_ACCEPTED":
      return receipt.recipientRunId === null ? "accepted" : "delivered";
    case "PENDING":
      return "pending";
    case "REJECTED":
    case "CONFLICT":
    case "INVALID":
      return "rejected";
    default:
      return "failed";
  }
}

/**
 * Applies one notifier attempt to the episode it was made for, which may by
 * now be the thread's previous episode. Returns null for an episode the
 * thread no longer tracks; the outbox row still holds that attempt's error.
 */
export function applyStopNotifierReceipt(input: {
  readonly notice: StopNotice | null | undefined;
  readonly receipt: StopNotifierReceipt;
  readonly attempt: number;
  readonly now: string;
}): StopNotice | null {
  const { notice, receipt, attempt, now } = input;
  if (notice == null) return null;
  if (receipt.operation === "resume") {
    if (notice.episodeId !== receipt.episodeId) return null;
    return {
      ...notice,
      resume: {
        previousEpisodeId: notice.resume?.previousEpisodeId ?? null,
        state:
          receipt.outcome === "unavailable"
            ? "unavailable"
            : receipt.outcome === "retry"
              ? receipt.final
                ? "failed"
                : "pending"
              : receipt.generation === null
                ? "failed"
                : "allocated",
        attempts: attempt,
        generation: receipt.generation,
        lastError: receipt.error,
        updatedAt: now,
      },
    };
  }
  const delivery = (previous: StopNoticeDelivery): StopNoticeDelivery => ({
    state: deliveryStateOf(receipt),
    attempts: attempt,
    notifierState: receipt.notifierState ?? previous.notifierState,
    deliveryEvidence: receipt.deliveryEvidence ?? previous.deliveryEvidence,
    eventId: receipt.eventId ?? previous.eventId,
    generation: receipt.generation ?? previous.generation,
    recipientRunId: receipt.recipientRunId,
    lastError: receipt.error,
    updatedAt: now,
  });
  if (notice.episodeId === receipt.episodeId && notice.delivery !== null) {
    return { ...notice, delivery: delivery(notice.delivery) };
  }
  if (notice.previous?.episodeId === receipt.episodeId) {
    return {
      ...notice,
      previous: { ...notice.previous, delivery: delivery(notice.previous.delivery) },
    };
  }
  return null;
}
