import * as Schema from "effect/Schema";

import {
  IsoDateTime,
  NonNegativeInt,
  PositiveInt,
  RunId,
  RuntimeRequestId,
  ThreadId,
  TrimmedNonEmptyString,
} from "./baseSchemas.ts";

/**
 * Why a work episode ended. Native finalization only ever records the
 * dispositions it can observe (FAILED, CANCELED, WAITING_INPUT,
 * WAITING_APPROVAL, UNDECLARED); every other value comes from the agent's own
 * `t3_stop_report`. Upper-case words joined by `_` or `-`, so integrations can
 * keep their own vocabulary (for example HOLD-DRAFT) without a T3 release.
 */
export const StopDisposition = TrimmedNonEmptyString.check(
  Schema.isPattern(/^[A-Z][A-Z0-9_-]{1,39}$/u),
);
export type StopDisposition = typeof StopDisposition.Type;

/** What still carries the accepted work when a run ends. Anything but `none` is not a stop. */
export const StopContinuation = Schema.Literals([
  "children",
  "native_event",
  "queued_work",
  "none",
]);
export type StopContinuation = typeof StopContinuation.Type;

export const StopTrigger = Schema.Literals([
  "run_completed",
  "run_failed",
  "run_interrupted",
  "run_cancelled",
  "runtime_request",
]);
export type StopTrigger = typeof StopTrigger.Type;

/**
 * Delivery of the stop event, kept apart from settlement. `accepted` means the
 * notifier reported the receiver took the event but proved no recipient run;
 * only `delivered` carries that proof. `handed_back` means the stop belongs to
 * the opener through a durable binding and no own event was sent.
 */
export const StopDeliveryState = Schema.Literals([
  "pending",
  "accepted",
  "delivered",
  "rejected",
  "failed",
  "unavailable",
  "handed_back",
]);
export type StopDeliveryState = typeof StopDeliveryState.Type;

export const StopNoticeDeclaration = Schema.Struct({
  disposition: StopDisposition,
  owner: Schema.NullOr(TrimmedNonEmptyString),
  resultPath: Schema.NullOr(TrimmedNonEmptyString),
  requiredAction: Schema.NullOr(TrimmedNonEmptyString),
  runId: Schema.NullOr(RunId),
  declaredAt: IsoDateTime,
});
export type StopNoticeDeclaration = typeof StopNoticeDeclaration.Type;

/**
 * Who opened this work. Only a `delegated_task` binding, whose native task
 * result is a durable handback, lets the opener own the stop. A thread that
 * another thread launched or messaged (`sender`) still sends its own notice;
 * its opener is kept as evidence only.
 */
export const StopNoticeOpener = Schema.Struct({
  threadId: ThreadId,
  binding: Schema.Literals(["delegated_task", "sender"]),
  /** The delegated task whose result hands the stop back; null when none is registered. */
  handbackId: Schema.NullOr(TrimmedNonEmptyString),
});
export type StopNoticeOpener = typeof StopNoticeOpener.Type;

/**
 * Where a stop's `resultPath` came from. `declared` is the path the agent
 * named in its `t3_stop_report`. `native_record` is the stop record T3 writes
 * under its own state when no path was named: stop metadata and a transcript
 * reference, never an agent RESULT and never a claim that the work is done.
 */
export const StopResultOrigin = Schema.Literals(["declared", "native_record"]);
export type StopResultOrigin = typeof StopResultOrigin.Type;

/** The owner a stop names when neither the thread nor the server named one. The notifier resolves it on. */
export const STOP_NOTICE_FALLBACK_OWNER = "Sats";

export const StopNoticeStop = Schema.Struct({
  disposition: StopDisposition,
  source: Schema.Literals(["explicit", "native"]),
  trigger: StopTrigger,
  runId: Schema.NullOr(RunId),
  runtimeRequestId: Schema.NullOr(RuntimeRequestId),
  owner: TrimmedNonEmptyString,
  resultPath: Schema.NullOr(TrimmedNonEmptyString),
  resultOrigin: Schema.NullOr(StopResultOrigin),
  requiredAction: Schema.NullOr(TrimmedNonEmptyString),
  opener: Schema.NullOr(StopNoticeOpener),
  stoppedAt: IsoDateTime,
});
export type StopNoticeStop = typeof StopNoticeStop.Type;

export const StopNoticeDelivery = Schema.Struct({
  state: StopDeliveryState,
  attempts: NonNegativeInt,
  /** The notifier's own state word, such as WEBHOOK_ACCEPTED or PENDING. */
  notifierState: Schema.NullOr(Schema.String),
  /** The notifier's evidence class: absent, local_only, attempted, rejected, accepted or recipient_run. */
  deliveryEvidence: Schema.NullOr(Schema.String),
  eventId: Schema.NullOr(Schema.String),
  generation: Schema.NullOr(PositiveInt),
  recipientRunId: Schema.NullOr(Schema.String),
  lastError: Schema.NullOr(Schema.String),
  updatedAt: IsoDateTime,
});
export type StopNoticeDelivery = typeof StopNoticeDelivery.Type;

