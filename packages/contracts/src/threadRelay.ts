import * as Schema from "effect/Schema";

import {
  EnvironmentId,
  MessageId,
  PositiveInt,
  RunId,
  ThreadId,
  TrimmedNonEmptyString,
} from "./baseSchemas.ts";

/**
 * Relays carry one message from an initiating sender through intermediate
 * threads to a declared final thread. Each environment records only the hops
 * that reach its own threads. T3 never forwards across environments: a hop
 * into another environment is a send through that environment's own
 * authenticated route, and only that environment can read its final-target
 * message back.
 */
export const ThreadRelayId = TrimmedNonEmptyString.check(
  Schema.isMaxLength(200),
  Schema.isPattern(/^[A-Za-z0-9][A-Za-z0-9._:-]*$/u),
);
export type ThreadRelayId = typeof ThreadRelayId.Type;

export const ThreadRelayContentSha256 = Schema.String.check(Schema.isPattern(/^[0-9a-f]{64}$/u));
export type ThreadRelayContentSha256 = typeof ThreadRelayContentSha256.Type;

export const ThreadRelayTarget = Schema.Struct({
  environmentId: EnvironmentId,
  threadId: ThreadId,
});
export type ThreadRelayTarget = typeof ThreadRelayTarget.Type;

export const ThreadRelayHopRef = Schema.Struct({
  environmentId: EnvironmentId,
  threadId: ThreadId,
  messageId: MessageId,
});
export type ThreadRelayHopRef = typeof ThreadRelayHopRef.Type;

/** Persisted on every relay hop's message, so the shared identity survives retries and hops. */
export const ThreadRelayHop = Schema.Struct({
  relayId: ThreadRelayId,
  finalTarget: ThreadRelayTarget,
  hop: PositiveInt,
  /** The message this hop forwards. Verified when it is in this environment, declared otherwise. */
  previous: Schema.NullOr(ThreadRelayHopRef),
  previousVerified: Schema.Boolean,
  /** Hash of the exact text that must reach the final target, when the initiating sender declared it. */
  contentSha256: Schema.NullOr(ThreadRelayContentSha256),
});
export type ThreadRelayHop = typeof ThreadRelayHop.Type;

/**
 * `delivered`: the message is in the thread's transcript as a user turn.
 * `pending`: recorded, but queued behind other work. `dropped`: recorded, then
 * cancelled before it reached the transcript. `missing`: no such message.
 */
export const ThreadRelayHopState = Schema.Literals(["delivered", "pending", "dropped", "missing"]);
export type ThreadRelayHopState = typeof ThreadRelayHopState.Type;

export const ThreadRelayHopReceipt = Schema.Struct({
  environmentId: EnvironmentId,
  threadId: ThreadId,
  messageId: MessageId,
  hop: Schema.NullOr(PositiveInt),
  state: ThreadRelayHopState,
  runId: Schema.NullOr(RunId),
  runStatus: Schema.NullOr(Schema.String),
  contentSha256: Schema.NullOr(ThreadRelayContentSha256),
});
export type ThreadRelayHopReceipt = typeof ThreadRelayHopReceipt.Type;

export const ThreadRelayDeliveryErrorCode = Schema.Literals([
  "final_target_message_absent",
  "final_target_dropped",
  "final_target_content_mismatch",
  "forwarder_ended",
  "final_target_other_environment",
]);
export type ThreadRelayDeliveryErrorCode = typeof ThreadRelayDeliveryErrorCode.Type;

/**
 * Only `delivered` proves final delivery, with the final target's own message
 * read back. A receipt read anywhere but the final target's environment is at
 * best `unverified`, whatever the intermediate hops show.
 */
export const ThreadRelayReceipt = Schema.Struct({
  relayId: ThreadRelayId,
  environmentId: EnvironmentId,
  finalTarget: ThreadRelayTarget,
  state: Schema.Literals(["delivered", "pending", "unverified", "delivery_error"]),
  error: Schema.NullOr(
    Schema.Struct({
      code: ThreadRelayDeliveryErrorCode,
      detail: Schema.String,
    }),
  ),
  hops: Schema.Array(ThreadRelayHopReceipt),
  finalMessage: Schema.NullOr(
    Schema.Struct({
      messageId: MessageId,
      contentSha256: ThreadRelayContentSha256,
      text: Schema.String,
      textTruncated: Schema.Boolean,
    }),
  ),
});
export type ThreadRelayReceipt = typeof ThreadRelayReceipt.Type;
