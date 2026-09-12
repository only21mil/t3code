import * as Effect from "effect/Effect";
import * as SqlClient from "effect/unstable/sql/SqlClient";

function quoteIdent(name: string): string {
  return `"${name.replaceAll('"', '""')}"`;
}

export default Effect.gen(function* () {
  const sql = yield* SqlClient.SqlClient;
  const columns = yield* sql<{
    readonly name: string;
    readonly type: string;
    readonly notnull: number;
    readonly dflt_value: string | null;
    readonly pk: number;
  }>`
    PRAGMA table_info(projection_threads)
  `;
  if (columns.length === 0) {
    return;
  }

  if (!columns.some((column) => column.name === "workspace_ownership")) {
    yield* sql`
      ALTER TABLE projection_threads
      ADD COLUMN workspace_ownership TEXT
    `;
  }

  const projectId = columns.find((column) => column.name === "project_id");
  if (projectId === undefined || projectId.notnull === 0) {
    return;
  }

  const refreshed = yield* sql<{
    readonly name: string;
    readonly type: string;
    readonly notnull: number;
    readonly dflt_value: string | null;
    readonly pk: number;
  }>`
    PRAGMA table_info(projection_threads)
  `;
  const columnSql = refreshed
    .map((column) => {
      const type = column.type.length > 0 ? column.type : "TEXT";
      if (column.pk === 1) {
        return `${quoteIdent(column.name)} ${type} PRIMARY KEY`;
      }
      if (column.name === "project_id") {
        return `${quoteIdent(column.name)} ${type}`;
      }
      const notNull = column.notnull === 1 ? " NOT NULL" : "";
      const dflt = column.dflt_value !== null ? ` DEFAULT ${column.dflt_value}` : "";
      return `${quoteIdent(column.name)} ${type}${notNull}${dflt}`;
    })
    .join(", ");
  const names = refreshed.map((column) => quoteIdent(column.name)).join(", ");

  yield* sql.unsafe(`
    CREATE TABLE projection_threads_051 (
      ${columnSql}
    )
  `);
  yield* sql.unsafe(`
    INSERT INTO projection_threads_051 (${names})
    SELECT ${names} FROM projection_threads
  `);
  yield* sql`DROP TABLE projection_threads`;
  yield* sql.unsafe(`ALTER TABLE projection_threads_051 RENAME TO projection_threads`);
  yield* sql`
    CREATE INDEX IF NOT EXISTS idx_projection_threads_project_deleted_created
    ON projection_threads(project_id, deleted_at, created_at)
  `;
  yield* sql`
    CREATE INDEX IF NOT EXISTS idx_projection_threads_project_archived_at
    ON projection_threads(project_id, archived_at)
  `;
  yield* sql`
    CREATE INDEX IF NOT EXISTS idx_projection_threads_shell_active
    ON projection_threads(deleted_at, archived_at, project_id, created_at, thread_id)
  `;
  yield* sql`
    CREATE INDEX IF NOT EXISTS idx_projection_threads_shell_archived
    ON projection_threads(deleted_at, archived_at, project_id, thread_id)
  `;
});
