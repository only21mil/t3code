import * as NodeCrypto from "@effect/platform-node/NodeCrypto";
import {
  EnvironmentId,
  MessageId,
  type OrchestrationV2ConversationMessage,
  type OrchestrationV2ThreadProjection,
  type OrchestrationV2ThreadShell,
  ProjectId,
  ProviderInstanceId,
  RunId,
  ThreadId,
} from "@t3tools/contracts";
import { threadRelayContentSha256, threadRelayMessageId } from "@t3tools/shared/threadRelay";
import * as DateTime from "effect/DateTime";
import * as Effect from "effect/Effect";
import * as Layer from "effect/Layer";
import { expect, it } from "vite-plus/test";

import { LocalEnvironmentId } from "../environment/LocalEnvironmentId.ts";
import * as ProviderAdapterRegistry from "../orchestration-v2/ProviderAdapterRegistry.ts";
import * as ThreadManagementService from "../orchestration-v2/ThreadManagementService.ts";
import * as ProjectService from "../project/ProjectService.ts";
import * as ProviderRegistry from "../provider/ProviderRegistry.ts";
import * as ScheduledTaskService from "../scheduledTasks/ScheduledTaskService.ts";
import * as SecretRequests from "../secrets/SecretRequests.ts";
import * as ServerSettings from "../serverSettings.ts";
import type * as McpInvocationContext from "./McpInvocationContext.ts";
import * as OrchestratorMcpService from "./OrchestratorMcpService.ts";

const fd = EnvironmentId.make("env-fd");
const mbp = EnvironmentId.make("env-mbp");
const projectId = ProjectId.make("project-relay");
const root = ThreadId.make("thread-relay-root");
const child = ThreadId.make("thread-relay-child");
const instanceId = ProviderInstanceId.make("codex");
const now = DateTime.makeUnsafe("2026-10-26T01:41:00.000Z");
const relayId = "relay-r6-option-2";
const approval = "Victor approved R6 option 2.";

interface StoredThread {
  runs: Array<{ id: RunId; ordinal: number; status: string }>;
  messages: Array<OrchestrationV2ConversationMessage>;
  turnItems: Array<{ type: "user_message"; messageId: MessageId; runId: RunId; status: string }>;
}

/**
 * A local stand-in for the thread store. `drop` makes the next send record its
 * message on a run that is cancelled before the message reaches the transcript.
 */
function makeStore(drop: { next: boolean }) {
  const threads = new Map<ThreadId, StoredThread>([
    [
      root,
      {
        runs: [{ id: RunId.make("run-root-1"), ordinal: 1, status: "running" }],
        messages: [],
        turnItems: [],
      },
    ],
    [child, { runs: [], messages: [], turnItems: [] }],
  ]);
  const projection = (threadId: ThreadId) => {
    const stored = threads.get(threadId)!;
    return {
      thread: {
        id: threadId,
        projectId,
        title: threadId,
        createdBy: "user",
        creationSource: "mcp",
        modelSelection: { instanceId, model: "gpt-5.4" },
        runtimeMode: "full-access",
        interactionMode: "default",
        branch: null,
        worktreePath: null,
        lineage: { parentThreadId: null, relationshipToParent: null, rootThreadId: threadId },
        archivedAt: null,
        deletedAt: null,
        providerInstanceId: instanceId,
        createdAt: now,
        updatedAt: now,
      },
      runs: stored.runs.map((run) => ({
        ...run,
        modelSelection: { instanceId, model: "gpt-5.4" },
        providerInstanceId: instanceId,
        requestedAt: now,
        startedAt: now,
        completedAt: null,
      })),
      messages: stored.messages,
      turnItems: stored.turnItems,
      runtimeRequests: [],
      contextTransfers: [],
      subagents: [],
      providerThreads: [],
      providerTurns: [],
      visibleTurnItems: [],
      updatedAt: now,
    } as unknown as OrchestrationV2ThreadProjection;
  };
  const filtered = (
    threadId: ThreadId,
    filter?: {
      readonly messageIds?: ReadonlyArray<MessageId>;
      readonly turnItemRunIds?: ReadonlyArray<RunId | null>;
    },
  ) => {
    const full = projection(threadId);
    return {
      ...full,
      messages:
        filter?.messageIds === undefined
          ? full.messages
          : full.messages.filter((message) => filter.messageIds!.includes(message.id)),
      turnItems:
        filter?.turnItemRunIds === undefined
          ? full.turnItems
          : full.turnItems.filter((item) => filter.turnItemRunIds!.includes(item.runId)),
    } as OrchestrationV2ThreadProjection;
  };
  const record = (threadId: ThreadId, input: ThreadManagementService.ThreadManagementSendInput) => {
    const stored = threads.get(threadId)!;
    const existing = stored.messages.find((message) => message.id === input.messageId);
    const runId = existing?.runId ?? RunId.make(`run-${threadId}-${stored.runs.length + 1}`);
    if (existing === undefined) {
      const dropped = drop.next;
      drop.next = false;
      stored.runs.push({
        id: runId,
        ordinal: stored.runs.length + 1,
        status: dropped ? "cancelled" : "running",
      });
      stored.messages.push({
        id: input.messageId,
        threadId,
        runId,
        nodeId: null,
        role: "user",
        text: input.text,
        attachments: [],
        streaming: false,
        createdBy: input.createdBy,
        creationSource: input.creationSource,
        ...(input.senderThreadId === undefined ? {} : { senderThreadId: input.senderThreadId }),
        ...(input.relay === undefined ? {} : { relay: input.relay }),
        createdAt: now,
        updatedAt: now,
      });
      if (!dropped) {
        stored.turnItems.push({
          type: "user_message",
          messageId: input.messageId,
          runId,
          status: "completed",
        });
      }
    }
    return runId;
  };
  return { threads, projection, filtered, record };
}

