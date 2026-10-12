/**
 * The subagent roster for one turn, and the compact label the mobile composer
 * pill renders for it.
 *
 * Scoped to a run rather than the whole thread: a thread accumulates every
 * subagent it ever spawned, while the pill and its sheet answer "what is this
 * turn doing right now". Agents still working from an earlier run, or with no
 * run at all, belong to that answer too, so they join the roster until they
 * settle. Statuses come from the v2 projection, reconciled with each child
 * conversation's own liveness the way the web composer reads it, so this stays
 * a pure fold over `runs`, `subagents` and that liveness map.
 */
import * as DateTime from "effect/DateTime";
import type { OrchestrationV2Subagent, OrchestrationV2ThreadProjection } from "@t3tools/contracts";
import { copySorted } from "@t3tools/shared/Array";

import { isActiveSubagentStatus, isTerminalSubagentStatus } from "./subagentRuntime.ts";
import { resolveActiveThreadRun } from "./threadWorkflows.ts";

type Projection = OrchestrationV2ThreadProjection;
type Subagent = OrchestrationV2Subagent;
type RunId = Projection["runs"][number]["id"];

const EMPTY_CHILD_CONVERSATION_LIVE: ReadonlyMap<string, boolean> = new Map();

export interface ThreadTurnSubagents {
  /** The run the roster belongs to: the active one, else the most recent one that spawned agents. */
  readonly runId: RunId | null;
  readonly turnActive: boolean;
  /**
   * The run's agents plus every live agent from any other run, in spawn order:
   * startedAt, falling back to updatedAt for agents that never started.
   */
  readonly subagents: ReadonlyArray<Subagent>;
  readonly liveCount: number;
  readonly settledCount: number;
}

export interface SubagentPillSegment {
  readonly label: string;
  readonly accessibilityLabel: string;
}

function orderKey(subagent: Subagent): number {
  return DateTime.toEpochMillis(subagent.startedAt ?? subagent.updatedAt);
}

/**
 * The task status as the child's own conversation tells it. A task left
 * running can point at a finished child, and a finished task can have a
 * running follow-up. Several tasks can share one child; its live work belongs
 * to the newest task still marked active, else to the newest task, so it
 * counts once. A follow-up row drops the earlier task's progress, result and
 * timing, which describe other work. Children absent from the map (never ran,
 * not in the shell snapshot, or provider-native) keep their task status.
 */
function reconcileWithChildConversations(
  ordered: ReadonlyArray<Subagent>,
  childConversationLive: ReadonlyMap<string, boolean>,
): ReadonlyArray<Subagent> {
  if (childConversationLive.size === 0) return ordered;
  const owners = new Map<string, Subagent>();
  for (const subagent of ordered) {
    const childThreadId = subagent.childThreadId;
    if (childThreadId === null || !childConversationLive.has(childThreadId)) continue;
    const owner = owners.get(childThreadId);
    if (
      owner === undefined ||
      isActiveSubagentStatus(subagent.status) ||
      !isActiveSubagentStatus(owner.status)
    ) {
      owners.set(childThreadId, subagent);
    }
  }
  if (owners.size === 0) return ordered;
  return ordered.map((subagent): Subagent => {
    const childThreadId = subagent.childThreadId;
    const live = childThreadId === null ? undefined : childConversationLive.get(childThreadId);
    if (childThreadId === null || live === undefined) return subagent;
    const active = isActiveSubagentStatus(subagent.status);
    if (live && owners.get(childThreadId) === subagent) {
      if (active) return subagent;
      const { progress: _progress, ...rest } = subagent;
      return { ...rest, status: "running", result: null, startedAt: null, completedAt: null };
    }
    // Not this task's work in flight: an active record is stale, and idle is
    // the honest state for work that is neither running nor known to be done.
    return active ? { ...subagent, status: "idle" } : subagent;
  });
}

/**
 * null when the thread has never spawned a subagent. `childConversationLive`
 * is keyed by child thread id, as the thread shell factory's
 * `childConversationLiveAtom` builds it.
 */
export function deriveThreadTurnSubagents(
  projection: Pick<Projection, "runs" | "subagents">,
  childConversationLive: ReadonlyMap<string, boolean> = EMPTY_CHILD_CONVERSATION_LIVE,
): ThreadTurnSubagents | null {
  if (projection.subagents.length === 0) return null;
  const activeRun = resolveActiveThreadRun(projection);
  // With no live run the newest roster is still worth showing: a turn that
  // just finished leaves results the user has not read yet.
  const latestUpdated = projection.subagents.reduce((latest, subagent) =>
    DateTime.toEpochMillis(subagent.updatedAt) > DateTime.toEpochMillis(latest.updatedAt)
      ? subagent
      : latest,
  );
  const runId = activeRun?.id ?? latestUpdated.runId;
  // Order before reconciling: a follow-up row has no start time of its own.
  const ordered = copySorted(
    projection.subagents,
    (left, right) => orderKey(left) - orderKey(right) || left.id.localeCompare(right.id),
  );
  const subagents = reconcileWithChildConversations(ordered, childConversationLive).filter(
    (subagent) => subagent.runId === runId || isActiveSubagentStatus(subagent.status),
  );
  if (subagents.length === 0) return null;

  let liveCount = 0;
  let settledCount = 0;
  for (const subagent of subagents) {
    if (isActiveSubagentStatus(subagent.status)) liveCount += 1;
    else if (isTerminalSubagentStatus(subagent.status)) settledCount += 1;
  }
  return { runId, turnActive: activeRun !== null, subagents, liveCount, settledCount };
}

/**
 * What the pill's agents segment says, or null while it should stay hidden.
 * The segment is for work in flight: once the turn settles it goes away
 * rather than leaving a stale count above the composer.
 */
export function resolveSubagentPillSegment(
  turn: ThreadTurnSubagents | null,
): SubagentPillSegment | null {
  if (turn === null) return null;
  if (!turn.turnActive && turn.liveCount === 0) return null;
  const total = turn.subagents.length;
  if (turn.liveCount > 0) {
    return {
      label: `${turn.liveCount}/${total}`,
      accessibilityLabel: `${turn.liveCount} of ${total} agents working`,
    };
  }
  // Nothing is live, so each agent completed, failed, stopped or went idle.
  // Only completed ones count as done.
  const counts = { done: 0, failed: 0, stopped: 0, idle: 0 };
  for (const subagent of turn.subagents) {
    if (subagent.status === "completed") counts.done += 1;
    else if (subagent.status === "failed") counts.failed += 1;
    else if (subagent.status === "idle") counts.idle += 1;
    else counts.stopped += 1;
  }
  const parts = Object.entries(counts)
    .filter(([, count]) => count > 0)
    .map(([outcome, count]) => `${count} ${outcome}`);
  const firstCount = Object.values(counts).find((count) => count > 0) ?? 0;
  const noun = firstCount === 1 ? "agent" : "agents";
  return {
    label: parts.join(" · "),
    accessibilityLabel: parts
      .map((part, index) => (index === 0 ? part.replace(" ", ` ${noun} `) : part))
      .join(", "),
  };
}
