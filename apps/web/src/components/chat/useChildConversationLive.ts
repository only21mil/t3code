import { useAtomValue } from "@effect/atom-react";
import { parseThreadKey, threadKey } from "@t3tools/client-runtime/state/entities";
import type { ScopedThreadRef } from "@t3tools/contracts";
import { subagentConversationIsLive } from "@t3tools/shared/orchestrationV2PendingBackgroundWork";
import { Atom } from "effect/reactivity";

import { environmentThreadShells } from "~/state/threads";

const EMPTY_CHILD_CONVERSATION_LIVE: ReadonlyMap<string, boolean> = new Map();
const EMPTY_CHILD_CONVERSATION_LIVE_ATOM = Atom.make(EMPTY_CHILD_CONVERSATION_LIVE).pipe(
  Atom.withLabel("web-child-conversation-live:empty"),
);

function sameLiveness(left: ReadonlyMap<string, boolean>, right: ReadonlyMap<string, boolean>) {
  if (left.size !== right.size) return false;
  for (const [threadId, live] of left) {
    if (right.get(threadId) !== live) return false;
  }
  return true;
}

// Reads direct subagent shells only, and keeps the old map until a child's
// liveness changes, so streaming in a child does not re-render the parent.
const childConversationLiveAtomFamily = Atom.family((key: string) => {
  const ref = parseThreadKey(key);
  let previous = EMPTY_CHILD_CONVERSATION_LIVE;
  return Atom.make((get) => {
    const next = new Map<string, boolean>();
    for (const thread of get(environmentThreadShells.environmentThreadsAtom(ref.environmentId))) {
      if (
        thread.lineage.parentThreadId !== ref.threadId ||
        thread.lineage.relationshipToParent !== "subagent"
      ) {
        continue;
      }
      const live = subagentConversationIsLive(thread);
      if (live !== null) next.set(thread.id, live);
    }
    if (sameLiveness(previous, next)) return previous;
    previous = next;
    return next;
  }).pipe(Atom.withLabel(`web-child-conversation-live:${key}`));
});

/**
 * Whether each direct subagent conversation of a thread is working, keyed by
 * child thread id. Children that never ran are absent.
 */
export function useChildConversationLive(
  ref: ScopedThreadRef | null,
): ReadonlyMap<string, boolean> {
  return useAtomValue(
    ref === null
      ? EMPTY_CHILD_CONVERSATION_LIVE_ATOM
      : childConversationLiveAtomFamily(threadKey(ref)),
  );
}
