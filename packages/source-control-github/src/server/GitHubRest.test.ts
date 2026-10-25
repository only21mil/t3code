import * as NodeServices from "@effect/platform-node/NodeServices";
import * as FileSystem from "effect/FileSystem";
import * as HostProcess from "@t3tools/shared/HostProcess";
import { HttpClientError } from "effect/http";
// @effect-diagnostics-next-line nodeBuiltinImport:off - A real HTTP socket peer verifies the transport, not a mocked client.
import * as NodeHttp from "node:http";
import { driver } from "./driver.ts";
import { describe, expect, it } from "@effect/vitest";
import * as NodeCrypto from "@effect/platform-node/NodeCrypto";
import * as Effect from "effect/Effect";
import * as Layer from "effect/Layer";
import * as Redacted from "effect/Redacted";
import * as TestClock from "effect/testing/TestClock";
import * as Tracer from "effect/Tracer";
import { ChildProcessSpawner } from "effect/process";
import * as PlatformError from "effect/PlatformError";
import { VcsProcessSpawnError, VcsProcessTimeoutError } from "@t3tools/contracts";
import { HttpClient, HttpClientResponse, type HttpClientRequest } from "effect/http";

import * as GitHubRest from "./GitHubRest.ts";
import * as GitHubRequestPolicy from "./GitHubRequestPolicy.ts";
import * as GitHubCredentials from "./GitHubCredentials.ts";
import * as GitHubQuota from "./GitHubQuota.ts";
import * as SourceControlRateLimit from "@t3tools/source-control-core/server/SourceControlRateLimit";
import type * as SourceControlHost from "@t3tools/source-control-core/server/SourceControlHost";
import * as TestSourceControlHost from "@t3tools/source-control-testing/TestSourceControlHost";

const NOW = Date.parse("2026-10-05T12:00:00.000Z");

function harness(respond: (request: HttpClientRequest.HttpClientRequest) => Response) {
  const requests: Array<HttpClientRequest.HttpClientRequest> = [];
  let tokens = ["first", "second"];
  let invalidations = 0;
  let credentialReads = 0;
  const credentials = Layer.succeed(
    GitHubCredentials.GitHubCredentials,
    GitHubCredentials.GitHubCredentials.of({
      get: (host) =>
        Effect.sync(() => {
          credentialReads++;
          return {
            host,
            token: Redacted.make(tokens[0]!),
            source: "gh" as const,
            fingerprint: `${host}:${tokens[0]}`,
          };
        }),
      invalidate: () =>
        Effect.sync(() => {
          invalidations++;
          tokens = tokens.slice(1);
        }),
    }),
  );
  const http = Layer.succeed(
    HttpClient.HttpClient,
    HttpClient.make((request) => {
      requests.push(request);
      return Effect.succeed(HttpClientResponse.fromWeb(request, respond(request)));
    }),
  );
  const layer = GitHubRest.layer.pipe(
    Layer.provide(Layer.mergeAll(credentials, http)),
    Layer.provideMerge(GitHubQuota.layer),
    Layer.provideMerge(SourceControlRateLimit.layer),
  );
  return {
    layer,
    requests,
    invalidations: () => invalidations,
    credentialReads: () => credentialReads,
  };
}

const json = (body: unknown, init?: ResponseInit) =>
  new Response(JSON.stringify(body), {
    ...init,
    headers: { "content-type": "application/json", ...init?.headers },
  });

describe("environmentToken", () => {
  it("follows gh's precedence per kind of host", () => {
    const env = { GH_TOKEN: "gh", GITHUB_TOKEN: "github", GH_ENTERPRISE_TOKEN: "ghe" };
    expect(GitHubCredentials.environmentToken("github.com", env)).toBe("gh");
    expect(GitHubCredentials.environmentToken("acme.ghe.com", { GITHUB_TOKEN: "github" })).toBe(
      "github",
    );
    expect(GitHubCredentials.environmentToken("git.acme.internal", env)).toBeNull();
    expect(
      GitHubCredentials.environmentToken("git.acme.internal", {
        ...env,
        GH_HOST: "git.acme.internal",
      }),
    ).toBe("ghe");
    expect(GitHubCredentials.environmentToken("git.acme.internal", { GH_TOKEN: "gh" })).toBeNull();
  });
});

