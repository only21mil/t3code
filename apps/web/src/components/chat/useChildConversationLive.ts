import { useAtomValue } from "@effect/atom-react";
import type { ScopedThreadRef } from "@t3tools/contracts";
import { Atom } from "effect/reactivity";

import { environmentThreadShells } from "~/state/threads";

const EMPTY_CHILD_CONVERSATION_LIVE: ReadonlyMap<string, boolean> = new Map();
const EMPTY_CHILD_CONVERSATION_LIVE_ATOM = Atom.make(EMPTY_CHILD_CONVERSATION_LIVE).pipe(
  Atom.withLabel("web-child-conversation-live:empty"),
);

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
      : environmentThreadShells.childConversationLiveAtom(ref),
  );
}
