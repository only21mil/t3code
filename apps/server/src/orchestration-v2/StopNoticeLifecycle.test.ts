import { assert, it } from "@effect/vitest";
import {
  CommandId,
  MessageId,
  ProjectId,
  ProviderDriverKind,
  ProviderInstanceId,
  RunId,
  RuntimeRequestId,
  ThreadId,
} from "@t3tools/contracts";
import * as Data from "effect/Data";
import * as Effect from "effect/Effect";
import * as Exit from "effect/Exit";
import * as Layer from "effect/Layer";
import * as SqlClient from "effect/sql/SqlClient";

import * as SqlitePersistence from "../persistence/Sqlite.ts";
import * as ServerSettings from "../serverSettings.ts";
import { CodexProviderCapabilitiesV2 } from "./Adapters/CodexAdapterV2.ts";
import * as CommandReceiptStore from "./CommandReceiptStore.ts";
import * as Orchestrator from "./Orchestrator.ts";
import * as ProjectionStore from "./ProjectionStore.ts";
import * as ProviderAdapterRegistry from "./ProviderAdapterRegistry.ts";
import { StopNoticeConfig } from "./StopNoticeConfig.ts";
import { deriveStopNotices, StopNoticeDeriver } from "./StopNoticeDerivation.ts";
import * as ThreadManagementService from "./ThreadManagementService.ts";
import * as ProviderReplayHarness from "./testkit/ProviderReplayHarness.ts";
import type * as ProviderAdapter from "@t3tools/provider-core/server/ProviderAdapter";

const instanceId = ProviderInstanceId.make("codex");
const modelSelection = { instanceId, model: "gpt-5.1-codex" };
const adapter = {
  instanceId,
  driver: ProviderDriverKind.make("codex"),
  getCapabilities: () => Effect.succeed(CodexProviderCapabilitiesV2),
  planSelectionTransition: () => Effect.succeed({ type: "apply_on_next_turn" as const }),
  openSession: () => Effect.die("Runs here never reach a provider"),
} as ProviderAdapter.ProviderAdapterV2["Service"];

// No effect worker: runs stay unstarted, and the outbox rows stay for inspection.
// While set, every stop derivation fails, as a projection read error would.
class InjectedDerivationError extends Data.TaggedError("InjectedDerivationError")<{}> {}
let derivationFails = false;
const flakyDeriver = Layer.succeed(StopNoticeDeriver, {
  derive: ((input) =>
    derivationFails
      ? Effect.fail(new InjectedDerivationError())
      : deriveStopNotices(input)) as typeof deriveStopNotices,
});

const makeLayer = (command: string | null) => {
  const layerDatabase = SqlitePersistence.layerMemory;
  return ThreadManagementService.layer.pipe(
    Layer.provideMerge(
      Layer.mergeAll(
        layerDatabase,
        ProjectionStore.layer.pipe(Layer.provide(layerDatabase)),
        ProviderReplayHarness.layerWithRegistry(
          { name: "stop-notice" },
          ProviderAdapterRegistry.layerFromAdapters([adapter]),
          { databaseLayer: layerDatabase, runEffectWorker: false },
        ),
      ),
    ),
    Layer.provideMerge(ServerSettings.layerTest()),
    Layer.provideMerge(CommandReceiptStore.layer.pipe(Layer.provide(layerDatabase))),
    Layer.provide(
      Layer.succeed(StopNoticeConfig, { command, defaultOwner: "genesis", nativeRecordDir: null }),
    ),
    Layer.provide(flakyDeriver),
  );
};

const threadId = ThreadId.make("thread:stop-notice");

const createAndSend = (text: string) =>
  Effect.gen(function* () {
    const orchestrator = yield* Orchestrator.OrchestratorV2;
    yield* orchestrator.dispatch({
      type: "thread.create",
      commandId: CommandId.make(`create:${threadId}`),
      threadId,
      projectId: ProjectId.make("project:stop-notice"),
      title: "Stop notice",
      modelSelection,
      runtimeMode: "full-access",
      interactionMode: "default",
      branch: null,
      worktreePath: null,
      createdBy: "user",
      creationSource: "web",
    });
    yield* send(text);
  });

const send = (text: string) =>
  Orchestrator.OrchestratorV2.use((orchestrator) =>
    orchestrator.dispatch({
      type: "message.dispatch",
      commandId: CommandId.make(`send:${text}`),
      threadId,
      messageId: MessageId.make(`message:${text}`),
      text,
      attachments: [],
      dispatchMode: { type: "start_immediately" },
      createdBy: "user",
      creationSource: "web",
    }),
  );

