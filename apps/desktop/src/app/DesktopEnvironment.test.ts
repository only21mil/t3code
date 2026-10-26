import * as NodePath from "@effect/platform-node/NodePath";
import * as NodeServices from "@effect/platform-node/NodeServices";
import { assert, describe, it } from "@effect/vitest";
import * as Effect from "effect/Effect";
import * as Layer from "effect/Layer";

import * as DesktopEnvironment from "./DesktopEnvironment.ts";
import * as DesktopConfig from "./DesktopConfig.ts";

const defaultInput = {
  dirname: "/repo/apps/desktop/dist-electron",
  homeDirectory: "/Users/alice",
  platform: "darwin",
  processArch: "arm64",
  appVersion: "0.0.22",
  appPath: "/Applications/T3 Code.app/Contents/Resources/app.asar",
  isPackaged: false,
  resourcesPath: "/Applications/T3 Code.app/Contents/Resources",
  runningUnderArm64Translation: false,
} satisfies DesktopEnvironment.MakeDesktopEnvironmentInput;

const layerEnvironment = (
  overrides: Partial<DesktopEnvironment.MakeDesktopEnvironmentInput> = {},
  env: Record<string, string | undefined> = {},
  pathLayer = NodePath.layerPosix,
) =>
  DesktopEnvironment.layer({
    ...defaultInput,
    ...overrides,
  }).pipe(
    Layer.provide(Layer.mergeAll(NodeServices.layer, pathLayer, DesktopConfig.layerTest(env))),
  );

const makeEnvironment = (
  overrides: Partial<DesktopEnvironment.MakeDesktopEnvironmentInput> = {},
  env: Record<string, string | undefined> = {},
  pathLayer = NodePath.layerPosix,
) =>
  DesktopEnvironment.DesktopEnvironment.pipe(
    Effect.provide(layerEnvironment(overrides, env, pathLayer)),
  );

describe("DesktopEnvironment", () => {
  it.effect("uses the packaged Windows server sidecar as the backend root", () =>
    Effect.gen(function* () {
      const environment = yield* makeEnvironment({
        platform: "win32",
        isPackaged: true,
        appPath: "/install/resources/app.asar",
        resourcesPath: "/install/resources",
      });

      assert.equal(environment.appRoot, "/install/resources/app.asar");
      assert.equal(environment.serverRoot, "/install/resources/server.asar");
      assert.equal(
        environment.backendEntryPath,
        "/install/resources/server.asar/apps/server/dist/bin.mjs",
      );
      assert.equal(
        environment.clientAssetsDir,
        "/install/resources/server.asar/apps/server/dist/client",
      );
    }),
  );

  it.effect("keeps implicit development state separate from production state", () =>
    Effect.gen(function* () {
      const development = yield* makeEnvironment(
        {},
        { VITE_DEV_SERVER_URL: "http://localhost:5173" },
      );
      const production = yield* makeEnvironment();

      assert.equal(development.stateDir, "/Users/alice/.t3/dev");
      assert.equal(production.stateDir, "/Users/alice/.t3/userdata");
    }),
  );

  it.effect.each([
    { t3Home: undefined, dev: true, baseDir: "/Users/alice/.t3", stateDir: "/Users/alice/.t3/dev" },
    { t3Home: "   ", dev: true, baseDir: "/Users/alice/.t3", stateDir: "/Users/alice/.t3/dev" },
    { t3Home: "  /srv/t3  ", dev: false, baseDir: "/srv/t3", stateDir: "/srv/t3/userdata" },
    { t3Home: "~", dev: false, baseDir: "/Users/alice", stateDir: "/Users/alice/userdata" },
    {
      t3Home: "~/t3-alt",
      dev: true,
      baseDir: "/Users/alice/t3-alt",
      stateDir: "/Users/alice/t3-alt/userdata",
    },
    {
      t3Home: "~\\t3-alt",
      dev: false,
      baseDir: "/Users/alice/t3-alt",
      stateDir: "/Users/alice/t3-alt/userdata",
    },
    { t3Home: "/srv/../srv/t3", dev: false, baseDir: "/srv/t3", stateDir: "/srv/t3/userdata" },
  ])("resolves POSIX T3CODE_HOME $t3Home to $stateDir", ({ t3Home, dev, baseDir, stateDir }) =>
    Effect.gen(function* () {
      const environment = yield* makeEnvironment(
        {},
        { T3CODE_HOME: t3Home, VITE_DEV_SERVER_URL: dev ? "http://localhost:5173" : undefined },
      );

      assert.equal(environment.baseDir, baseDir);
      assert.equal(environment.stateDir, stateDir);
    }),
  );

  it.effect("resolves a relative POSIX T3CODE_HOME against the desktop's cwd", () =>
    Effect.gen(function* () {
      const environment = yield* makeEnvironment({ isPackaged: true }, { T3CODE_HOME: "state/t3" });

      assert.equal(environment.baseDir, environment.path.join(process.cwd(), "state", "t3"));
    }),
  );

  it.effect.each([
    { t3Home: undefined, baseDir: "C:\\Users\\alice\\.t3" },
    { t3Home: "D:\\t3", baseDir: "D:\\t3" },
    { t3Home: "~", baseDir: "C:\\Users\\alice" },
    { t3Home: "~\\t3-alt", baseDir: "C:\\Users\\alice\\t3-alt" },
    { t3Home: "~/t3-alt", baseDir: "C:\\Users\\alice\\t3-alt" },
    { t3Home: "D:/t3/../t3", baseDir: "D:\\t3" },
  ])("resolves Windows T3CODE_HOME $t3Home to $baseDir", ({ t3Home, baseDir }) =>
    Effect.gen(function* () {
      const environment = yield* makeEnvironment(
        { platform: "win32", homeDirectory: "C:\\Users\\alice" },
        { T3CODE_HOME: t3Home },
        NodePath.layerWin32,
      );

      assert.equal(environment.baseDir, baseDir);
      assert.equal(environment.stateDir, `${baseDir}\\userdata`);
    }),
  );

  it.effect("resolves a relative Windows T3CODE_HOME against the desktop's cwd", () =>
    Effect.gen(function* () {
      const environment = yield* makeEnvironment(
        { platform: "win32", homeDirectory: "C:\\Users\\alice", isPackaged: true },
        { T3CODE_HOME: "state\\t3" },
        NodePath.layerWin32,
      );

      assert.equal(environment.baseDir, environment.path.join(process.cwd(), "state", "t3"));
    }),
  );
});
