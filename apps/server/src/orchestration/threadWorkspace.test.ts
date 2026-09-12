import { assert, it } from "@effect/vitest";
import * as Effect from "effect/Effect";
import * as FileSystem from "effect/FileSystem";
import * as Path from "effect/Path";
import * as NodeServices from "@effect/platform-node/NodeServices";
import { ThreadId } from "@t3tools/contracts";

import {
  allocateAppOwnedThreadWorkspace,
  appOwnedConversationWorkPath,
  isPathInsideDirectory,
  removeAppOwnedThreadWorkspace,
} from "./threadWorkspace.ts";

it.layer(NodeServices.layer)("threadWorkspace", (it) => {
  it.effect("allocates isolated folders per thread and deletes only app-owned ones", () =>
    Effect.gen(function* () {
      const fileSystem = yield* FileSystem.FileSystem;
      const path = yield* Path.Path;
      const stateDir = yield* fileSystem.makeTempDirectoryScoped({ prefix: "t3-conversations-" });
      const first = ThreadId.make("thread-a");
      const second = ThreadId.make("thread-b");

      const firstWork = yield* allocateAppOwnedThreadWorkspace({ stateDir, threadId: first });
      const secondWork = yield* allocateAppOwnedThreadWorkspace({ stateDir, threadId: second });
      assert.notEqual(firstWork, secondWork);
      assert.equal(firstWork, appOwnedConversationWorkPath(stateDir, first, path.join));
      assert.equal(
        yield* fileSystem.exists(path.join(stateDir, "conversations", first, "attachments")),
        true,
      );
      assert.equal(
        yield* fileSystem.exists(path.join(stateDir, "conversations", first, "outputs")),
        true,
      );

      yield* fileSystem.writeFileString(path.join(firstWork, "notes.md"), "one");
      yield* fileSystem.writeFileString(path.join(secondWork, "notes.md"), "two");
      assert.equal(yield* fileSystem.readFileString(path.join(firstWork, "notes.md")), "one");
      assert.equal(yield* fileSystem.readFileString(path.join(secondWork, "notes.md")), "two");

      const removed = yield* removeAppOwnedThreadWorkspace({ stateDir, threadId: first });
      assert.equal(removed, true);
      assert.equal(yield* fileSystem.exists(path.join(stateDir, "conversations", first)), false);
      assert.equal(yield* fileSystem.exists(secondWork), true);
    }),
  );

  it.effect("refuses to delete a path that is also a user project root", () =>
    Effect.gen(function* () {
      const fileSystem = yield* FileSystem.FileSystem;
      const path = yield* Path.Path;
      const stateDir = yield* fileSystem.makeTempDirectoryScoped({
        prefix: "t3-conversations-protect-",
      });
      const threadId = ThreadId.make("thread-protected");
      const workPath = yield* allocateAppOwnedThreadWorkspace({ stateDir, threadId });
      const conversationRoot = path.dirname(workPath);
      const removed = yield* removeAppOwnedThreadWorkspace({
        stateDir,
        threadId,
        projectWorkspaceRoots: [conversationRoot],
      });
      assert.equal(removed, false);
      assert.equal(yield* fileSystem.exists(workPath), true);
    }),
  );

  it.effect("treats a path as inside its parent directory", () =>
    Effect.sync(() => {
      assert.equal(
        isPathInsideDirectory("/tmp/conversations", "/tmp/conversations/thread-1/work"),
        true,
      );
      assert.equal(isPathInsideDirectory("/tmp/conversations", "/tmp/other/thread-1"), false);
    }),
  );
});