const interruptLatest = (name: string) =>
  Effect.gen(function* () {
    const orchestrator = yield* Orchestrator.OrchestratorV2;
    const run = (yield* orchestrator.getThreadProjection(threadId)).runs.at(-1)!;
    yield* orchestrator.dispatch({
      type: "run.interrupt",
      commandId: CommandId.make(`interrupt:${name}`),
      threadId,
      runId: run.id,
    });
  });

const declare = (disposition: string, name: string) =>
  Orchestrator.OrchestratorV2.use((orchestrator) =>
    orchestrator.dispatch({
      type: "thread.stop-notice.declare",
      commandId: CommandId.make(`declare:${name}`),
      threadId,
      declaration: {
        disposition,
        owner: "genesis",
        resultPath: "/home/victor/work/lane/RESULT.md",
        requiredAction: "Review the draft diff.",
        runId: RunId.make("run:unused"),
        declaredAt: "2026-10-26T01:30:00.000Z",
      },
    }),
  );

const stopRows = Effect.gen(function* () {
  const sql = yield* SqlClient.SqlClient;
  return (yield* sql<{ readonly effect_id: string; readonly payload_json: string }>`
    SELECT effect_id, payload_json FROM orchestration_v2_effect_outbox
    WHERE effect_type = 'stop-notice.deliver'
    ORDER BY rowid
  `).map((row) => ({ id: row.effect_id, request: JSON.parse(row.payload_json).request }));
});

const stopNotice = Orchestrator.OrchestratorV2.use((orchestrator) =>
  orchestrator.getThreadProjection(threadId),
).pipe(Effect.map((projection) => projection.thread.stopNotice));

it.effect("without a notifier, a held run ends with no stop record, as before the fix", () =>
  Effect.gen(function* () {
    yield* createAndSend("work");
    assert.isTrue(Exit.isFailure(yield* Effect.exit(declare("HOLD-DRAFT", "off"))));
    yield* interruptLatest("off");
    assert.isUndefined(yield* stopNotice);
    assert.deepEqual(yield* stopRows, []);
  }).pipe(Effect.provide(makeLayer(null))),
);

it.effect(
  "an explicit HOLD-DRAFT and the run's end commit one stop and one outbox row, then a reply resumes once",
  () =>
    Effect.gen(function* () {
      yield* createAndSend("work");
      yield* declare("HOLD-DRAFT", "hold");
      // Declaring while the run is live records it; the stop waits for the run to end.
      assert.isNull((yield* stopNotice)?.stop);

      yield* interruptLatest("hold");
      const stopped = yield* stopNotice;
      assert.equal(stopped?.episodeId, "message:work");
      assert.equal(stopped?.stop?.disposition, "HOLD-DRAFT");
      assert.equal(stopped?.stop?.source, "explicit");
      assert.equal(stopped?.delivery?.state, "pending");

      // The same report again replays; a different one in this episode is refused.
      yield* declare("HOLD-DRAFT", "hold-again");
      assert.isTrue(Exit.isFailure(yield* Effect.exit(declare("DONE", "conflict"))));

      assert.deepEqual(
        (yield* stopRows).map((row) => row.id),
        [
          `effect:stop-notice.deliver:resume:${threadId}:message:work`,
          `effect:stop-notice.deliver:stop:${threadId}:message:work`,
        ],
      );
      assert.deepEqual((yield* stopRows)[1]?.request, {
        thread_id: threadId,
        episode_message_id: "message:work",
        owner: "genesis",
        disposition: "HOLD-DRAFT",
        continuation: "none",
        result_path: "/home/victor/work/lane/RESULT.md",
        required_action: "Review the draft diff.",
      });

      // The answer opens the next episode once; a retried dispatch of it adds nothing.
      yield* send("amended brief");
      yield* send("amended brief");
      const resumed = yield* stopNotice;
      assert.equal(resumed?.episodeId, "message:amended brief");
      assert.equal(resumed?.previous?.stop.disposition, "HOLD-DRAFT");
      assert.deepEqual(
        (yield* stopRows).map((row) => row.id),
        [
          `effect:stop-notice.deliver:resume:${threadId}:message:work`,
          `effect:stop-notice.deliver:stop:${threadId}:message:work`,
          `effect:stop-notice.deliver:resume:${threadId}:message:amended brief`,
        ],
      );

      // A notifier receipt for the earlier hold still lands on that hold.
      yield* Orchestrator.OrchestratorV2.use((orchestrator) =>
        orchestrator.dispatch({
          type: "thread.stop-notice.record",
          commandId: CommandId.make("record:hold"),
          threadId,
          attempt: 1,
          receipt: {
            operation: "stop",
            episodeId: "message:work",
            outcome: "recorded",
            notifierState: "WEBHOOK_ACCEPTED",
            deliveryEvidence: "accepted",
            eventId: "e".repeat(64),
            generation: 1,
            recipientRunId: null,
            error: null,
            final: false,
          },
        }),
      );
      const recorded = yield* stopNotice;
      assert.equal(recorded?.previous?.delivery.state, "accepted");
      assert.equal(recorded?.episodeId, "message:amended brief");
    }).pipe(Effect.provide(makeLayer("/opt/sats/sats-completion-notify"))),
);

