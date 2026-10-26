import * as NodeServices from "@effect/platform-node/NodeServices";
import { expect, it } from "@effect/vitest";
import { EnvironmentId, type StopNativeRecord, ThreadId } from "@t3tools/contracts";
import * as Effect from "effect/Effect";
import * as FileSystem from "effect/FileSystem";
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

const stubbedDelivery = (
  calls: Array<ProcessRunner.ProcessRunInput>,
  beforeRun: Effect.Effect<void> = Effect.void,
) => {
  const runner = ProcessRunner.ProcessRunner.of({
    run: (input) =>
      beforeRun.pipe(
        Effect.andThen(
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
        ),
      ),
  });
  return StopNoticeDelivery.layer.pipe(
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
        nativeRecordDir: null,
      }),
    ),
    Layer.provide(NodeServices.layer),
  );
};

it.effect("hands the notifier only the seam fields, with this environment, on stdin", () =>
  Effect.gen(function* () {
    const calls: Array<ProcessRunner.ProcessRunInput> = [];
    const layer = stubbedDelivery(calls);
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

// Inside this checkout, never the system temp directory.
const recordRoot = `${import.meta.dirname}/.stop-notice-records.test`;
const removeRecords = FileSystem.FileSystem.use((fs) =>
  fs.remove(recordRoot, { recursive: true, force: true }),
);

it.effect("writes the native stop record before the notifier runs, the same bytes on replay", () =>
  Effect.gen(function* () {
    const fs = yield* FileSystem.FileSystem;
    yield* removeRecords;
    const recordPath = `${recordRoot}/thread/episode.json`;
    const seenBeforeRun: Array<boolean> = [];
    const calls: Array<ProcessRunner.ProcessRunInput> = [];
    const layer = stubbedDelivery(
      calls,
      fs.exists(recordPath).pipe(
        Effect.orDie,
        Effect.map((seen) => {
          seenBeforeRun.push(seen);
        }),
      ),
    );
    const nativeRecord: StopNativeRecord = {
      path: recordPath,
      body: {
        schema: "t3-native-stop-record/v1",
        note: "Not the agent's RESULT.",
        threadId: ThreadId.make("thread:stopper"),
        episodeId: "message:objective",
        episodeOrigin: "message",
        disposition: "UNDECLARED",
        source: "native",
        trigger: "run_completed",
        runId: null,
        runtimeRequestId: null,
        owner: "Sats",
        requiredAction: "The run ended without a stop report. Read the thread's last message.",
        opener: null,
        stoppedAt: "2026-10-26T02:00:00.000Z",
        transcript: {
          threadId: ThreadId.make("thread:stopper"),
          runId: null,
          read: "t3_thread_read",
        },
      },
    };
    const notifyOnce = Effect.gen(function* () {
      const delivery = yield* StopNoticeDelivery.StopNoticeDeliveryService;
      return yield* delivery.notify({
        final: false,
        delivery: {
          operation: "stop",
          episodeId: "message:objective",
          request: {
            thread_id: ThreadId.make("thread:stopper"),
            episode_message_id: "message:objective",
            owner: "Sats",
            disposition: "UNDECLARED",
            continuation: "none",
            result_path: recordPath,
            required_action: nativeRecord.body.requiredAction,
          },
          nativeRecord,
        },
      });
    }).pipe(Effect.provide(layer));
    yield* Effect.gen(function* () {
      yield* notifyOnce;
      const first = yield* fs.readFileString(recordPath);
      yield* notifyOnce;
      expect(seenBeforeRun).toEqual([true, true]);
      expect(yield* fs.readFileString(recordPath)).toBe(first);
      const written = JSON.parse(first);
      expect(written).toMatchObject({
        schema: "t3-native-stop-record/v1",
        environment: "env-test",
        disposition: "UNDECLARED",
        owner: "Sats",
      });
      expect(first).not.toContain("sats-completion-notify");
      expect(JSON.parse(calls[0]?.stdin ?? "{}").result_path).toBe(recordPath);
      expect(yield* fs.readDirectory(`${recordRoot}/thread`)).toEqual(["episode.json"]);
    }).pipe(Effect.ensuring(Effect.orDie(removeRecords)));
  }).pipe(Effect.provide(NodeServices.layer)),
);

it.effect("does not run the notifier when the native stop record cannot be written", () =>
  Effect.gen(function* () {
    const fs = yield* FileSystem.FileSystem;
    yield* removeRecords;
    yield* fs.makeDirectory(recordRoot, { recursive: true });
    // A file where the record's directory must go makes the write fail.
    yield* fs.writeFileString(`${recordRoot}/blocked`, "");
    const calls: Array<ProcessRunner.ProcessRunInput> = [];
    yield* Effect.gen(function* () {
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
              owner: "Sats",
              disposition: "UNDECLARED",
              continuation: "none",
              result_path: `${recordRoot}/blocked/episode.json`,
              required_action: "Read the thread.",
            },
            nativeRecord: {
              path: `${recordRoot}/blocked/episode.json`,
              body: {
                schema: "t3-native-stop-record/v1",
                note: "Not the agent's RESULT.",
                threadId: ThreadId.make("thread:stopper"),
                episodeId: "message:objective",
                episodeOrigin: "message",
                disposition: "UNDECLARED",
                source: "native",
                trigger: "run_completed",
                runId: null,
                runtimeRequestId: null,
                owner: "Sats",
                requiredAction: "Read the thread.",
                opener: null,
                stoppedAt: "2026-10-26T02:00:00.000Z",
                transcript: {
                  threadId: ThreadId.make("thread:stopper"),
                  runId: null,
                  read: "t3_thread_read",
                },
              },
            },
          },
        });
      }).pipe(Effect.provide(stubbedDelivery(calls)));
      expect(receipt).toMatchObject({ outcome: "retry", notifierState: null });
      expect(receipt.error).toContain("native stop record could not be written");
      expect(calls).toEqual([]);
    }).pipe(Effect.ensuring(Effect.orDie(removeRecords)));
  }).pipe(Effect.provide(NodeServices.layer)),
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