export const StopNoticeResume = Schema.Struct({
  /** Null for a thread's first recorded episode. */
  previousEpisodeId: Schema.NullOr(TrimmedNonEmptyString),
  state: Schema.Literals(["pending", "allocated", "failed", "unavailable"]),
  attempts: NonNegativeInt,
  generation: Schema.NullOr(PositiveInt),
  lastError: Schema.NullOr(Schema.String),
  updatedAt: IsoDateTime,
});
export type StopNoticeResume = typeof StopNoticeResume.Type;

/** A stopped episode whose delivery may still settle after the thread moved on. */
export const StopNoticeStoppedEpisode = Schema.Struct({
  episodeId: TrimmedNonEmptyString,
  stop: StopNoticeStop,
  delivery: StopNoticeDelivery,
});
export type StopNoticeStoppedEpisode = typeof StopNoticeStoppedEpisode.Type;

/**
 * The thread's current work episode and its stop event. An episode opens on an
 * accepted objective message (its id) or on the answer to a pending question or
 * approval (`runtime-request:<id>`); wakes, retries and reads never open one.
 */
export const StopNotice = Schema.Struct({
  episodeId: TrimmedNonEmptyString,
  episodeOrigin: Schema.Literals(["message", "runtime_request"]),
  /** When the episode's message or answer was accepted; older messages never reopen it. */
  episodeStartedAt: IsoDateTime,
  /** Last time a run ended while work continued, and what carried it. */
  continuation: Schema.NullOr(
    Schema.Struct({
      kind: StopContinuation,
      runId: Schema.NullOr(RunId),
      evaluatedAt: IsoDateTime,
    }),
  ),
  declaration: Schema.NullOr(StopNoticeDeclaration),
  stop: Schema.NullOr(StopNoticeStop),
  delivery: Schema.NullOr(StopNoticeDelivery),
  resume: Schema.NullOr(StopNoticeResume),
  previous: Schema.NullOr(StopNoticeStoppedEpisode),
});
export type StopNotice = typeof StopNotice.Type;

/**
 * The bodies handed to the stop notifier on stdin, frozen when the stop or
 * resume is recorded. Field names follow the notifier's snake_case seam. They
 * name roles and ids only; no secret, route or command is ever part of them.
 */
export const StopNotifierStopRequest = Schema.Struct({
  thread_id: ThreadId,
  episode_message_id: TrimmedNonEmptyString,
  owner: TrimmedNonEmptyString,
  disposition: StopDisposition,
  continuation: StopContinuation,
  result_path: Schema.NullOr(TrimmedNonEmptyString),
  required_action: Schema.NullOr(TrimmedNonEmptyString),
  opener_thread_id: Schema.optional(ThreadId),
  handback_id: Schema.optional(TrimmedNonEmptyString),
});
export type StopNotifierStopRequest = typeof StopNotifierStopRequest.Type;

/** Accepted input resumed a stopped episode: the notifier allocates the next generation once. */
export const StopNotifierResumeRequest = Schema.Struct({
  thread_id: ThreadId,
  episode_message_id: TrimmedNonEmptyString,
  owner: Schema.NullOr(TrimmedNonEmptyString),
});
export type StopNotifierResumeRequest = typeof StopNotifierResumeRequest.Type;

/**
 * The stop record T3 writes under its own state when a stop names no result
 * path, so the notifier's `result_path` always names a real file. Frozen in the
 * stop's outbox row: every replay writes the same bytes to the same path before
 * the notifier runs. It holds ids and the stop's own fields only, no secret and
 * no server configuration.
 */
export const StopNativeRecord = Schema.Struct({
  path: TrimmedNonEmptyString,
  body: Schema.Struct({
    schema: Schema.Literal("t3-native-stop-record/v1"),
    note: Schema.String,
    threadId: ThreadId,
    episodeId: TrimmedNonEmptyString,
    episodeOrigin: Schema.Literals(["message", "runtime_request"]),
    disposition: StopDisposition,
    source: Schema.Literals(["explicit", "native"]),
    trigger: StopTrigger,
    runId: Schema.NullOr(RunId),
    runtimeRequestId: Schema.NullOr(RuntimeRequestId),
    owner: TrimmedNonEmptyString,
    requiredAction: Schema.NullOr(TrimmedNonEmptyString),
    opener: Schema.NullOr(StopNoticeOpener),
    stoppedAt: IsoDateTime,
    /** Where the work itself is: the thread's own transcript, read through T3. */
    transcript: Schema.Struct({
      threadId: ThreadId,
      runId: Schema.NullOr(RunId),
      read: Schema.String,
    }),
  }),
});
export type StopNativeRecord = typeof StopNativeRecord.Type;

/** Notifier receipt for one stop or resume request, as the delivery effect records it. */
export const StopNotifierReceipt = Schema.Struct({
  operation: Schema.Literals(["stop", "resume"]),
  episodeId: TrimmedNonEmptyString,
  /** Transport-level outcome; `retry` keeps the outbox row and the same key. */
  outcome: Schema.Literals(["recorded", "retry", "unavailable"]),
  notifierState: Schema.NullOr(Schema.String),
  deliveryEvidence: Schema.NullOr(Schema.String),
  eventId: Schema.NullOr(Schema.String),
  generation: Schema.NullOr(PositiveInt),
  recipientRunId: Schema.NullOr(Schema.String),
  error: Schema.NullOr(Schema.String),
  final: Schema.Boolean,
});
export type StopNotifierReceipt = typeof StopNotifierReceipt.Type;