const scope = (threadId: ThreadId): McpInvocationContext.McpInvocationScope => ({
  environmentId: fd,
  requestNamespace: `session-${threadId}`,
  thread: { threadId, providerSessionId: `session-${threadId}`, providerInstanceId: instanceId },
  client: undefined,
  capabilities: new Set(["orchestration"]),
  issuedAt: 1,
});

function serviceLayer(store: ReturnType<typeof makeStore>) {
  return OrchestratorMcpService.layer.pipe(
    Layer.provide(
      Layer.mergeAll(
        Layer.mock(ThreadManagementService.ThreadManagementService)({
          getThreadRecords: (threadId, _fields, filter) =>
            store.threads.has(threadId)
              ? Effect.succeed(store.filtered(threadId, filter))
              : Effect.die(`unexpected thread ${threadId}`),
          getThreadShell: (threadId) =>
            Effect.succeed(
              store.threads.has(threadId)
                ? (store.projection(threadId).thread as unknown as OrchestrationV2ThreadShell)
                : null,
            ),
          getProjectThreadRecords: (input, _fields, filter) =>
            Effect.succeed(store.filtered(input.threadId, filter)),
          sendToThread: (input) =>
            Effect.sync(() => {
              const runId = store.record(input.threadId, input);
              return {
                run: { id: runId, status: "running" },
                delivery: "started",
              } as unknown as ThreadManagementService.ThreadManagementSendResult;
            }),
        } satisfies Partial<ThreadManagementService.ThreadManagementService["Service"]>),
        ServerSettings.layerTest(),
        Layer.mock(ProviderRegistry.ProviderRegistry)({ getProviders: Effect.succeed([]) }),
        Layer.mock(ProjectService.ProjectService)({}),
        Layer.mock(SecretRequests.SecretRequests)({}),
        Layer.mock(ScheduledTaskService.ScheduledTaskService)({}),
        Layer.mock(ProviderAdapterRegistry.ProviderAdapterRegistryV2)({
          list: () => Effect.succeed([]),
        }),
        Layer.succeed(LocalEnvironmentId, { get: Effect.succeed(fd) }),
        NodeCrypto.layer,
      ),
    ),
  );
}

/** The first hop as the initiating sender (a bot) leaves it in the root thread. */
const seedRootHop = (store: ReturnType<typeof makeStore>, finalEnvironmentId: EnvironmentId) =>
  store.record(root, {
    projectId,
    commandId: "command-seed" as never,
    threadId: root,
    messageId: MessageId.make(threadRelayMessageId({ relayId, environmentId: fd, threadId: root })),
    text: `${approval} Forward it to ${child}.`,
    attachments: [],
    mode: "auto",
    createdBy: "agent",
    creationSource: "mcp",
    relay: {
      relayId,
      finalTarget: { environmentId: finalEnvironmentId, threadId: child },
      hop: 1,
      previous: null,
      previousVerified: false,
      contentSha256: threadRelayContentSha256(approval),
    },
  });

