import { assert, it } from "@effect/vitest";
import * as Deferred from "effect/Deferred";
import * as Effect from "effect/Effect";
import * as Fiber from "effect/Fiber";
import * as Layer from "effect/Layer";

import * as NodeServices from "@effect/platform-node/NodeServices";
import * as FileSystem from "effect/FileSystem";
import type { GitRunStackedActionResult } from "@t3tools/contracts";

import * as ServerConfig from "../config.ts";
import * as VcsProcess from "../vcs/VcsProcess.ts";
import * as GitManager from "./GitManager.ts";
import * as GitWorkflowService from "./GitWorkflowService.ts";
import * as GitVcsDriver from "../vcs/GitVcsDriver.ts";
import * as VcsDriverRegistry from "../vcs/VcsDriverRegistry.ts";

it.layer(NodeServices.layer)("GitWorkflowService", (it) => {
  it.effect("finds a name among the refs of every namespace", () =>
    Effect.gen(function* () {
      const fileSystem = yield* FileSystem.FileSystem;
      const cwd = yield* fileSystem.makeTempDirectoryScoped({ prefix: "t3-ref-named-" });
      const workflow = yield* GitWorkflowService.GitWorkflowService;
      const driver = yield* GitVcsDriver.GitVcsDriver;
      for (const args of [
        ["init", "-b", "main"],
        ["-c", "user.email=t@t", "-c", "user.name=t", "commit", "--allow-empty", "-m", "init"],
        ["update-ref", "refs/remotes/upstream/feature/topic", "HEAD"],
        ["symbolic-ref", "refs/remotes/origin/alias", "refs/heads/main"],
        ["update-ref", "refs/mirror/origin/mirrored", "HEAD"],
      ]) {
        yield* driver.execute({ operation: "test.setupRepo", cwd, args });
      }
      const found = yield* Effect.forEach(
        ["main", "feature/topic", "alias", "mirrored", "t3/renamed", "feature/*"],
        (refName) => workflow.hasRefNamed({ cwd, refName }),
      );
      assert.deepEqual(found, [true, true, true, true, false, false]);
    }).pipe(
      Effect.scoped,
      Effect.provide(
        GitWorkflowService.layer.pipe(
          Layer.provide(
            Layer.mock(VcsDriverRegistry.VcsDriverRegistry)({
              resolve: () => Effect.succeed({ kind: "git" } as VcsDriverRegistry.VcsDriverHandle),
            }),
          ),
          Layer.provide(Layer.mock(GitManager.GitManager)({})),
          Layer.provideMerge(GitVcsDriver.layer),
          Layer.provideMerge(VcsProcess.layer),
          Layer.provideMerge(
            ServerConfig.layerTest(process.cwd(), { prefix: "t3-ref-named-" }).pipe(
              Layer.provide(NodeServices.layer),
            ),
          ),
          Layer.provideMerge(NodeServices.layer),
        ),
      ),
    ),
  );

  it.effect("holds an ordinary commit until a branch switch in the same checkout finishes", () =>
    Effect.gen(function* () {
      const fileSystem = yield* FileSystem.FileSystem;
      const cwd = yield* fileSystem.makeTempDirectoryScoped({ prefix: "t3-stacked-lease-" });
      const switchEntered = Deferred.makeUnsafe<void>();
      const releaseSwitch = Deferred.makeUnsafe<void>();
      const steps: string[] = [];
      yield* Effect.gen(function* () {
        const workflow = yield* GitWorkflowService.GitWorkflowService;
        const switching = yield* workflow
          .switchRef({ cwd, refName: "feature/b" })
          .pipe(Effect.forkChild({ startImmediately: true }));
        yield* Deferred.await(switchEntered);
        const commit = yield* workflow
          .runStackedAction({ actionId: "action-1", cwd, action: "commit" })
          .pipe(Effect.forkChild({ startImmediately: true }));
        yield* Deferred.succeed(releaseSwitch, undefined);
        yield* Fiber.join(switching);
        yield* Fiber.join(commit);
        assert.deepEqual(steps, ["switch", "commit"]);
      }).pipe(
        Effect.provide(
          GitWorkflowService.layer.pipe(
            Layer.provide(
              Layer.mock(VcsDriverRegistry.VcsDriverRegistry)({
                resolve: () =>
                  Effect.succeed({
                    kind: "git",
                    repository: { rootPath: cwd },
                  } as VcsDriverRegistry.VcsDriverHandle),
              }),
            ),
            Layer.provide(
              Layer.mock(GitManager.GitManager)({
                runStackedAction: () =>
                  Effect.sync(() => {
                    steps.push("commit");
                    return {} as GitRunStackedActionResult;
                  }),
              }),
            ),
            Layer.provide(
              Layer.mock(GitVcsDriver.GitVcsDriver)({
                switchRef: () =>
                  Deferred.succeed(switchEntered, undefined).pipe(
                    Effect.andThen(Deferred.await(releaseSwitch)),
                    Effect.map(() => {
                      steps.push("switch");
                      return { refName: "feature/b" };
                    }),
                  ),
              }),
            ),
            Layer.provide(NodeServices.layer),
          ),
        ),
      );
    }).pipe(Effect.scoped),
  );
});
