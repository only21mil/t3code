import * as Effect from "effect/Effect";
import * as SqlClient from "effect/sql/SqlClient";

// Compaction repeats these predicates and the key expression verbatim; SQLite only uses a partial or
// expression index for a query that repeats them. Predicate columns are indexed so reads stay index-only.
export default Effect.gen(function* () {
  const sql = yield* SqlClient.SqlClient;

  // One row: what the last completed compaction pass covered. Lives in the database so a restored copy carries it.
  yield* sql`
    CREATE TABLE orchestration_v2_compaction_watermark (
      id INTEGER PRIMARY KEY CHECK (id = 1),
      event_sequence INTEGER NOT NULL,
      imported_transcript_count INTEGER NOT NULL,
      updated_at TEXT NOT NULL
    )
  `;

  // New compactable events in sequence order, covering their compaction keys.
  yield* sql`
    CREATE INDEX orchestration_events_compaction_sequence_idx
    ON orchestration_events(
      sequence,
      stream_id,
      event_type,
      (CASE
        WHEN event_type IN ('message.updated', 'node.updated')
        THEN json_extract(payload_json, '$.id')
        WHEN event_type = 'thread.pull-request-link-updated'
        THEN json_array(json_extract(payload_json, '$.host'),
          json_extract(payload_json, '$.repository'),
          json_extract(payload_json, '$.number'))
      END),
      application_event_version,
      aggregate_kind
    )
    WHERE application_event_version = 2
      AND aggregate_kind = 'thread'
      AND event_type IN (
        'thread.archived', 'thread.unarchived', 'thread.settled', 'thread.unsettled',
        'thread.snoozed', 'thread.unsnoozed', 'thread.pinned', 'thread.auto-settle-set',
        'thread.unpinned', 'thread.pin-reordered', 'thread.active-reordered',
        'thread.metadata-updated', 'thread.pull-request-synced', 'thread.runtime-mode-updated',
        'thread.interaction-mode-updated', 'thread.model-selection-updated',
        'thread.provider-switched', 'thread.guest-share-updated',
        'thread.visited', 'thread.marked-unread',
        'thread.pull-request-link-updated', 'message.updated', 'node.updated'
      )
  `;

  // Earlier retained events per thread and key, plus v1 thread events awaiting transcript import.
  yield* sql`
    CREATE INDEX orchestration_events_compaction_key_idx
    ON orchestration_events(
      stream_id,
      application_event_version,
      event_type,
      (CASE
        WHEN event_type IN ('message.updated', 'node.updated')
        THEN json_extract(payload_json, '$.id')
        WHEN event_type = 'thread.pull-request-link-updated'
        THEN json_array(json_extract(payload_json, '$.host'),
          json_extract(payload_json, '$.repository'),
          json_extract(payload_json, '$.number'))
      END),
      sequence,
      aggregate_kind
    )
    WHERE aggregate_kind = 'thread'
      AND (
        application_event_version = 1
        OR event_type IN (
          'thread.archived', 'thread.unarchived', 'thread.settled', 'thread.unsettled',
          'thread.snoozed', 'thread.unsnoozed', 'thread.pinned', 'thread.auto-settle-set',
          'thread.unpinned', 'thread.pin-reordered', 'thread.active-reordered',
          'thread.metadata-updated', 'thread.pull-request-synced', 'thread.runtime-mode-updated',
          'thread.interaction-mode-updated', 'thread.model-selection-updated',
          'thread.provider-switched', 'thread.guest-share-updated',
          'thread.visited', 'thread.marked-unread',
          'thread.pull-request-link-updated', 'message.updated', 'node.updated'
        )
      )
  `;

  yield* sql`
    CREATE INDEX orchestration_command_receipts_legacy_thread_idx
    ON orchestration_command_receipts(aggregate_id, command_type, aggregate_kind)
    WHERE command_type = 'legacy' AND aggregate_kind = 'thread'
  `;
});