it("a forward inherits the relay and proves delivery from the final target's message", async () => {
  const store = makeStore({ next: false });
  seedRootHop(store, fd);
  await Effect.gen(function* () {
    const service = yield* OrchestratorMcpService.OrchestratorMcpService;
    const sent = yield* service.sendToThread(scope(root), {
      threadId: child,
      message: approval,
      relay: { relayId },
    });
    expect(sent.relay?.state).toBe("delivered");
    expect(sent.relay?.finalMessage?.text).toBe(approval);
    const hop = store.threads.get(child)!.messages[0]!.relay;
    expect(hop).toMatchObject({ hop: 2, previousVerified: true, finalTarget: { threadId: child } });
    expect(hop?.previous?.threadId).toBe(root);

    // A retried forward replays the same message instead of adding one.
    yield* service.sendToThread(scope(root), {
      threadId: child,
      message: approval,
      relay: { relayId },
    });
    expect(store.threads.get(child)!.messages).toHaveLength(1);

    const receipt = yield* service.relayReceipt(scope(root), {
      relayId,
      finalTarget: { threadId: child },
      viaThreadId: root,
    });
    expect(receipt.state).toBe("delivered");
    expect(receipt.hops.map((entry) => entry.state)).toEqual(["delivered", "delivered"]);

    // The final hop must carry the declared text exactly.
    const changed = yield* service
      .sendToThread(scope(root), {
        threadId: child,
        message: "Option 1.",
        relay: {
          relayId: `${relayId}-x`,
          finalTarget: { threadId: child },
          contentSha256: threadRelayContentSha256(approval),
        },
      })
      .pipe(Effect.flip);
    expect(changed.code).toBe("invalid_request");
  }).pipe(Effect.provide(serviceLayer(store)), Effect.runPromise);
});

it("reports a deliberately dropped final hop and a forwarder that ended without sending", async () => {
  const drop = { next: false };
  const store = makeStore(drop);
  seedRootHop(store, fd);
  await Effect.gen(function* () {
    const service = yield* OrchestratorMcpService.OrchestratorMcpService;
    // Without a forward, an interrupted forwarder is an explicit delivery error.
    store.threads.get(root)!.runs = store.threads
      .get(root)!
      .runs.map((run) => ({ ...run, status: "interrupted" }));
    const unsent = yield* service.relayReceipt(scope(root), {
      relayId,
      finalTarget: { threadId: child },
      viaThreadId: root,
    });
    expect(unsent.state).toBe("delivery_error");
    expect(unsent.error?.code).toBe("forwarder_ended");

    // The forwarder resumes and sends, but the final target drops the message.
    store.threads.get(root)!.runs = store.threads
      .get(root)!
      .runs.map((run) => ({ ...run, status: "running" }));
    drop.next = true;
    const dropped = yield* service.sendToThread(scope(root), {
      threadId: child,
      message: approval,
      relay: { relayId },
    });
    expect(dropped.relay?.state).toBe("delivery_error");
    expect(dropped.relay?.error?.code).toBe("final_target_dropped");
  }).pipe(Effect.provide(serviceLayer(store)), Effect.runPromise);
});

it("never forwards across environments and reads a remote final target as unverified", async () => {
  const store = makeStore({ next: false });
  seedRootHop(store, mbp);
  await Effect.gen(function* () {
    const service = yield* OrchestratorMcpService.OrchestratorMcpService;
    const refused = yield* service
      .sendToThread(scope(root), { threadId: child, message: approval, relay: { relayId } })
      .pipe(Effect.flip);
    expect(refused.code).toBe("invalid_request");
    expect(refused.message).toContain("does not forward across environments");
    expect(store.threads.get(child)!.messages).toHaveLength(0);

    const receipt = yield* service.relayReceipt(scope(root), {
      relayId,
      finalTarget: { environmentId: mbp, threadId: child },
      viaThreadId: root,
    });
    expect(receipt.state).toBe("unverified");
    expect(receipt.error?.code).toBe("final_target_other_environment");
  }).pipe(Effect.provide(serviceLayer(store)), Effect.runPromise);
});
