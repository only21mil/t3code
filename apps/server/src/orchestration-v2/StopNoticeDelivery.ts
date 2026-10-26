import {
  EnvironmentId,
  type StopNativeRecord,
  type StopNotifierReceipt,
  StopNotifierResumeRequest,
  StopNotifierStopRequest,
} from "@t3tools/contracts";
import * as Context from "effect/Context";
import * as Duration from "effect/Duration";
import * as Effect from "effect/Effect";
import * as FileSystem from "effect/FileSystem";
import * as Layer from "effect/Layer";
import * as Path from "effect/Path";
import * as Schema from "effect/Schema";
import { writeFileStringAtomically } from "@t3tools/shared/atomicWrite";

import * as ServerEnvironment from "../environment/ServerEnvironment.ts";
import * as ProcessRunner from "../processRunner.ts";
import { StopNoticeConfig } from "./StopNoticeConfig.ts";

export type StopNoticeDeliveryRequest =
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

/** The notifier's printed receipt; only the fields T3 records are read. */
const NotifierOutput = Schema.Struct({
  notification_state: Schema.optional(Schema.String),
  delivery_evidence: Schema.optional(Schema.NullOr(Schema.String)),
  event_id: Schema.optional(Schema.NullOr(Schema.String)),
  generation: Schema.optional(Schema.NullOr(Schema.Number)),
  recipient_run_id: Schema.optional(Schema.NullOr(Schema.String)),
  error: Schema.optional(Schema.NullOr(Schema.Unknown)),
  reason: Schema.optional(Schema.NullOr(Schema.String)),
});
const decodeNotifierOutput = Schema.decodeUnknownOption(Schema.fromJsonString(NotifierOutput));
const notifierEnvironment = { environment: EnvironmentId };
const encodeStopInput = Schema.encodeSync(
  Schema.fromJsonString(
    Schema.Struct({ ...notifierEnvironment, ...StopNotifierStopRequest.fields }),
  ),
);
const encodeResumeInput = Schema.encodeSync(
  Schema.fromJsonString(
    Schema.Struct({ ...notifierEnvironment, ...StopNotifierResumeRequest.fields }),
  ),
);

/** Stop states the notifier may still move forward by itself; T3 retries them under the same key. */
const RETRYABLE_STOP_STATES = new Set(["PENDING"]);

const errorText = (value: unknown): string | null =>
  value === null || value === undefined
    ? null
    : typeof value === "string"
      ? value
      : JSON.stringify(value);

const positiveGeneration = (value: number | null | undefined) =>
  typeof value === "number" && Number.isInteger(value) && value >= 1 ? value : null;

/**
 * Turns one notifier run into a receipt. Exit status alone never counts as
 * delivery: only a printed `WEBHOOK_ACCEPTED` names an accepted event, and
 * only a printed recipient run id proves the receiver started work.
 */
export function classifyNotifierRun(input: {
  readonly operation: "stop" | "resume";
  readonly episodeId: string;
  readonly stdout: string;
  readonly stderr: string;
  readonly code: number | null;
  readonly timedOut: boolean;
  readonly final: boolean;
}): StopNotifierReceipt {
  const base = {
    operation: input.operation,
    episodeId: input.episodeId,
    notifierState: null,
    deliveryEvidence: null,
    eventId: null,
    generation: null,
    recipientRunId: null,
    final: input.final,
  } as const;
  if (input.timedOut) {
    return { ...base, outcome: "retry", error: "The stop notifier timed out." };
  }
  const line = input.stdout.trim().split("\n").at(-1) ?? "";
  const parsed = decodeNotifierOutput(line);
  if (parsed._tag === "None") {
    const stderr = input.stderr.trim().split("\n").at(-1)?.slice(0, 500) ?? "";
    return {
      ...base,
      outcome: "retry",
      error: `The stop notifier exited ${input.code ?? "without a code"} with no receipt${stderr.length > 0 ? `: ${stderr}` : "."}`,
    };
  }
  const output = parsed.value;
  const receipt: StopNotifierReceipt = {
    ...base,
    outcome: "recorded",
    notifierState: output.notification_state ?? null,
    deliveryEvidence: output.delivery_evidence ?? null,
    eventId: output.event_id ?? null,
    generation: positiveGeneration(output.generation),
    recipientRunId: output.recipient_run_id ?? null,
    error: errorText(output.error),
  };
  if (input.operation === "resume") {
    return receipt.generation === null
      ? {
          ...receipt,
          outcome: input.code === 2 ? "recorded" : "retry",
          error: receipt.error ?? `The stop notifier allocated no generation (exit ${input.code}).`,
        }
      : receipt;
  }
  if (receipt.notifierState !== null && RETRYABLE_STOP_STATES.has(receipt.notifierState)) {
    return { ...receipt, outcome: "retry" };
  }
  return receipt;
}

