import { ThreadId } from "@t3tools/contracts";
import * as NodeSqliteClient from "@t3tools/shared/nodeSqliteClient";
import * as Context from "effect/Context";
import * as DateTime from "effect/DateTime";
import * as Effect from "effect/Effect";
import * as Layer from "effect/Layer";
import * as Schema from "effect/Schema";
import * as Stream from "effect/Stream";
import * as SqlClient from "effect/sql/SqlClient";

import * as EventStore from "./EventStore.ts";
import * as ProjectionStore from "./ProjectionStore.ts";

export interface ProjectionVerificationV2 {
  readonly valid: boolean;
  readonly schemaVersion: number;
  readonly expectedSequence: number;
  readonly projectionSequence: number;
  readonly unreadableThreadIds: ReadonlyArray<ThreadId>;
  readonly missingThreadIds: ReadonlyArray<ThreadId>;
  readonly unexpectedThreadIds: ReadonlyArray<ThreadId>;
}

export class ProjectionMaintenanceError extends Schema.TaggedError<ProjectionMaintenanceError>()(
  "ProjectionMaintenanceError",
  {
    operation: Schema.String,
    cause: Schema.optional(Schema.Defect()),
  },
) {}

export interface ProjectionMaintenanceV2Shape {
  readonly verify: Effect.Effect<ProjectionVerificationV2, ProjectionMaintenanceError>;
  readonly rebuild: Effect.Effect<ProjectionVerificationV2, ProjectionMaintenanceError>;
  readonly compactEventStore: Effect.Effect<
    {
      readonly deletedEventCount: number;
      readonly deletedReceiptCount: number;
      readonly reclaimableBytes: number;
      /** Event index entries this pass read: compactable events since the last pass, rows kept for the threads and entities they touch, and v1 events of imported threads. */
      readonly scannedEventCount: number;
    },
    ProjectionMaintenanceError
  >;
}

export class ProjectionMaintenanceV2 extends Context.Service<
  ProjectionMaintenanceV2,
  ProjectionMaintenanceV2Shape
>()("t3/orchestration-v2/ProjectionMaintenance/ProjectionMaintenanceV2") {}

type ProjectionMetadataRow = {
  readonly schema_version: number;
  readonly last_sequence: number;
};

const encodeEntityKey = Schema.encodeSync(
  Schema.fromJsonString(Schema.Tuple([Schema.String, Schema.String, Schema.NullOr(Schema.String)])),
);

export const layer: Layer.Layer<
  ProjectionMaintenanceV2,
  never,
  EventStore.EventStoreV2 | ProjectionStore.ProjectionStoreV2 | SqlClient.SqlClient