describe("GitHubRest", () => {
  it.effect("traces the operation, path and quota, never the query string or the token", () => {
    const spans: Array<Tracer.NativeSpan> = [];
    const tracer = Tracer.make({
      span: (options) => {
        const span = new Tracer.NativeSpan(options);
        spans.push(span);
        return span;
      },
    });
    const { layer } = harness(() =>
      json({ ok: true }, { headers: { "x-ratelimit-remaining": "4800" } }),
    );
    return Effect.gen(function* () {
      yield* TestClock.setTime(NOW);
      const api = yield* GitHubRest.GitHubRest;
      yield* api.rest({
        host: "github.com",
        operation: "listWorkflowRuns",
        path: "repos/acme/web/actions/runs?head_sha=abc123&branch=feat%2Fx",
      });
      const send = spans.find((span) => span.name === "GitHubRest.send")!;
      expect(Object.fromEntries(send.attributes)).toMatchObject({
        "github.operation": "listWorkflowRuns",
        "github.kind": "rest",
        "url.path": "/repos/acme/web/actions/runs",
        "http.response.status_code": 200,
        "github.ratelimit.remaining": 4800,
      });
      const everything = spans
        .flatMap((span) => [...span.attributes].map(([key, value]) => `${key}=${String(value)}`))
        .join("\n");
      expect(everything).not.toContain("head_sha");
      expect(everything).not.toContain("first");
      expect(spans.some((span) => span.attributes.has("url.full"))).toBe(false);
    }).pipe(Effect.provide(layer), Effect.withTracer(tracer));
  });

  it.effect("lets an interactive request through a pause a background read recorded", () => {
    const reset = Math.floor(NOW / 1000) + 600;
    let call = 0;
    const { layer, requests } = harness(() =>
      ++call === 1
        ? json(
            { message: "API rate limit exceeded" },
            {
              status: 403,
              headers: { "x-ratelimit-remaining": "0", "x-ratelimit-reset": String(reset) },
            },
          )
        : json({ ok: true }),
    );
    return Effect.gen(function* () {
      yield* TestClock.setTime(NOW);
      const api = yield* GitHubRest.GitHubRest;
      const read = { host: "github.com", operation: "sweep", path: "repos/acme/web/pulls" };
      yield* Effect.flip(api.rest(read));
      expect((yield* Effect.flip(api.rest(read)))._tag).toBe("SourceControlRateLimitPausedError");
      const merged = yield* api
        .rest({
          host: "github.com",
          operation: "merge",
          method: "PUT",
          path: "repos/acme/web/pulls/7/merge",
        })
        .pipe(Effect.provideService(SourceControlRateLimit.Interactive, true));
      expect(merged.status).toBe(200);
      expect(requests).toHaveLength(2);
    }).pipe(Effect.provide(layer));
  });

  it.effect("maps REST 403 with an exhausted quota to a rate limit, and 304 to an answer", () => {
    let call = 0;
    const { layer } = harness(() =>
      ++call === 1
        ? new Response(null, { status: 304 })
        : json(
            { message: "API rate limit exceeded" },
            {
              status: 403,
              headers: { "retry-after": "60" },
            },
          ),
    );
    return Effect.gen(function* () {
      yield* TestClock.setTime(NOW);
      const api = yield* GitHubRest.GitHubRest;
      const notModified = yield* api.rest({
        host: "github.com",
        operation: "checks",
        path: "repos/acme/web/pulls/7",
        ifNoneMatch: '"abc"',
      });
      expect(notModified.status).toBe(304);
      const error = yield* Effect.flip(
        api.rest({ host: "github.com", operation: "checks", path: "repos/acme/web/pulls/7" }),
      );
      expect(error).toMatchObject({ _tag: "GitHubApiRateLimitError", retryAt: NOW + 60_000 });
    }).pipe(Effect.provide(layer));
  });

  it.effect("drops a refused token so the next request asks the source again", () => {
    const { layer, requests, invalidations } = harness((request) =>
      request.headers.authorization === "Bearer first"
        ? new Response(null, { status: 401 })
        : json({ ok: true }),
    );
    return Effect.gen(function* () {
      const api = yield* GitHubRest.GitHubRest;
      const refused = yield* Effect.flip(
        api.rest({ host: "github.com", operation: "user", path: "user" }),
      );
      expect(refused._tag).toBe("GitHubApiAuthenticationError");
      expect(invalidations()).toBe(1);
      const answered = yield* api.rest({ host: "github.com", operation: "user", path: "user" });
      expect(answered.status).toBe(200);
      expect(requests.map((request) => request.headers.authorization)).toEqual([
        "Bearer first",
        "Bearer second",
      ]);
    }).pipe(Effect.provide(layer));
  });

  it.effect("refuses to send a pinned credential to another host", () => {
    const { layer, requests } = harness(() => json({}));
    return Effect.gen(function* () {
      const api = yield* GitHubRest.GitHubRest;
      const error = yield* Effect.flip(
        api.rest({ host: "git.acme.internal", operation: "user", path: "user" }),
      ).pipe(
        Effect.provideService(GitHubRequestPolicy.PinnedGitHubCredential, {
          host: "github.com",
          token: Redacted.make("pinned"),
          credentialFingerprint: "github.com:pinned",
        }),
      );
      expect(error._tag).toBe("GitHubApiAuthenticationError");
      expect(requests).toHaveLength(0);
    }).pipe(Effect.provide(layer));
  });
});

