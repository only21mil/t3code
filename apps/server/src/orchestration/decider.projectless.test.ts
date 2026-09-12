import * as NodeServices from "@effect/platform-node/NodeServices";
import { expect, it } from "@effect/vitest";
import { CommandId, ProviderInstanceId, ThreadId } from "@t3tools/contracts";
import * as Effect from "effect/Effect";

import { decideOrchestrationCommand } from "./decider.ts";
import { createEmptyReadModel } from "./projector.ts";

it.layer(NodeServices.layer)("projectless thread.create", (it) => {
  it.effect("creates a thread without a project when a workspace path is set", () =>
    Effect.gen(function* () {
      const createdAt = "2026-09-12T00:00:00.000Z";
      const events = yield* decideOrchestrationCommand({
        command: {
          type: "thread.create",
          commandId: CommandId.make("cmd-projectless-create"),
          threadId: ThreadId.make("thread-projectless"),
          projectId: null,
          workspaceOwnership: "app",
          title: "New chat",
          modelSelection: { instanceId: ProviderInstanceId.make("codex"), model: "gpt-5.4" },
          runtimeMode: "full-access",
          interactionMode: "default",
          branch: null,
          worktreePath: "/tmp/conversations/thread-projectless/work",
          createdAt,
        },
        readModel: createEmptyReadModel(createdAt),
      });

      expect(events).toMatchObject({
        type: "thread.created",
        payload: {
          threadId: "thread-projectless",
          projectId: null,
          workspaceOwnership: "app",
          worktreePath: "/tmp/conversations/thread-projectless/work",
        },
      });
    }),
  );

  it.effect("rejects a projectless thread.create without a workspace path", () =>
    Effect.gen(function* () {
      const createdAt = "2026-09-12T00:00:00.000Z";
      const result = yield* decideOrchestrationCommand({
        command: {
          type: "thread.create",
          commandId: CommandId.make("cmd-projectless-missing-cwd"),
          threadId: ThreadId.make("thread-projectless"),
          projectId: null,
          title: "New chat",
          modelSelection: { instanceId: ProviderInstanceId.make("codex"), model: "gpt-5.4" },
          runtimeMode: "full-access",
          interactionMode: "default",
          branch: null,
          worktreePath: null,
          createdAt,
        },
        readModel: createEmptyReadModel(createdAt),
      }).pipe(Effect.exit);

      expect(result._tag).toBe("Failure");
    }),
  );
});
