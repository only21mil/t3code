import * as Cause from "effect/Cause";
import * as Clock from "effect/Clock";
import * as Effect from "effect/Effect";
import * as Exit from "effect/Exit";
import * as Option from "effect/Option";
import type * as HttpServerRequest from "effect/http/HttpServerRequest";
import * as Socket from "effect/socket/Socket";

const ADDRESS_MAX_CHARS = 64;

/** What the server saw of one `/ws` connection before it ended. */
export interface WsConnectionObservation {
  closeCode: number | undefined;
  closeReasonLength: number | undefined;
  lastInboundAtMs: number | undefined;
  invalidated: boolean;
}

export const makeObservation = (): WsConnectionObservation => ({
  closeCode: undefined,
  closeReasonLength: undefined,
  lastInboundAtMs: undefined,
  invalidated: false,
});

const observeSocket = (socket: Socket.Socket, observation: WsConnectionObservation) => {
  const recordClose = (error: Socket.SocketError) =>
    Effect.sync(() => {
      if (error.reason._tag !== "SocketCloseError") return;
      observation.closeCode = error.reason.code;
      observation.closeReasonLength = error.reason.closeReason?.length;
    });
  return Socket.make({
    // An already-closed socket fails while its reader is acquired, before any pull.
    reader: socket.reader.pipe(
      Effect.tapError(recordClose),
      Effect.map((reader) => ({
        ...reader,
        pull: reader.pull.pipe(
          Effect.tap(() =>
            Clock.currentTimeMillis.pipe(
              Effect.map((now) => {
                observation.lastInboundAtMs = now;
              }),
            ),
          ),
          Effect.tapError(recordClose),
        ),
      })),
    ),
    writer: socket.writer,
  });
};

/**
 * Effect's RPC server catches the close error its socket reader raises, so the close
 * code exists only inside the reader. This request upgrades to a socket that keeps it.
 */
export const observeUpgrade = (
  request: HttpServerRequest.HttpServerRequest,
  observation: WsConnectionObservation,
): HttpServerRequest.HttpServerRequest =>
  // A prototype wrapper rather than a Proxy: a Proxy must return the target's own value
  // for a non-configurable `upgrade`, so it cannot replace it.
  Object.create(request, {
    upgrade: {
      value: Effect.map(request.upgrade, (socket) => observeSocket(socket, observation)),
    },
  });

/**
 * 1006 means the TCP connection ended with no close frame: a network drop, a killed
 * client, or a proxy that gave up. Any other code came in a close frame.
 */
export const wsCloseAttributes = (input: {
  readonly observation: WsConnectionObservation;
  readonly exit: Exit.Exit<unknown, unknown>;
  readonly connectedAtMs: number;
  readonly closedAtMs: number;
}) => {
  const { observation, exit, connectedAtMs, closedAtMs } = input;
  const endedBy = observation.invalidated
    ? "session_invalidated"
    : observation.closeCode === 1006
      ? "connection_lost"
      : observation.closeCode !== undefined
        ? "close_frame"
        : Exit.isFailure(exit) && Cause.hasInterruptsOnly(exit.cause)
          ? "server_interrupted"
          : Exit.isFailure(exit)
            ? "server_error"
            : "unknown";
  return {
    endedBy,
    ...(observation.closeCode === undefined ? {} : { closeCode: observation.closeCode }),
    ...(observation.closeReasonLength ? { closeReasonLength: observation.closeReasonLength } : {}),
    durationMs: closedAtMs - connectedAtMs,
    ...(observation.lastInboundAtMs === undefined
      ? {}
      : { lastInboundAgeMs: closedAtMs - observation.lastInboundAtMs }),
  };
};

/** Who is on the other end. A forwarded address is what the proxy reported. */
export const wsPeerAttributes = (request: HttpServerRequest.HttpServerRequest) => {
  const remoteAddress = Option.getOrUndefined(request.remoteAddress);
  const forwardedFor = request.headers["x-forwarded-for"]?.split(",")[0]?.trim();
  return {
    ...(remoteAddress ? { remoteAddress: remoteAddress.slice(0, ADDRESS_MAX_CHARS) } : {}),
    ...(forwardedFor ? { forwardedFor: forwardedFor.slice(0, ADDRESS_MAX_CHARS) } : {}),
  };
};