> = Layer.effect(
  ProjectionMaintenanceV2,
  Effect.gen(function* () {
    const sql = yield* SqlClient.SqlClient;
    const eventStore = yield* EventStore.EventStoreV2;
    const projectionStore = yield* ProjectionStore.ProjectionStoreV2;

    const verify = Effect.gen(function* () {
      const expectedThreadRows = yield* sql<{ readonly thread_id: string }>`
        SELECT DISTINCT stream_id AS thread_id
        FROM orchestration_events INDEXED BY orchestration_events_v2_created_threads_idx
        WHERE application_event_version = 2
          AND aggregate_kind = 'thread'
          AND event_type = 'thread.created'
        ORDER BY stream_id ASC
      `;
      const projectionRows = yield* sql<{ readonly thread_id: string }>`
        SELECT thread_id
        FROM orchestration_v2_projection_threads
        ORDER BY thread_id ASC
      `;
      const actualIds = projectionRows.map((row) => ThreadId.make(row.thread_id));
      const expectedIds = expectedThreadRows.map((row) => ThreadId.make(row.thread_id));
      const actualSet = new Set(actualIds);
      const expectedSet = new Set(expectedIds);
      const missingThreadIds = expectedIds.filter((threadId) => !actualSet.has(threadId));
      const unexpectedThreadIds = actualIds.filter((threadId) => !expectedSet.has(threadId));
      const unreadableThreadIds = yield* projectionStore.getUnreadableThreadIds();
      const metadata = yield* sql<ProjectionMetadataRow>`
        SELECT schema_version, last_sequence
        FROM orchestration_v2_projection_metadata
        WHERE projection_name = 'thread-projections'
        LIMIT 1
      `;
      const expectedSequence = yield* eventStore.latestSequence();
      const schemaVersion = metadata[0]?.schema_version ?? 0;
      const projectionSequence = metadata[0]?.last_sequence ?? 0;
      return {
        valid:
          schemaVersion === ProjectionStore.ORCHESTRATION_V2_PROJECTION_SCHEMA_VERSION &&
          projectionSequence === expectedSequence &&
          missingThreadIds.length === 0 &&
          unexpectedThreadIds.length === 0 &&
          unreadableThreadIds.length === 0,
        schemaVersion,
        expectedSequence,
        projectionSequence,
        unreadableThreadIds,
        missingThreadIds,
        unexpectedThreadIds,
      } satisfies ProjectionVerificationV2;
    }).pipe(sql.withTransaction);

    const rebuild = Effect.gen(function* () {
      yield* sql.withTransaction(
        Effect.gen(function* () {
          const throughSequence = yield* eventStore.latestSequence();
          yield* sql`DELETE FROM orchestration_v2_projection_context_transfers`;
          yield* sql`DELETE FROM orchestration_v2_projection_context_handoffs`;
          yield* sql`DELETE FROM orchestration_v2_projection_checkpoints`;
          yield* sql`DELETE FROM orchestration_v2_projection_checkpoint_scopes`;
          yield* sql`DELETE FROM orchestration_v2_projection_turn_items`;
          yield* sql`DELETE FROM orchestration_v2_projection_plans`;
          yield* sql`DELETE FROM orchestration_v2_projection_messages`;
          yield* sql`DELETE FROM orchestration_v2_projection_runtime_requests`;
          yield* sql`DELETE FROM orchestration_v2_projection_provider_turns`;
          yield* sql`DELETE FROM orchestration_v2_projection_provider_threads`;
          yield* sql`DELETE FROM orchestration_v2_projection_provider_session_bindings`;
          yield* sql`DELETE FROM orchestration_v2_projection_provider_sessions`;
          yield* sql`DELETE FROM orchestration_v2_projection_subagents`;
          yield* sql`DELETE FROM orchestration_v2_projection_nodes`;
          yield* sql`DELETE FROM orchestration_v2_projection_run_attempts`;
          yield* sql`DELETE FROM orchestration_v2_projection_runs`;
          yield* sql`DELETE FROM orchestration_v2_projection_threads`;
          yield* sql`DELETE FROM orchestration_v2_turn_item_positions`;

          const pageSize = 500;
          let lastSequence = 0;
          while (true) {
            const page = yield* eventStore
              .read({ afterSequence: lastSequence, throughSequence, limit: pageSize })
              .pipe(Stream.runCollect);
            for (const stored of page) {
              yield* projectionStore.apply(stored.event);
              if (stored.event.type === "turn-item.updated") {
                yield* sql`
                INSERT INTO orchestration_v2_turn_item_positions (
                  thread_id,
                  turn_item_id,
                  ordinal
                )
                VALUES (
                  ${stored.event.threadId},
                  ${stored.event.payload.id},
                  ${stored.event.payload.ordinal}
                )
                ON CONFLICT(thread_id, turn_item_id) DO UPDATE SET
                  ordinal = excluded.ordinal
                `;
              }
              lastSequence = stored.sequence;
            }
            if (page.length < pageSize) break;
            yield* Effect.yieldNow;
          }
          const now = DateTime.formatIso(yield* DateTime.now);
          yield* sql`
            INSERT INTO orchestration_v2_projection_metadata (
              projection_name,
              schema_version,
              last_sequence,
              updated_at
            )
            VALUES (
              'thread-projections',
              ${ProjectionStore.ORCHESTRATION_V2_PROJECTION_SCHEMA_VERSION},
              ${lastSequence},
              ${now}
            )
            ON CONFLICT(projection_name) DO UPDATE SET
              schema_version = excluded.schema_version,
              last_sequence = excluded.last_sequence,
              updated_at = excluded.updated_at
          `;
        }),
      );
      return yield* verify;
    });

    const mapError =
      (operation: string) =>
      <A, E, R>(effect: Effect.Effect<A, E, R>) =>
        effect.pipe(
          Effect.mapError((cause) => new ProjectionMaintenanceError({ operation, cause })),
        );

    // Keep thread.created as the verification and replay anchor; clients recognize deletion by thread.deleted event type.
    const SUPERSEDABLE_THREAD_EVENT_TYPES = [
      "thread.archived",
      "thread.unarchived",
      "thread.settled",
      "thread.unsettled",
      "thread.snoozed",
      "thread.unsnoozed",
      "thread.pinned",
      "thread.auto-settle-set",
      "thread.unpinned",
      "thread.pin-reordered",
      "thread.active-reordered",
      "thread.metadata-updated",
      "thread.pull-request-synced",
      "thread.runtime-mode-updated",
      "thread.interaction-mode-updated",
      "thread.model-selection-updated",
      "thread.provider-switched",
      "thread.guest-share-updated",
    ];
    // Read-state events preserve updatedAt and supersede only each other. Activity events supersede both groups.
    const READ_STATE_THREAD_EVENT_TYPES = ["thread.visited", "thread.marked-unread"];

    const supersedableThreadEventTypes = new Set(SUPERSEDABLE_THREAD_EVENT_TYPES);
    const readStateThreadEventTypes = new Set(READ_STATE_THREAD_EVENT_TYPES);
    const KEYED_EVENT_TYPES = [
      "thread.pull-request-link-updated",
      "message.updated",
      "node.updated",
      "turn-item.updated",
    ];
    const keyedEventTypes = new Set(KEYED_EVENT_TYPES);
    const quoteList = (values: ReadonlyArray<string>) =>
      values.map((value) => `'${value}'`).join(", ");
    // Partial index predicates and the key expression in migration 070 must match these element for element.
    const compactableEventTypes = sql.literal(
      quoteList([
        ...SUPERSEDABLE_THREAD_EVENT_TYPES,
        ...READ_STATE_THREAD_EVENT_TYPES,
        ...KEYED_EVENT_TYPES,
      ]),
    );
    const threadStateEventTypes = sql.literal(
      quoteList([
        ...SUPERSEDABLE_THREAD_EVENT_TYPES,
        ...READ_STATE_THREAD_EVENT_TYPES,
        "thread.pull-request-link-updated",
      ]),
    );
    const compactionKey = sql.literal(`(CASE
        WHEN event.event_type IN ('message.updated', 'node.updated', 'turn-item.updated')
        THEN json_extract(event.payload_json, '$.id')
        WHEN event.event_type = 'thread.pull-request-link-updated'
        THEN json_array(json_extract(event.payload_json, '$.host'),
          json_extract(event.payload_json, '$.repository'),
          json_extract(event.payload_json, '$.number'))
      END)`);
    const citedPromptSequence = sql.literal(`(CASE
        WHEN event.event_type = 'turn-item.updated'
        THEN json_extract(event.payload_json, '$.promptSequence')
      END)`);
    // Keep subagent.updated rows: slimmed payloads reference their prompts.
    // Small pages bound work on the reader worker and synchronous fallback.
    const COMPACTION_PAGE_SIZE = 50;

    type CompactableEventRow = {
      readonly sequence: number;
      readonly stream_id: string;
      readonly event_type: string;
      readonly command_id: string | null;
      readonly entity_id: string | null;
      /** The prompt anchor a slimmed subagent turn item names; read only for an item's newest event. */
      readonly prompt_sequence: number | null;
    };

    /** Retain newest and oldest uncommanded keyed events to preserve client insertion order. Keep command-written
     * turn items and the prompt anchors retained items cite. Partial indexes hold only compactable event types. A pass walks those
     * written since the last completed pass, then the rows earlier passes kept for each thread and entity it met,
     * so it deletes what one full newest-first pass would. */
    const compactEventStore = Effect.gen(function* () {
      const bounds = yield* sql<{
        readonly event_sequence: number;
        readonly imported_transcript_count: number;
      }>`
        SELECT
          COALESCE((SELECT MAX(sequence) FROM orchestration_events), 0) AS event_sequence,
          (
            SELECT COUNT(*) FROM orchestration_v2_legacy_imports
            WHERE transcript_imported_at IS NOT NULL
          ) AS imported_transcript_count
      `;
      const eventSequence = bounds[0]?.event_sequence ?? 0;
      const importedTranscriptCount = bounds[0]?.imported_transcript_count ?? 0;
      const watermark = (yield* sql<{
        readonly event_sequence: number;
        readonly imported_transcript_count: number;
      }>`
        SELECT event_sequence, imported_transcript_count
        FROM orchestration_v2_compaction_watermark
        WHERE id = 1
      `)[0];
      // A watermark above the current log describes a different event table; walk it all.
      const afterSequence =
        watermark !== undefined && watermark.event_sequence <= eventSequence
          ? watermark.event_sequence
          : 0;
      // transcript_imported_at never resets, so a changed count means an import completed since the last pass.
      const importedSinceWatermark =
        afterSequence === 0 || watermark?.imported_transcript_count !== importedTranscriptCount;
      const retainedThreadIds = new Set<string>();
      const retainedReadStateThreadIds = new Set<string>();
      // Retain each key's oldest candidate, deleting it only when an older event appears.
      const oldestCandidateByEntityKey = new Map<string, number | null>();
      // Command-result replay also needs anchors cited by retained intermediate command events.
      const citedPromptSequences = new Set<number>();
      // Threads and entities with new events; rows earlier passes kept for them may now be obsolete.
      const touchedThreadIds = new Set<string>();
      const touchedEntities = new Map<string, CompactableEventRow>();
      let deletedEventCount = 0;
      let deletedReceiptCount = 0;
      let scannedEventCount = 0;

      const deleteEvents =
        /* This helper runs once per compaction page; the enclosing operation owns the span. */
        Effect.fnUntraced(function* (obsolete: ReadonlyArray<number>) {
          // Yield even without deletions for clients using the synchronous fallback.
          yield* Effect.yieldNow;
          for (let index = 0; index < obsolete.length; index += COMPACTION_PAGE_SIZE) {
            const page = obsolete.slice(index, index + COMPACTION_PAGE_SIZE);
            yield* sql`DELETE FROM orchestration_events WHERE sequence IN ${sql.in(page)}`;
            deletedEventCount += page.length;
            yield* Effect.yieldNow;
          }
        });

      // Rows must arrive newest first per thread and entity.
      const classify = (row: CompactableEventRow, obsolete: Array<number>) => {
        // Command receipts replay these exact events, including intermediate item versions.
        if (row.event_type === "turn-item.updated" && row.command_id !== null) {
          if (row.prompt_sequence !== null) citedPromptSequences.add(row.prompt_sequence);
          return;
        }
        if (supersedableThreadEventTypes.has(row.event_type)) {
          if (retainedThreadIds.has(row.stream_id)) obsolete.push(row.sequence);
          else retainedThreadIds.add(row.stream_id);
        } else if (readStateThreadEventTypes.has(row.event_type)) {
          if (
            retainedThreadIds.has(row.stream_id) ||
            retainedReadStateThreadIds.has(row.stream_id)
          ) {
            obsolete.push(row.sequence);
          } else retainedReadStateThreadIds.add(row.stream_id);
        } else if (
          row.event_type === "thread.pull-request-link-updated" &&
          retainedThreadIds.has(row.stream_id)
        ) {
          // A newer whole-thread payload already carries this link's state.
          obsolete.push(row.sequence);
        } else if (keyedEventTypes.has(row.event_type)) {
          const key = encodeEntityKey([row.event_type, row.stream_id, row.entity_id]);
          const candidate = oldestCandidateByEntityKey.get(key);
          if (candidate === undefined) {
            oldestCandidateByEntityKey.set(key, null);
            if (row.prompt_sequence !== null) {
              citedPromptSequences.add(row.prompt_sequence);
            }
          } else {
            if (candidate !== null && !citedPromptSequences.has(candidate)) {
              obsolete.push(candidate);
            }
            oldestCandidateByEntityKey.set(key, row.sequence);
          }
        }
      };

      let throughSequence = eventSequence;
      while (throughSequence > afterSequence) {
        const rows = yield* sql<CompactableEventRow>`
          SELECT
            event.sequence,
            event.stream_id,
            event.event_type,
            event.command_id,
            ${compactionKey} AS entity_id,
            ${citedPromptSequence} AS prompt_sequence
          FROM orchestration_events AS event
            INDEXED BY orchestration_events_compaction_sequence_idx
          WHERE event.application_event_version = 2
            AND event.aggregate_kind = 'thread'
            AND event.event_type IN (${compactableEventTypes})
            AND event.sequence <= ${throughSequence}
            AND event.sequence > ${afterSequence}
          ORDER BY event.sequence DESC
          LIMIT ${COMPACTION_PAGE_SIZE}
        `.pipe(NodeSqliteClient.readOnly);
        scannedEventCount += rows.length;
        const obsolete: Array<number> = [];
        for (const row of rows) {
          classify(row, obsolete);
          if (afterSequence > 0) {
            if (
              row.event_type === "message.updated" ||
              row.event_type === "node.updated" ||
              row.event_type === "turn-item.updated"
            ) {
              touchedEntities.set(
                encodeEntityKey([row.event_type, row.stream_id, row.entity_id]),
                row,
              );
            } else touchedThreadIds.add(row.stream_id);
          }
        }
        yield* deleteEvents(obsolete);
        throughSequence = (rows.at(-1)?.sequence ?? 1) - 1;
        if (rows.length < COMPACTION_PAGE_SIZE) break;
      }

      // Continue below the watermark through retained thread state and each link/entity's boundary events.
      // Turn items can also retain any number of command-written versions and their cited prompt anchors.
      if (afterSequence > 0) {
        const threadIds = Array.from(touchedThreadIds);
        for (let index = 0; index < threadIds.length; index += COMPACTION_PAGE_SIZE) {
          let oldThroughSequence = afterSequence;
          while (oldThroughSequence > 0) {
            // The first event_type term satisfies the partial index predicate; the second picks thread state.
            const rows = yield* sql<CompactableEventRow>`
            SELECT
              event.sequence,
              event.stream_id,
              event.event_type,
              event.command_id,
              ${compactionKey} AS entity_id,
              ${citedPromptSequence} AS prompt_sequence
            FROM orchestration_events AS event
              INDEXED BY orchestration_events_compaction_key_idx
            WHERE event.aggregate_kind = 'thread'
              AND event.application_event_version = 2
              AND event.event_type IN (${compactableEventTypes})
              AND event.stream_id IN ${sql.in(threadIds.slice(index, index + COMPACTION_PAGE_SIZE))}
              AND event.event_type IN (${threadStateEventTypes})
              AND event.sequence <= ${oldThroughSequence}
            ORDER BY event.sequence DESC
            LIMIT ${COMPACTION_PAGE_SIZE}
          `.pipe(NodeSqliteClient.readOnly);
            scannedEventCount += rows.length;
            const obsolete: Array<number> = [];
            for (const row of rows) classify(row, obsolete);
            yield* deleteEvents(obsolete);
            oldThroughSequence = (rows.at(-1)?.sequence ?? 1) - 1;
            if (rows.length < COMPACTION_PAGE_SIZE) break;
          }
        }
        const entities = Array.from(touchedEntities.values());
        for (let index = 0; index < entities.length; index += COMPACTION_PAGE_SIZE) {
          const keys = entities
            .slice(index, index + COMPACTION_PAGE_SIZE)
            .map((entity) => sql`(${entity.stream_id}, ${entity.event_type}, ${entity.entity_id})`);
          let oldThroughSequence = afterSequence;
          while (oldThroughSequence > 0) {
            // CROSS JOIN keeps the key list outermost, so each key is one index seek.
            const rows = yield* sql<CompactableEventRow>`
            WITH entity(stream_id, event_type, entity_id) AS (VALUES ${sql.csv(keys)})
            SELECT
              event.sequence,
              event.stream_id,
              event.event_type,
              event.command_id,
              ${compactionKey} AS entity_id,
              ${citedPromptSequence} AS prompt_sequence
            FROM entity
            CROSS JOIN orchestration_events AS event
              INDEXED BY orchestration_events_compaction_key_idx
            WHERE event.aggregate_kind = 'thread'
              AND event.application_event_version = 2
              AND event.event_type IN (${compactableEventTypes})
              AND event.stream_id = entity.stream_id
              AND event.event_type = entity.event_type
              AND ${compactionKey} IS entity.entity_id
              AND event.sequence <= ${oldThroughSequence}
            ORDER BY event.sequence DESC
            LIMIT ${COMPACTION_PAGE_SIZE}
          `.pipe(NodeSqliteClient.readOnly);
            scannedEventCount += rows.length;
            const obsolete: Array<number> = [];
            for (const row of rows) classify(row, obsolete);
            yield* deleteEvents(obsolete);
            oldThroughSequence = (rows.at(-1)?.sequence ?? 1) - 1;
            if (rows.length < COMPACTION_PAGE_SIZE) break;
          }
        }
      }

      // Imported transcripts replace their thread's v1 events and legacy receipts. New writes are never v1.
      if (importedSinceWatermark) {
        let afterThreadId = "";
        while (true) {
          const imports = yield* sql<{ readonly thread_id: string }>`
            SELECT thread_id
            FROM orchestration_v2_legacy_imports
            WHERE transcript_imported_at IS NOT NULL
              AND thread_id > ${afterThreadId}
            ORDER BY thread_id ASC
            LIMIT ${COMPACTION_PAGE_SIZE}
          `.pipe(NodeSqliteClient.readOnly);
          for (const { thread_id: threadId } of imports) {
            while (true) {
              const rows = yield* sql<{ readonly sequence: number }>`
                SELECT event.sequence
                FROM orchestration_events AS event
                  INDEXED BY orchestration_events_compaction_key_idx
                WHERE event.aggregate_kind = 'thread'
                  AND event.application_event_version = 1
                  AND event.stream_id = ${threadId}
                LIMIT ${COMPACTION_PAGE_SIZE}
              `.pipe(NodeSqliteClient.readOnly);
              scannedEventCount += rows.length;
              yield* deleteEvents(rows.map((row) => row.sequence));
              if (rows.length < COMPACTION_PAGE_SIZE) break;
            }
            while (true) {
              const rows = yield* sql<{ readonly row_id: number }>`
                SELECT receipt.rowid AS row_id
                FROM orchestration_command_receipts AS receipt
                  INDEXED BY orchestration_command_receipts_legacy_thread_idx
                WHERE receipt.command_type = 'legacy'
                  AND receipt.aggregate_kind = 'thread'
                  AND receipt.aggregate_id = ${threadId}
                LIMIT ${COMPACTION_PAGE_SIZE}
              `.pipe(NodeSqliteClient.readOnly);
              yield* Effect.yieldNow;
              if (rows.length > 0) {
                yield* sql`DELETE FROM orchestration_command_receipts WHERE rowid IN ${sql.in(rows.map((row) => row.row_id))}`;
                deletedReceiptCount += rows.length;
                yield* Effect.yieldNow;
              }
              if (rows.length < COMPACTION_PAGE_SIZE) break;
            }
          }
          afterThreadId = imports.at(-1)?.thread_id ?? afterThreadId;
          if (imports.length < COMPACTION_PAGE_SIZE) break;
        }
      }

      // Written only after a completed pass; an interrupted pass resumes from the previous watermark.
      const updatedAt = DateTime.formatIso(yield* DateTime.now);
      yield* sql`
        INSERT INTO orchestration_v2_compaction_watermark (
          id,
          event_sequence,
          imported_transcript_count,
          updated_at
        )
        VALUES (1, ${eventSequence}, ${importedTranscriptCount}, ${updatedAt})
        ON CONFLICT(id) DO UPDATE SET
          event_sequence = excluded.event_sequence,
          imported_transcript_count = excluded.imported_transcript_count,
          updated_at = excluded.updated_at
      `;

      const freelistRows = yield* sql<{ readonly freelist_count: number }>`PRAGMA freelist_count`;
      const pageSizeRows = yield* sql<{ readonly page_size: number }>`PRAGMA page_size`;
      const reclaimableBytes =
        (freelistRows[0]?.freelist_count ?? 0) * (pageSizeRows[0]?.page_size ?? 0);

      return { deletedEventCount, deletedReceiptCount, reclaimableBytes, scannedEventCount };
    });

    return ProjectionMaintenanceV2.of({
      verify: mapError("verify")(verify),
      rebuild: mapError("rebuild")(rebuild),
      compactEventStore: mapError("compact event store")(compactEventStore),
    });
  }),
);