it.effect("a run ended with no report still stops natively, from the run's own end", () =>
  Effect.gen(function* () {
    yield* createAndSend("silent");
    yield* interruptLatest("silent");
    const notice = yield* stopNotice;
    assert.equal(notice?.stop?.source, "native");
    assert.equal(notice?.stop?.disposition, "CANCELED");
    assert.equal(notice?.stop?.trigger, "run_interrupted");
  }).pipe(Effect.provide(makeLayer("/opt/sats/sats-completion-notify"))),
);

const reconcileRows = Effect.gen(function* () {
  const sql = yield* SqlClient.SqlClient;
  return (yield* sql<{ readonly effect_id: string; readonly payload_json: string }>`
    SELECT effect_id, payload_json FROM orchestration_v2_effect_outbox
    WHERE effect_type = 'stop-notice.reconcile'
    ORDER BY rowid
  `).map((row) => ({
    id: row.effect_id,
    request: JSON.parse(row.payload_json) as {
      readonly objectiveMessageIds: ReadonlyArray<MessageId>;
      readonly resolvedRequestIds: ReadonlyArray<RuntimeRequestId>;
      readonly terminalRunIds: ReadonlyArray<RunId>;
      readonly subagentEnded: boolean;
    },
  }));
});

// What the effect worker does with a reconcile row.
const runReconcile = (row: Effect.Success<typeof reconcileRows>[number]) =>
  Orchestrator.OrchestratorV2.use((orchestrator) =>
    orchestrator.dispatch({
      objectiveMessageIds: row.request.objectiveMessageIds,
      resolvedRequestIds: row.request.resolvedRequestIds,
      terminalRunIds: row.request.terminalRunIds,
      subagentEnded: row.request.subagentEnded,
      type: "thread.stop-notice.reconcile",
      commandId: CommandId.make(`command:${row.id}`),
      threadId,
    }),
  );

it.effect("a failed stop derivation commits a reconcile row, never a silently lost stop", () =>
  Effect.gen(function* () {
    // Old cause: the derivation error was logged and the run's end committed
    // with no stop record and no outbox row, so nothing would ever report it.
    derivationFails = true;
    yield* createAndSend("lost");
    yield* interruptLatest("lost");
    derivationFails = false;
    assert.isUndefined(yield* stopNotice);
    assert.deepEqual(yield* stopRows, []);
    const rows = yield* reconcileRows;
    assert.isAbove(rows.length, 0);
    assert.isTrue(
      rows.some((row) => row.request.objectiveMessageIds.includes(MessageId.make("message:lost"))),
    );
    assert.isTrue(rows.some((row) => row.request.terminalRunIds.length > 0));

    // Each row replans from the committed projection; running them again adds nothing.
    for (const row of rows) yield* runReconcile(row);
    for (const row of rows) yield* runReconcile(row);
    const notice = yield* stopNotice;
    assert.equal(notice?.episodeId, "message:lost");
    assert.equal(notice?.stop?.source, "native");
    assert.equal(notice?.stop?.disposition, "CANCELED");
    assert.deepEqual(
      (yield* stopRows).map((row) => row.id),
      [
        `effect:stop-notice.deliver:resume:${threadId}:message:lost`,
        `effect:stop-notice.deliver:stop:${threadId}:message:lost`,
      ],
    );
  }).pipe(
    Effect.ensuring(Effect.sync(() => (derivationFails = false))),
    Effect.provide(makeLayer("/opt/sats/sats-completion-notify")),
  ),
);
