import { assert, it } from "@effect/vitest";
import * as Effect from "effect/Effect";
import * as SqlClient from "effect/unstable/sql/SqlClient";
import * as NodeSqliteClient from "@t3tools/shared/nodeSqliteClient";

import { runMigrations } from "../Migrations.ts";

it.layer(NodeSqliteClient.layerMemory())("051_ProjectionThreadsProjectless", (it) => {
  it.effect("makes project_id nullable and adds workspace_ownership without rewriting rows", () =>
    Effect.gen(function* () {
      const sql = yield* SqlClient.SqlClient;
      yield* runMigrations({ toMigrationInclusive: 50 });
      const now = "2026-01-01T00:00:00.000Z";
      yield* sql`
        INSERT INTO projection_threads (
          thread_id, project_id, title, model_selection_json, runtime_mode,
          created_at, updated_at
        ) VALUES (
          'thread-1', 'project-1', 'Existing thread',
          '{"instanceId":"codex","model":"gpt-5.4"}', 'full-access', ${now}, ${now}
        )
      `;
      yield* runMigrations({ toMigrationInclusive: 51 });
      const columns = yield* sql<{
        readonly name: string;
        readonly notnull: number;
      }>`
        PRAGMA table_info(projection_threads)
      `;
      const projectId = columns.find((column) => column.name === "project_id");
      assert.ok(projectId);
      assert.equal(projectId.notnull, 0);
      assert.ok(columns.some((column) => column.name === "workspace_ownership"));

      const existing = yield* sql<{
        readonly projectId: string | null;
        readonly workspaceOwnership: string | null;
        readonly title: string;
      }>`
        SELECT project_id AS "projectId", workspace_ownership AS "workspaceOwnership", title
        FROM projection_threads
        WHERE thread_id = 'thread-1'
      `;
      assert.deepEqual(existing, [
        { projectId: "project-1", workspaceOwnership: null, title: "Existing thread" },
      ]);

      yield* sql`
        INSERT INTO projection_threads (
          thread_id, project_id, title, model_selection_json, runtime_mode,
          worktree_path, workspace_ownership, created_at, updated_at
        ) VALUES (
          'thread-projectless', NULL, 'New chat',
          '{"instanceId":"codex","model":"gpt-5.4"}', 'full-access',
          '/tmp/conversations/thread-projectless/work', 'app', ${now}, ${now}
        )
      `;
      const inserted = yield* sql<{
        readonly projectId: string | null;
        readonly workspaceOwnership: string | null;
      }>`
        SELECT project_id AS "projectId", workspace_ownership AS "workspaceOwnership"
        FROM projection_threads
        WHERE thread_id = 'thread-projectless'
      `;
      assert.deepEqual(inserted, [{ projectId: null, workspaceOwnership: "app" }]);
    }),
  );
});
