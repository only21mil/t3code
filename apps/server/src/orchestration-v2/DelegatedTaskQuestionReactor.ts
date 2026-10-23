import {
  CommandId,
  MessageId,
  type OrchestrationV2AppThread,
  type OrchestrationV2DomainEvent,
  type OrchestrationV2RuntimeRequest,
  type OrchestrationV2Subagent,
  type RunId,
  type RuntimeRequestId,
  type ThreadId,
} from "@t3tools/contracts";
import * as Context from "effect/Context";
import * as Effect from "effect/Effect";
import * as Layer from "effect/Layer";
import type * as Scope from "effect/Scope";
import * as Stream from "effect/Stream";

import { reportLabel } from "@t3tools/provider-core/server/notification";

import { forkParked } from "../serverActivation.ts";
import * as ServerSettings from "../serverSettings.ts";
import * as ProjectionStore from "./ProjectionStore.ts";
import * as ThreadManagementService from "./ThreadManagementService.ts";

export class DelegatedTaskQuestionReactor extends Context.Service<
  DelegatedTaskQuestionReactor,
  {
    readonly start: () => Effect.Effect<void, never, Scope.Scope>;
    readonly handle: (event: OrchestrationV2DomainEvent) => Effect.Effect<void>;
  }
>()("t3/orchestration-v2/DelegatedTaskQuestionReactor") {}

