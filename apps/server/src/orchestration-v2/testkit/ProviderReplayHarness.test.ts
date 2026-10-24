import * as NodeOS from "node:os";

import * as NodeServices from "@effect/platform-node/NodeServices";
import { assert, it } from "@effect/vitest";
import type { ProviderReplayTranscript } from "@t3tools/contracts";
import * as Effect from "effect/Effect";
import * as FileSystem from "effect/FileSystem";
import * as Layer from "effect/Layer";

import { AcpRegistryOrchestratorReplayHarness } from "../Adapters/AcpRegistryAdapterV2.testkit.ts";
import { CodexOrchestratorReplayHarness } from "../Adapters/CodexAdapterV2.testkit.ts";
import { GrokOrchestratorReplayHarness } from "../Adapters/GrokAdapterV2.testkit.ts";
import { readReplayFixtureTranscript } from "./ProviderReplayFixtures.ts";
import {
  layerProviderReplay,
  type OrchestratorV2ProviderReplayHarness,
} from "./ProviderReplayHarness.ts";

const tempDirectoriesNamed = Effect.fn(function* (prefixes: ReadonlyArray<string>) {
  const entries = yield* (yield* FileSystem.FileSystem).readDirectory(NodeOS.tmpdir());
  return entries.filter((entry) => prefixes.some((prefix) => entry.startsWith(prefix)));
});

const assertReplayLayerDeletesTempDirectories = <
  Transcript extends ProviderReplayTranscript,
  Error,
>(
  harness: OrchestratorV2ProviderReplayHarness<Transcript, Error>,
  fixture: string,
  providerPrefix: string,
) =>
  Effect.gen(function* () {
    const scenario = `temp-cleanup-${harness.driver}`;
    const recorded = yield* readReplayFixtureTranscript(new URL(fixture, import.meta.url));
    const transcript = yield* harness.decodeTranscript({ ...recorded, scenario });
    const prefixes = [`t3-orchestration-v2-replay-${scenario}-`, `${providerPrefix}${scenario}-`];

    // Diff against a snapshot so directories leaked by an earlier broken run don't count.
    const before = new Set(yield* tempDirectoriesNamed(prefixes));
    const whileOpen = yield* Effect.gen(function* () {
      yield* Layer.build(
        layerProviderReplay({ name: scenario, commands: [], transcript }, harness, {
          runEffectWorker: false,
        }),
      );
      return (yield* tempDirectoriesNamed(prefixes)).filter((entry) => !before.has(entry));
    }).pipe(Effect.scoped);

    assert.deepEqual(
      prefixes.map((prefix) => whileOpen.filter((entry) => entry.startsWith(prefix)).length),
      [1, 1],
    );
    const afterClose = new Set(yield* tempDirectoriesNamed(prefixes));
    assert.deepEqual(
      whileOpen.filter((entry) => afterClose.has(entry)),
      [],
    );
  }).pipe(Effect.provide(NodeServices.layer));

it.effect("Codex replay deletes its temp directories when the replay layer closes", () =>
  assertReplayLayerDeletesTempDirectories(
    CodexOrchestratorReplayHarness,
    "./fixtures/simple/codex_transcript.ndjson",
    "t3-orchestration-v2-codex-",
  ),
);

it.effect("Grok replay deletes its temp directories when the replay layer closes", () =>
  assertReplayLayerDeletesTempDirectories(
    GrokOrchestratorReplayHarness,
    "./fixtures/simple/grok_transcript.ndjson",
    "t3-orchestration-v2-grok-replay-",
  ),
);

it.effect("ACP registry replay deletes its temp directories when the replay layer closes", () =>
  assertReplayLayerDeletesTempDirectories(
    AcpRegistryOrchestratorReplayHarness,
    "./fixtures/simple/registry_transcript.ndjson",
    "t3-orchestration-v2-acp-registry-replay-",
  ),
);