export interface StopNoticeDeliveryShape {
  /** Runs the notifier once for a frozen request. Never fails: problems come back as a receipt. */
  readonly notify: (input: {
    readonly delivery: StopNoticeDeliveryRequest;
    readonly final: boolean;
  }) => Effect.Effect<StopNotifierReceipt>;
}

const unavailableReceipt = (
  delivery: StopNoticeDeliveryRequest,
  error: string,
): StopNotifierReceipt => ({
  operation: delivery.operation,
  episodeId: delivery.episodeId,
  outcome: "unavailable",
  notifierState: null,
  deliveryEvidence: null,
  eventId: null,
  generation: null,
  recipientRunId: null,
  error,
  final: true,
});

/** Defaults to reporting the notifier unavailable, so a server without the layer stays visible. */
export class StopNoticeDeliveryService extends Context.Reference<StopNoticeDeliveryShape>(
  "t3/orchestration-v2/StopNoticeDeliveryService",
  {
    defaultValue: () => ({
      notify: ({ delivery }) =>
        Effect.succeed(
          unavailableReceipt(delivery, "Stop notice delivery is not installed in this server."),
        ),
    }),
  },
) {}

/**
 * Under the outbox's 30 second lease, so a slow notifier never lets a second
 * worker claim the same row. The notifier records the stop before any
 * transport, so a timed-out attempt is retried under the same key.
 */
const NOTIFIER_TIMEOUT = Duration.seconds(25);

/**
 * The native stop record's bytes: the frozen row's body plus this server's
 * environment id, so a replay rewrites the same file.
 */
export function nativeStopRecordContents(record: StopNativeRecord, environment: string): string {
  return `${JSON.stringify({ ...record.body, environment }, null, 2)}\n`;
}

const make = Effect.gen(function* () {
  const config = yield* StopNoticeConfig;
  const fileSystem = yield* FileSystem.FileSystem;
  const path = yield* Path.Path;
  const processRunner = yield* ProcessRunner.ProcessRunner;
  const environment = yield* ServerEnvironment.ServerEnvironmentIdentity;

  const notify: StopNoticeDeliveryShape["notify"] = (input) =>
    Effect.gen(function* () {
      const { delivery } = input;
      if (config.command === null) {
        return unavailableReceipt(delivery, "No stop notifier is configured.");
      }
      if (!/^(?:\/|[A-Za-z]:[\\/])/u.test(config.command)) {
        return unavailableReceipt(delivery, "T3CODE_STOP_NOTIFIER must be an absolute path.");
      }
      const environmentId = yield* environment.getEnvironmentId;
      // The record result_path names is written, by rename, before any transport.
      if (delivery.operation === "stop" && delivery.nativeRecord !== undefined) {
        const record = delivery.nativeRecord;
        const written = yield* writeFileStringAtomically({
          filePath: record.path,
          contents: nativeStopRecordContents(record, environmentId),
        }).pipe(
          Effect.provideService(FileSystem.FileSystem, fileSystem),
          Effect.provideService(Path.Path, path),
          Effect.as(null),
          Effect.catch((error) => Effect.succeed(String(error))),
        );
        if (written !== null) {
          return {
            operation: delivery.operation,
            episodeId: delivery.episodeId,
            outcome: "retry",
            notifierState: null,
            deliveryEvidence: null,
            eventId: null,
            generation: null,
            recipientRunId: null,
            error: `The native stop record could not be written, so the notifier was not run: ${written}`,
            final: input.final,
          } satisfies StopNotifierReceipt;
        }
      }
      const stdin =
        delivery.operation === "stop"
          ? encodeStopInput({ environment: environmentId, ...delivery.request })
          : encodeResumeInput({ environment: environmentId, ...delivery.request });
      return yield* processRunner
        .run({
          command: config.command,
          args: [delivery.operation === "stop" ? "t3-stop" : "t3-resume"],
          stdin,
          timeout: NOTIFIER_TIMEOUT,
          timeoutBehavior: "timedOutResult",
          maxOutputBytes: 64 * 1024,
          outputMode: "truncate",
        })
        .pipe(
          Effect.map((output) =>
            classifyNotifierRun({
              operation: delivery.operation,
              episodeId: delivery.episodeId,
              stdout: output.stdout,
              stderr: output.stderr,
              code: output.code === null ? null : Number(output.code),
              timedOut: output.timedOut,
              final: input.final,
            }),
          ),
          Effect.catch((error) =>
            Effect.succeed<StopNotifierReceipt>({
              operation: delivery.operation,
              episodeId: delivery.episodeId,
              outcome: "retry",
              notifierState: null,
              deliveryEvidence: null,
              eventId: null,
              generation: null,
              recipientRunId: null,
              error: `The stop notifier could not run: ${error.message}`,
              final: input.final,
            }),
          ),
        );
    }).pipe(Effect.withSpan("StopNoticeDeliveryService.notify"));

  return { notify } satisfies StopNoticeDeliveryShape;
});

export const layer = Layer.effect(StopNoticeDeliveryService, make);
