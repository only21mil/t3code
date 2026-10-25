import * as NodeHttpClient from "@effect/platform-node/NodeHttpClient";
import * as HostProcess from "@t3tools/shared/HostProcess";
import * as SourceControlHost from "@t3tools/source-control-core/server/SourceControlHost";
import * as Data from "effect/Data";
import * as Effect from "effect/Effect";
import { HttpClient, HttpClientError, HttpClientRequest } from "effect/http";
import * as Layer from "effect/Layer";
import * as Scope from "effect/Scope";
import * as PlatformError from "effect/PlatformError";

import { GH_PROCESS_CONCURRENCY } from "./GitHubCredentials.ts";

class GitHubSocketConfigError extends Data.TaggedError("GitHubSocketConfigError")<{
  readonly detail: string;
}> {}

const make = Effect.gen(function* () {
  const ordinary = yield* HttpClient.HttpClient;
  const host = yield* SourceControlHost.SourceControlHost;
  const cwd = yield* HostProcess.WorkingDirectory;
  const scope = yield* Scope.Scope;

  // Resolve once, lazily, so constructing an unused driver does not spawn gh.
  const transport = yield* Effect.gen(function* () {
    const config = yield* host.process
      .run({
        operation: "GitHubHttpClient.config",
        command: "gh",
        args: ["config", "get", "http_unix_socket"],
        cwd,
        env: { GH_DEBUG: "", GH_PROMPT_DISABLED: "1" },
        timeoutMs: 10_000,
        maxOutputBytes: 16_384,
        allowNonZeroExit: true,
        concurrency: GH_PROCESS_CONCURRENCY,
      })
      .pipe(
        Effect.catchIf(
          // gh is optional when credentials come from settings or the environment.
          (error) =>
            error._tag === "VcsProcessSpawnError" &&
            error.cause instanceof PlatformError.PlatformError &&
            error.cause.reason._tag === "NotFound",
          () => Effect.succeed(null),
        ),
      );
    if (config === null) return null;
    if (config.stdoutTruncated || config.stderrTruncated) {
      return yield* new GitHubSocketConfigError({
        detail: "gh socket configuration was truncated",
      });
    }
    if (config.exitCode !== 0) {
      if (config.exitCode === 1 && config.stderr.trim() === 'could not find key "http_unix_socket"')
        return null;
      return yield* new GitHubSocketConfigError({
        detail: "Could not read gh socket configuration",
      });
    }
    if (config.stdout.trim() === "") return null;
    const agent = yield* NodeHttpClient.makeAgent({ socketPath: config.stdout.trim() });
    return yield* NodeHttpClient.makeNodeHttp.pipe(
      Effect.provideService(NodeHttpClient.HttpAgent, agent),
    );
  }).pipe(Effect.provideService(Scope.Scope, scope), Effect.cached);

  return HttpClient.make((request) =>
    transport.pipe(
      Effect.mapError(
        (cause) =>
          new HttpClientError.HttpClientError({
            reason: new HttpClientError.TransportError({ request, cause }),
          }),
      ),
      Effect.flatMap((socket) => {
        if (socket === null) return ordinary.execute(request);
        const url = new URL(request.url);
        const authority = url.host;
        // gh's socket peer receives plain HTTP even for a logical HTTPS API URL.
        url.protocol = "http:";
        return socket.execute(
          request.pipe(
            HttpClientRequest.setUrl(url),
            HttpClientRequest.setHeader("host", authority),
          ),
        );
      }),
    ),
  );
});

export const layer = Layer.effect(HttpClient.HttpClient, make);