describe("GitHubCredentials", () => {
  const credentialsWith = (run: SourceControlHost.SourceControlHost["Service"]["process"]["run"]) =>
    GitHubCredentials.layer.pipe(
      Layer.provide(TestSourceControlHost.layer({ process: { run } })),
      Layer.provide(NodeCrypto.layer),
    );

  it.effect("does not cache a gh failure that is not about signing in", () => {
    let calls = 0;
    return Effect.gen(function* () {
      const credentials = yield* GitHubCredentials.GitHubCredentials;
      const first = yield* Effect.flip(credentials.get("github.com"));
      expect(first._tag).toBe("GitHubCliFailedError");
      expect((yield* credentials.get("github.com")).source).toBe("gh");
      expect(calls).toBe(2);
    }).pipe(
      Effect.provide(
        credentialsWith(() =>
          ++calls === 1
            ? Effect.fail(
                new VcsProcessTimeoutError({
                  operation: "GitHubCredentials.get",
                  command: "gh",
                  cwd: "/",
                  timeoutMs: 10_000,
                }),
              )
            : Effect.succeed({
                exitCode: ChildProcessSpawner.ExitCode(0),
                stdout: "token\n",
                stderr: "",
                stdoutTruncated: false,
                stderrTruncated: false,
              }),
        ),
      ),
    );
  });

  it.effect("fails with GitHubNotSignedInError when gh prints no token", () =>
    Effect.gen(function* () {
      const credentials = yield* GitHubCredentials.GitHubCredentials;
      const error = yield* Effect.flip(credentials.get("git.acme.internal"));
      expect(error._tag).toBe("GitHubNotSignedInError");
    }).pipe(
      Effect.provide(
        credentialsWith(() =>
          Effect.succeed({
            exitCode: ChildProcessSpawner.ExitCode(0),
            stdout: "\n",
            stderr: "",
            stdoutTruncated: false,
            stderrTruncated: false,
          }),
        ),
      ),
    ),
  );
});

