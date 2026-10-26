import { expect, it } from "@effect/vitest";
import { EnvironmentId, ThreadId } from "@t3tools/contracts";
import * as Effect from "effect/Effect";
import * as Layer from "effect/Layer";
import { describe } from "vite-plus/test";

import { ServerEnvironmentIdentity } from "../environment/ServerEnvironment.ts";
import * as ProcessRunner from "../processRunner.ts";
import { StopNoticeConfig } from "./StopNoticeConfig.ts";
import * as StopNoticeDelivery from "./StopNoticeDelivery.ts";

const run = (stdout: string, code: number | null, timedOut = false) =>
  StopNoticeDelivery.classifyNotifierRun({
    operation: "stop",
    episodeId: "message:objective",
    stdout,
    stderr: "",
    code,
    timedOut,
    final: false,
  });

describe("classifyNotifierRun", () => {
  it("never treats exit 0 alone as a receipt", () => {
    expect(run("", 0)).toMatchObject({ outcome: "retry", notifierState: null });
  });

  it("reads the notifier's state, evidence and recipient run", () => {
    const accepted = run(
      '{"notification_state":"WEBHOOK_ACCEPTED","delivery_evidence":"accepted","event_id":"e","generation":2,"recipient_run_id":null}',
      3,
    );
    expect(accepted).toMatchObject({
      outcome: "recorded",
      notifierState: "WEBHOOK_ACCEPTED",
      deliveryEvidence: "accepted",
      generation: 2,
      recipientRunId: null,
    });
    expect(
      run('{"notification_state":"WEBHOOK_ACCEPTED","recipient_run_id":"r-1","generation":2}', 0)
        .recipientRunId,
    ).toBe("r-1");
  });

  it("retries a pending stop under the same key and a timeout", () => {
    expect(run('{"notification_state":"PENDING","error":{"http_status":503}}', 1)).toMatchObject({
      outcome: "retry",
      error: '{"http_status":503}',
    });
    expect(run("", null, true).outcome).toBe("retry");
  });
});

it.effect("hands the notifier only the seam fields, with this environment, on stdin", () =>
  Effect.gen(function* () {
    const calls: Array<ProcessRunner.ProcessRunInput> = [];
    const runner = ProcessRunner.ProcessRunner.of({
      run: (input) =>
        Effect.sync(() => {
          calls.push(input);
          return {
            stdout:
              '{"operation":"t3-stop","notification_state":"WEBHOOK_ACCEPTED","delivery_evidence":"recipient_run","recipient_run_id":"r-9","generation":4,"event_id":"e"}\n',
            stderr: "",
            code: 0 as never,
            timedOut: false,
            stdoutTruncated: false,
            stderrTruncated: false,
            stdoutInvalidUtf8: false,
            stderrInvalidUtf8: false,
          };
        }),
    });
    const layer = StopNoticeDelivery.layer.pipe(
      Layer.provide(Layer.succeed(ProcessRunner.ProcessRunner, runner)),
      Layer.provide(
        Layer.succeed(ServerEnvironmentIdentity, {
          getEnvironmentId: Effect.succeed(EnvironmentId.make("env-test")),
        }),
      ),
      Layer.provide(
        Layer.succeed(StopNoticeConfig, {
          command: "/opt/sats/sats-completion-notify",
          defaultOwner: "genesis",
        }),
      ),
    );
    const receipt = yield* Effect.gen(function* () {
      const delivery = yield* StopNoticeDelivery.StopNoticeDeliveryService;
      return yield* delivery.notify({
        final: false,
        delivery: {
          operation: "stop",
          episodeId: "message:objective",
          request: {
            thread_id: ThreadId.make("thread:stopper"),
            episode_message_id: "message:objective",
            owner: "genesis",
            disposition: "HOLD-DRAFT",
            continuation: "none",
            result_path: "/home/victor/work/lane/RESULT.md",
            required_action: "Review the draft.",
          },
        },
      });
    }).pipe(Effect.provide(layer));

    expect(receipt).toMatchObject({ outcome: "recorded", recipientRunId: "r-9", generation: 4 });
    expect(calls.map((call) => [call.command, ...call.args])).toEqual([
      ["/opt/sats/sats-completion-notify", "t3-stop"],
    ]);
    expect(JSON.parse(calls[0]?.stdin ?? "{}")).toEqual({
      environment: "env-test",
      thread_id: "thread:stopper",
      episode_message_id: "message:objective",
      owner: "genesis",
      disposition: "HOLD-DRAFT",
      continuation: "none",
      result_path: "/home/victor/work/lane/RESULT.md",
      required_action: "Review the draft.",
    });
  }),
);

it.effect("reports an unconfigured notifier as unavailable without running anything", () =>
  Effect.gen(function* () {
    const delivery = yield* StopNoticeDelivery.StopNoticeDeliveryService;
    const receipt = yield* delivery.notify({
      final: false,
      delivery: {
        operation: "resume",
        episodeId: "message:answer",
        request: {
          thread_id: ThreadId.make("thread:stopper"),
          episode_message_id: "message:answer",
          owner: null,
        },
      },
    });
    expect(receipt).toMatchObject({ outcome: "unavailable", final: true });
  }),
);
