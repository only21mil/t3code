/**
 * App-owned conversation workspaces for threads that are not attached to a
 * project. Path is keyed by thread id so a title change never moves the folder.
 *
 * Layout:
 *   {stateDir}/conversations/{threadId}/
 *     attachments/
 *     work/        <- provider cwd
 *     outputs/
 */
import * as Effect from "effect/Effect";
import * as FileSystem from "effect/FileSystem";
import * as Path from "effect/Path";
import { normalizeProjectPathForComparison } from "@t3tools/shared/path";
import type { ThreadId } from "@t3tools/contracts";

const APP_OWNED_CONVERSATION_DIR = "conversations";
const APP_OWNED_WORK_DIR = "work";

function appOwnedConversationRoot(stateDir: string, threadId: ThreadId, join: Path.Path["join"]) {
  return join(stateDir, APP_OWNED_CONVERSATION_DIR, threadId);
}

export function appOwnedConversationWorkPath(
  stateDir: string,
  threadId: ThreadId,
  join: Path.Path["join"],
) {
  return join(appOwnedConversationRoot(stateDir, threadId, join), APP_OWNED_WORK_DIR);
}

export function isPathInsideDirectory(directory: string, candidate: string): boolean {
  const normalizedDirectory = normalizeProjectPathForComparison(directory);
  const normalizedCandidate = normalizeProjectPathForComparison(candidate);
  return (
    normalizedCandidate === normalizedDirectory ||
    normalizedCandidate.startsWith(`${normalizedDirectory}/`)
  );
}

export const allocateAppOwnedThreadWorkspace = Effect.fn("allocateAppOwnedThreadWorkspace")(
  function* (input: { readonly stateDir: string; readonly threadId: ThreadId }) {
    const fileSystem = yield* FileSystem.FileSystem;
    const path = yield* Path.Path;
    const conversationRoot = appOwnedConversationRoot(input.stateDir, input.threadId, path.join);
    const workPath = path.join(conversationRoot, APP_OWNED_WORK_DIR);
    yield* fileSystem.makeDirectory(path.join(conversationRoot, "attachments"), {
      recursive: true,
    });
    yield* fileSystem.makeDirectory(workPath, { recursive: true });
    yield* fileSystem.makeDirectory(path.join(conversationRoot, "outputs"), { recursive: true });
    return workPath;
  },
);

export const removeAppOwnedThreadWorkspace = Effect.fn("removeAppOwnedThreadWorkspace")(
  function* (input: {
    readonly stateDir: string;
    readonly threadId: ThreadId;
    readonly projectWorkspaceRoots?: ReadonlyArray<string>;
  }) {
    const fileSystem = yield* FileSystem.FileSystem;
    const path = yield* Path.Path;
    const conversationsDir = path.join(input.stateDir, APP_OWNED_CONVERSATION_DIR);
    const conversationRoot = appOwnedConversationRoot(input.stateDir, input.threadId, path.join);
    if (!isPathInsideDirectory(conversationsDir, conversationRoot)) {
      return false;
    }
    const protectedRoots = (input.projectWorkspaceRoots ?? []).map(
      normalizeProjectPathForComparison,
    );
    if (protectedRoots.includes(normalizeProjectPathForComparison(conversationRoot))) {
      return false;
    }
    const exists = yield* fileSystem.exists(conversationRoot);
    if (!exists) {
      return false;
    }
    yield* fileSystem.remove(conversationRoot, { recursive: true });
    return true;
  },
);
