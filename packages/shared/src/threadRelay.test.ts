import { EnvironmentId, MessageId, RunId, ThreadId, type ThreadRelayHop } from "@t3tools/contracts";
import { describe, expect, it } from "vite-plus/test";

import {
  evaluateThreadRelayReceipt,
  threadRelayContentSha256,
  threadRelayMessageId,
  type ThreadRelayHopObservation,
} from "./threadRelay.ts";

const fd = EnvironmentId.make("env-fd");
const mbp = EnvironmentId.make("env-mbp");
const root = ThreadId.make("thread:root");
const child = ThreadId.make("thread:child");
const relayId = "relay:r6-option-2";
const approval = "Victor approved R6 option 2.";

const relay = (finalTarget: {
  environmentId: EnvironmentId;
  threadId: ThreadId;
}): ThreadRelayHop => ({
  relayId,
  finalTarget,
  hop: 1,
  previous: null,
  previousVerified: false,
  contentSha256: threadRelayContentSha256(approval),
});

const hop = (
  threadId: ThreadId,
  environmentId: EnvironmentId,
  input: Partial<ThreadRelayHopObservation> = {},
): ThreadRelayHopObservation => ({
  threadId,
  messageId: MessageId.make(threadRelayMessageId({ relayId, environmentId, threadId })),
  message: { text: approval, relay: relay({ environmentId: fd, threadId: child }) },
  inTranscript: true,
  run: { id: RunId.make(`run:${threadId}`), status: "running" },
  ...input,
});

describe("threadRelayMessageId", () => {
  it("is stable per relay, environment and thread", () => {
    const id = threadRelayMessageId({ relayId, environmentId: fd, threadId: child });
    expect(threadRelayMessageId({ relayId, environmentId: fd, threadId: child })).toBe(id);
    expect(threadRelayMessageId({ relayId, environmentId: mbp, threadId: child })).not.toBe(id);
    expect(threadRelayMessageId({ relayId, environmentId: fd, threadId: root })).not.toBe(id);
  });
});

describe("evaluateThreadRelayReceipt", () => {
  const finalTarget = { environmentId: fd, threadId: child };

  it("proves delivery only from the final target's transcript, with its text read back", () => {
    const receipt = evaluateThreadRelayReceipt({
      relayId,
      environmentId: fd,
      finalTarget,
      final: hop(child, fd),
    });
    expect(receipt.state).toBe("delivered");
    expect(receipt.finalMessage).toMatchObject({
      text: approval,
      contentSha256: threadRelayContentSha256(approval),
    });
  });

  it("does not count a queued final message as delivered", () => {
    const receipt = evaluateThreadRelayReceipt({
      relayId,
      environmentId: fd,
      finalTarget,
      final: hop(child, fd, {
        inTranscript: false,
        run: { id: RunId.make("run:q"), status: "queued" },
      }),
    });
    expect(receipt.state).toBe("pending");
  });

  it("returns a delivery error for a deliberately dropped final message", () => {
    const receipt = evaluateThreadRelayReceipt({
      relayId,
      environmentId: fd,
      finalTarget,
      final: hop(child, fd, {
        inTranscript: false,
        run: { id: RunId.make("run:q"), status: "cancelled" },
      }),
    });
    expect(receipt.state).toBe("delivery_error");
    expect(receipt.error?.code).toBe("final_target_dropped");
  });

  it("does not let an accepted intermediate hop stand in for the final target", () => {
    // The incident: the root accepted the approval and its run started, then the run
    // was interrupted without ever sending the final hop.
    const receipt = evaluateThreadRelayReceipt({
      relayId,
      environmentId: fd,
      finalTarget,
      via: {
        ...hop(root, fd),
        forwarderActive: false,
        forwarderRunStatus: "interrupted",
      },
      final: hop(child, fd, { message: undefined, inTranscript: false, run: undefined }),
    });
    expect(receipt.hops.map((entry) => entry.state)).toEqual(["delivered", "missing"]);
    expect(receipt.state).toBe("delivery_error");
    expect(receipt.error?.code).toBe("forwarder_ended");
    expect(receipt.error?.detail).toContain("interrupted");
  });

  it("stays pending while the forwarder still works, and errors with no forwarder", () => {
    const missing = hop(child, fd, { message: undefined, inTranscript: false, run: undefined });
    expect(
      evaluateThreadRelayReceipt({
        relayId,
        environmentId: fd,
        finalTarget,
        via: { ...hop(root, fd), forwarderActive: true, forwarderRunStatus: "running" },
        final: missing,
      }).state,
    ).toBe("pending");
    expect(
      evaluateThreadRelayReceipt({ relayId, environmentId: fd, finalTarget, final: missing }).error
        ?.code,
    ).toBe("final_target_message_absent");
  });

  it("is only unverified when the final target is in another environment", () => {
    const receipt = evaluateThreadRelayReceipt({
      relayId,
      environmentId: fd,
      finalTarget: { environmentId: mbp, threadId: child },
      via: { ...hop(root, fd), forwarderActive: false, forwarderRunStatus: "interrupted" },
    });
    expect(receipt.state).toBe("unverified");
    expect(receipt.error?.code).toBe("final_target_other_environment");
    expect(receipt.finalMessage).toBeNull();
  });

  it("rejects a final message whose text differs from the declared content", () => {
    const receipt = evaluateThreadRelayReceipt({
      relayId,
      environmentId: fd,
      finalTarget,
      final: hop(child, fd, {
        message: { text: "Option 1 it is.", relay: relay(finalTarget) },
      }),
    });
    expect(receipt.state).toBe("delivery_error");
    expect(receipt.error?.code).toBe("final_target_content_mismatch");
  });
});
