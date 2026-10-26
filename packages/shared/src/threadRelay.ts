import { sha256 } from "@noble/hashes/sha2";
import type {
  EnvironmentId,
  OrchestrationV2Run,
  ThreadId,
  ThreadRelayHop,
  ThreadRelayHopReceipt,
  ThreadRelayReceipt,
  ThreadRelayTarget,
} from "@t3tools/contracts";

const hex = (bytes: Uint8Array) =>
  Array.from(bytes, (byte) => byte.toString(16).padStart(2, "0")).join("");

export function threadRelayContentSha256(text: string): string {
  return hex(sha256(new TextEncoder().encode(text)));
}

/**
 * Every hop of a relay into one thread has the same message id, derived from
 * the relay, the thread's environment and the thread. A retried or duplicated
 * forward replays that message instead of adding another, and any reader in
 * that environment can find the hop without a shared index.
 */
export function threadRelayMessageId(input: {
  readonly relayId: string;
  readonly environmentId: string;
  readonly threadId: string;
}): string {
  const digest = hex(
    sha256(
      new TextEncoder().encode(
        `${input.relayId}\u0000${input.environmentId}\u0000${input.threadId}`,
      ),
    ),
  ).slice(0, 40);
  return `message:relay:${digest}`;
}

/** What one environment knows about a relay hop into one of its threads. */
export interface ThreadRelayHopObservation {
  readonly threadId: ThreadId;
  readonly messageId: ThreadRelayHopReceipt["messageId"];
  readonly message:
    | { readonly text: string; readonly relay?: ThreadRelayHop | undefined }
    | undefined;
  /** The message reached the thread's transcript as a user turn. */
  readonly inTranscript: boolean;
  readonly run: Pick<OrchestrationV2Run, "id" | "status"> | undefined;
}

const DROPPED_RUN_STATUSES = new Set<OrchestrationV2Run["status"]>([
  "cancelled",
  "rolled_back",
  "interrupted",
  "failed",
]);

const FINAL_TEXT_LIMIT = 4000;

function hopReceipt(
  environmentId: EnvironmentId,
  hop: ThreadRelayHopObservation,
): ThreadRelayHopReceipt {
  const state: ThreadRelayHopReceipt["state"] =
    hop.message === undefined
      ? "missing"
      : hop.inTranscript
        ? "delivered"
        : hop.run !== undefined && DROPPED_RUN_STATUSES.has(hop.run.status)
          ? "dropped"
          : "pending";
  return {
    environmentId,
    threadId: hop.threadId,
    messageId: hop.messageId,
    hop: hop.message?.relay?.hop ?? null,
    state,
    runId: hop.run?.id ?? null,
    runStatus: hop.run?.status ?? null,
    contentSha256: hop.message === undefined ? null : threadRelayContentSha256(hop.message.text),
  };
}

/**
 * Judges a relay from one environment's own records. Only the final target's
 * transcript proves delivery; an intermediate hop, a queued message or a
 * started run never does. Read from any other environment the result is at
 * best `unverified`: T3 does not reach across environments, so the sender
 * reads the final environment's receipt through that environment's own
 * authenticated route.
 */
export function evaluateThreadRelayReceipt(input: {
  readonly relayId: string;
  readonly environmentId: EnvironmentId;
  readonly finalTarget: ThreadRelayTarget;
  readonly via?:
    | (ThreadRelayHopObservation & {
        /** A run at or after the via hop's run is still working, so a forward may still come. */
        readonly forwarderActive: boolean;
        readonly forwarderRunStatus: string | null;
      })
    | undefined;
  readonly final?: ThreadRelayHopObservation | undefined;
}): ThreadRelayReceipt {
  const { relayId, environmentId, finalTarget, via, final } = input;
  const hops: Array<ThreadRelayHopReceipt> = [];
  if (via !== undefined) hops.push(hopReceipt(environmentId, via));
  const base = { relayId, environmentId, finalTarget, hops, finalMessage: null };
  const forwarderDetail =
    via === undefined
      ? ""
      : ` The forwarding thread ${via.threadId} ${via.message === undefined ? "has no hop of this relay" : `holds hop ${via.messageId}`}; its latest run is ${via.forwarderRunStatus ?? "absent"}.`;

  if (finalTarget.environmentId !== environmentId || final === undefined) {
    return {
      ...base,
      state: "unverified",
      error: {
        code: "final_target_other_environment",
        detail: `The final target ${finalTarget.threadId} is in environment ${finalTarget.environmentId}. Read this relay's receipt there through that environment's authenticated route; this environment cannot prove final delivery.${forwarderDetail}`,
      },
    };
  }

  const finalHop = hopReceipt(environmentId, final);
  hops.push(finalHop);
  switch (finalHop.state) {
    case "delivered": {
      const text = final.message?.text ?? "";
      const declared = final.message?.relay?.contentSha256 ?? via?.message?.relay?.contentSha256;
      const finalMessage = {
        messageId: final.messageId,
        contentSha256: finalHop.contentSha256 ?? threadRelayContentSha256(text),
        text: text.slice(0, FINAL_TEXT_LIMIT),
        textTruncated: text.length > FINAL_TEXT_LIMIT,
      };
      if (declared != null && declared !== finalMessage.contentSha256) {
        return {
          ...base,
          finalMessage,
          state: "delivery_error",
          error: {
            code: "final_target_content_mismatch",
            detail: `The final target's message hashes to ${finalMessage.contentSha256}, not the declared ${declared}.`,
          },
        };
      }
      return { ...base, finalMessage, state: "delivered", error: null };
    }
    case "pending":
      return { ...base, state: "pending", error: null };
    case "dropped":
      return {
        ...base,
        state: "delivery_error",
        error: {
          code: "final_target_dropped",
          detail: `The final target recorded ${final.messageId}, but its run ended ${finalHop.runStatus} before the message reached the transcript.`,
        },
      };
    case "missing":
      if (via !== undefined && via.message !== undefined && via.forwarderActive) {
        return { ...base, state: "pending", error: null };
      }
      return {
        ...base,
        state: "delivery_error",
        error:
          via !== undefined && via.message !== undefined
            ? {
                code: "forwarder_ended",
                detail: `The final target has no message ${final.messageId}, and the forwarding thread stopped working without sending it.${forwarderDetail}`,
              }
            : {
                code: "final_target_message_absent",
                detail: `The final target ${finalTarget.threadId} has no message ${final.messageId}.${forwarderDetail}`,
              },
      };
  }
}