describe("GitHub driver Unix socket REST", () => {
  const readStack = Effect.gen(function* () {
    const instance = yield* driver.make;
    return yield* instance.pullRequests!.getChangeRequestStack!({
      cwd: "/fixture",
      repository: "acme/web",
      host: "github.com",
      number: 7,
    });
  }).pipe(Effect.provideService(HostProcess.Environment, {}));

  const services = (socketPath: string, ordinary: HttpClient.HttpClient, missingKey = false) =>
    Layer.mergeAll(
      NodeServices.layer,
      NodeCrypto.layer,
      SourceControlRateLimit.layer,
      Layer.succeed(HttpClient.HttpClient, ordinary),
      TestSourceControlHost.layer({
        process: {
          run: (input) => {
            expect(input.command).toBe("gh");
            if (input.args[0] === "config") {
              expect(input.args).toEqual(["config", "get", "http_unix_socket"]);
              return Effect.succeed(
                TestSourceControlHost.processOutput(
                  socketPath + "\n",
                  missingKey
                    ? {
                        exitCode: ChildProcessSpawner.ExitCode(1),
                        stderr: 'could not find key "http_unix_socket"\n',
                      }
                    : undefined,
                ),
              );
            }
            expect(input.args).toEqual(["auth", "token", "--hostname", "github.com"]);
            return Effect.succeed(TestSourceControlHost.processOutput("placeholder\n"));
          },
        },
      }),
    );

  // quarantine: #24958 This fixture exercises Unix-domain sockets on Linux and macOS.
  it.live("reads REST through gh's plain HTTP socket with the API authority and query", (context) =>
    Effect.gen(function* () {
      if ((yield* HostProcess.Platform) === "win32") return context.skip();
      const fs = yield* FileSystem.FileSystem;
      const dir = yield* fs.makeTempDirectoryScoped();
      const socketPath = `${dir}/gh.sock`;
      const received: Array<{
        host: string | undefined;
        path: string | undefined;
        auth: string | undefined;
      }> = [];
      const server = NodeHttp.createServer((request, response) => {
        received.push({
          host: request.headers.host,
          path: request.url,
          auth: request.headers.authorization,
        });
        response.setHeader("content-type", "application/json");
        response.end("[]");
      });
      yield* Effect.acquireRelease(
        Effect.callback<void>((resume) => {
          server.once("error", (error) => resume(Effect.die(error)));
          server.listen(socketPath, () => resume(Effect.void));
        }),
        () =>
          Effect.promise(
            () =>
              new Promise<void>((resolve, reject) =>
                server.close((error) => (error ? reject(error) : resolve())),
              ),
          ),
      );
      const ordinaryRequests: Array<string> = [];
      const ordinary = HttpClient.make((request) => {
        ordinaryRequests.push(request.url);
        return Effect.fail(
          new HttpClientError.HttpClientError({
            reason: new HttpClientError.TransportError({
              request,
              cause: "ordinary-client sentinel",
            }),
          }),
        );
      });
      yield* Effect.gen(function* () {
        const instance = yield* driver.make;
        expect(
          yield* instance.pullRequests!.getChangeRequestStack!({
            cwd: "/fixture",
            repository: "acme/web",
            host: "github.com",
            number: 7,
          }),
        ).toBeNull();
        const mediaError = yield* Effect.flip(
          instance.fetchMedia!({
            url: "https://objects.example.test/file.png",
            headers: {},
          }),
        );
        expect(mediaError.reason._tag).toBe("TransportError");
      }).pipe(
        Effect.provideService(HostProcess.Environment, {}),
        Effect.provide(services(socketPath, ordinary)),
      );
      expect(ordinaryRequests).toEqual(["https://objects.example.test/file.png"]);
      expect(received).toEqual([
        {
          host: "api.github.com",
          path: "/repos/acme/web/stacks?pull_request=7",
          auth: "Bearer placeholder",
        },
      ]);
    }).pipe(Effect.scoped, Effect.provide(NodeServices.layer)),
  );

  // quarantine: #24958 This fixture exercises Unix-domain sockets on Linux and macOS.
  it.live("never falls back to the ordinary client when the configured socket fails", (context) =>
    Effect.gen(function* () {
      if ((yield* HostProcess.Platform) === "win32") return context.skip();
      const fs = yield* FileSystem.FileSystem;
      const dir = yield* fs.makeTempDirectoryScoped();
      let ordinaryCalls = 0;
      const ordinary = HttpClient.make((request) => {
        ordinaryCalls++;
        return Effect.succeed(HttpClientResponse.fromWeb(request, json([])));
      });
      const error = yield* Effect.flip(
        readStack.pipe(Effect.provide(services(`${dir}/missing.sock`, ordinary))),
      );
      expect(error.reason).toBe("failed");
      expect(ordinaryCalls).toBe(0);
    }).pipe(Effect.scoped, Effect.provide(NodeServices.layer)),
  );

  it.live.each([false, true])(
    "retains the ordinary client for unset gh config, missing key: %s",
    (missingKey) => {
      const requests: Array<HttpClientRequest.HttpClientRequest> = [];
      const ordinary = HttpClient.make((request) => {
        requests.push(request);
        return Effect.succeed(HttpClientResponse.fromWeb(request, json([])));
      });
      return Effect.gen(function* () {
        expect(yield* readStack).toBeNull();
        expect(requests.map((request) => request.url)).toEqual([
          "https://api.github.com/repos/acme/web/stacks?pull_request=7",
        ]);
      }).pipe(Effect.scoped, Effect.provide(services("", ordinary, missingKey)));
    },
  );

  it.live.each(["NotFound", "PermissionDenied"] as const)(
    "preserves environment credentials when the gh config process fails with %s",
    (tag) => {
      const requests: Array<HttpClientRequest.HttpClientRequest> = [];
      return Effect.gen(function* () {
        const instance = yield* driver.make;
        const read = instance.pullRequests!.getChangeRequestStack!({
          cwd: "/fixture",
          repository: "acme/web",
          host: "github.com",
          number: 7,
        });
        if (tag === "NotFound") {
          expect(yield* read).toBeNull();
          expect(requests[0]?.headers.authorization).toBe("Bearer environment-placeholder");
        } else {
          expect((yield* Effect.flip(read)).reason).toBe("failed");
          expect(requests).toHaveLength(0);
        }
      }).pipe(
        Effect.scoped,
        Effect.provideService(HostProcess.Environment, { GH_TOKEN: "environment-placeholder" }),
        Effect.provide(
          Layer.mergeAll(
            NodeServices.layer,
            NodeCrypto.layer,
            SourceControlRateLimit.layer,
            Layer.succeed(
              HttpClient.HttpClient,
              HttpClient.make((request) => {
                requests.push(request);
                return Effect.succeed(HttpClientResponse.fromWeb(request, json([])));
              }),
            ),
            TestSourceControlHost.layer({
              process: {
                run: (input) => {
                  expect(input.args).toEqual(["config", "get", "http_unix_socket"]);
                  return Effect.fail(
                    new VcsProcessSpawnError({
                      operation: input.operation,
                      command: input.command,
                      cwd: input.cwd,
                      cause: new PlatformError.PlatformError(
                        new PlatformError.SystemError({
                          _tag: tag,
                          module: "ChildProcess",
                          method: "spawn",
                        }),
                      ),
                    }),
                  );
                },
              },
            }),
          ),
        ),
      );
    },
  );
});