const make = Effect.gen(function* () {
  const threads = yield* ThreadManagementService.ThreadManagementService;
  const projections = yield* ProjectionStore.ProjectionStoreV2;
  const settings = yield* ServerSettings.ServerSettingsService;
  // Wakes refused because the parent's provider is off for its project. They
  // are retried when settings change or the parent switches provider.
  const deferred = new Map<
    string,
    { readonly task: OrchestrationV2Subagent; readonly requestId: RuntimeRequestId }
  >();

  const wakeParent = Effect.fnUntraced(
    function* (task: OrchestrationV2Subagent, request: OrchestrationV2RuntimeRequest) {
      if (task.childThreadId === null) return;
      const key = `${task.threadId}:${request.id}`;
      deferred.delete(key);
      const label = reportLabel(task.title?.trim() || task.prompt);
      const situation =
        request.responseCapability.type === "message"
          ? `Delegated task ${task.id} asked a question and is still working.`
          : `Delegated task ${task.id} is blocked on a question and cannot continue until it is answered.`;
      yield* threads.dispatch({
        type: "message.dispatch",
        commandId: CommandId.make(`server:delegated-task-question:${key}`),
        threadId: task.threadId,
        messageId: MessageId.make(`message:delegated-task-question:${key}`),
        text: `${situation} Read it with t3_pending_request_read using threadId ${task.childThreadId} and requestId ${request.id}. Answer it with t3_pending_request_respond when the answer follows from the task or the user's instructions; otherwise ask the user, then answer it. If it is no longer pending, it was answered or dismissed.`,
        notification: {
          source: { kind: "delegated_task", taskIds: [task.id], childThreadId: task.childThreadId },
          outcome: "updated",
          summary: `Delegated task${label === undefined ? "" : ` "${label}"`} has a question`,
        },
        attachments: [],
        dispatchMode: { type: "queue_after_active" },
        createdBy: "agent",
        creationSource: "server",
      });
    },
    (effect, task, request) =>
      effect.pipe(
        Effect.catchTag("ThreadManagementProviderInstanceDisabledError", () =>
          Effect.sync(() => {
            deferred.set(`${task.threadId}:${request.id}`, { task, requestId: request.id });
          }),
        ),
      ),
  );

  const wakeForQuestion = Effect.fnUntraced(function* (
    child: OrchestrationV2AppThread,
    runId: RunId | undefined,
    request: OrchestrationV2RuntimeRequest,
  ) {
    const parentThreadId = child.lineage.parentThreadId;
    if (parentThreadId === null) return;
    const parent = yield* projections.getThreadRecords(parentThreadId, ["subagents", "runs"]);
    const { runs } = yield* projections.getThreadRecords(child.id, ["runs"]);
    const run =
      runs.find((run) => run.id === runId) ?? runs.toSorted((a, b) => b.ordinal - a.ordinal)[0];
    const taskId =
      run?.delegatedTaskId ??
      (child.forkedFrom?.type === "node" ? child.forkedFrom.nodeId : undefined);
    const task = parent.subagents.find(
      (candidate) => candidate.origin === "app_owned" && candidate.id === taskId,
    );
    if (
      task === undefined ||
      parent.thread.archivedAt !== null ||
      parent.thread.deletedAt !== null
    ) {
      return;
    }
    // A blocking delegate_task wait delivers the question itself.
    if (
      task.completionWake === "settled_only" &&
      request.responseCapability.type === "live" &&
      parent.runs.some(
        (run) =>
          run.id === task.runId &&
          (run.status === "preparing" || run.status === "starting" || run.status === "running"),
      )
    ) {
      return;
    }
    yield* wakeParent(task, request);
  });

  const retryDeferred = Effect.fnUntraced(function* (parentThreadId?: ThreadId) {
    for (const [key, { task, requestId }] of [...deferred]) {
      if (parentThreadId !== undefined && task.threadId !== parentThreadId) continue;
      yield* Effect.gen(function* () {
        const request =
          task.childThreadId === null
            ? undefined
            : yield* projections.getRuntimeRequest(task.childThreadId, requestId);
        const parent = yield* projections.getThread(task.threadId);
        if (
          request?.status !== "pending" ||
          parent.archivedAt !== null ||
          parent.deletedAt !== null
        ) {
          deferred.delete(key);
          return;
        }
        yield* wakeParent(task, request);
      }).pipe(
        Effect.catchCause((cause) =>
          Effect.logWarning("retrying a delegated task question failed", {
            taskId: task.id,
            requestId,
            cause,
          }),
        ),
      );
    }
  });

  // Live questions do not outlive a restart, but message questions stay
  // pending. A question whose wake was already delivered replays its receipt.
  const wakeMessageQuestions = Effect.fnUntraced(
    function* () {
      for (const childThreadId of yield* threads.listActiveSubagentThreadIds()) {
        const child = yield* projections.getThreadRecords(childThreadId, ["runtimeRequests"]);
        for (const request of child.runtimeRequests) {
          if (
            request.kind !== "user_input" ||
            request.status !== "pending" ||
            request.responseCapability.type !== "message"
          ) {
            continue;
          }
          const { node } = yield* projections.getRuntimeResponseContext(childThreadId, request.id);
          yield* wakeForQuestion(child.thread, node?.runId ?? undefined, request);
        }
      }
    },
    Effect.catchCause((cause) =>
      Effect.logWarning("waking parents of pending delegated task questions failed", { cause }),
    ),
  );

  // Runs for every domain event; most events return before any work is needed.
  const handle: DelegatedTaskQuestionReactor["Service"]["handle"] = Effect.fnUntraced(
    function* (event) {
      if (event.type === "run.updated") {
        if (!["completed", "failed", "waiting"].includes(event.payload.status)) return;
        const parent = yield* projections.getThreadRecords(event.threadId, ["subagents"]);
        if (parent.thread.archivedAt !== null || parent.thread.deletedAt !== null) return;
        for (const task of parent.subagents) {
          if (
            task.origin !== "app_owned" ||
            task.runId !== event.payload.id ||
            task.completionWake !== "settled_only" ||
            task.completionDelivery?.state === "disposed" ||
            task.childThreadId === null ||
            ["completed", "failed", "cancelled", "interrupted"].includes(task.status)
          ) {
            continue;
          }
          const child = yield* projections.getThreadRecords(task.childThreadId, [
            "runtimeRequests",
          ]);
          for (const request of child.runtimeRequests) {
            if (
              request.kind !== "user_input" ||
              request.status !== "pending" ||
              request.responseCapability.type !== "live"
            ) {
              continue;
            }
            yield* wakeParent(task, request).pipe(
              Effect.catchCause((cause) =>
                Effect.logWarning("catching up a delegated task question failed", {
                  taskId: task.id,
                  requestId: request.id,
                  cause,
                }),
              ),
            );
          }
        }
        return;
      }
      if (event.type === "thread.provider-switched") {
        yield* retryDeferred(event.threadId);
        return;
      }
      if (event.type !== "runtime-request.updated" || event.payload.kind !== "user_input") {
        return;
      }
      const child = yield* projections.getThread(event.threadId);
      const parentThreadId = child.lineage.parentThreadId;
      if (parentThreadId === null) return;
      const request = yield* projections.getRuntimeRequest(event.threadId, event.payload.id);
      const key = `${parentThreadId}:${event.payload.id}`;
      const messageId = MessageId.make(`message:delegated-task-question:${key}`);
      if (event.payload.status !== "pending" || request?.status !== "pending") {
        deferred.delete(key);
        const parent = yield* projections.getThreadRecords(parentThreadId, ["runs"]);
        const queued = parent.runs.find(
          (run) => run.status === "queued" && run.userMessageId === messageId,
        );
        if (queued !== undefined) {
          yield* threads.dispatch({
            type: "queued-run.cancel",
            commandId: CommandId.make(`server:delegated-task-question-cancel:${key}`),
            threadId: parentThreadId,
            runId: queued.id,
          });
        }
        return;
      }
      yield* wakeForQuestion(child, event.runId, request);
    },
    (effect, event) =>
      effect.pipe(
        Effect.catchCause((cause) =>
          Effect.logWarning("waking the parent of a delegated task question failed", {
            threadId: event.threadId,
            cause,
          }),
        ),
      ),
  );

  const start: DelegatedTaskQuestionReactor["Service"]["start"] = Effect.fn(
    "DelegatedTaskQuestionReactor.start",
  )(function* () {
    const settingsChanges = yield* settings.subscribeChanges;
    yield* forkParked(
      Stream.runForEach(threads.streamDomainEvents, handle).pipe(
        Effect.catchCause((cause) =>
          Effect.logWarning("delegated task question event stream failed", { cause }),
        ),
      ),
    );
    yield* forkParked(wakeMessageQuestions());
    yield* forkParked(Stream.runForEach(settingsChanges, () => retryDeferred()));
  });

  return { start, handle } satisfies DelegatedTaskQuestionReactor["Service"];
});

export const layer = Layer.effect(DelegatedTaskQuestionReactor, make);
