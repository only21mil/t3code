import { it } from "@effect/vitest";
import * as Effect from "effect/Effect";
import * as Layer from "effect/Layer";
import * as Option from "effect/Option";
import * as Schema from "effect/Schema";
import { expect } from "vite-plus/test";

import * as ElectronWindow from "../electron/ElectronWindow.ts";
import * as DesktopIpc from "./DesktopIpc.ts";

const mainFrame = {};
const mainWindow = { webContents: { id: 1, mainFrame } };

const fromMainWindow = { sender: { id: 1 }, senderFrame: mainFrame };
const fromSubframe = { sender: { id: 1 }, senderFrame: {} };
const fromPreviewGuest = { sender: { id: 2 }, senderFrame: {} };

const registerSecretChannels = (main: Option.Option<typeof mainWindow>) => {
  const invokeListeners = new Map<string, DesktopIpc.DesktopIpcHandleListener>();
  const syncListeners = new Map<string, DesktopIpc.DesktopIpcSyncListener>();
  let handlerRuns = 0;
  const secret = Effect.sync(() => {
    handlerRuns += 1;
    return "secret";
  });
  const install = Effect.gen(function* () {
    const ipc = yield* DesktopIpc.DesktopIpc;
    yield* ipc.handle(
      DesktopIpc.makeIpcMethod({
        channel: "test:secret",
        payload: Schema.Void,
        result: Schema.String,
        handler: () => secret,
      }),
    );
    yield* ipc.handleSync(
      DesktopIpc.makeSyncIpcMethod({
        channel: "test:secret-sync",
        result: Schema.String,
        handler: () => secret,
      }),
    );
  }).pipe(
    Effect.provide(
      DesktopIpc.layer({
        removeHandler: (channel) => invokeListeners.delete(channel),
        handle: (channel, listener) => invokeListeners.set(channel, listener),
        removeAllListeners: (channel) => syncListeners.delete(channel),
        on: (channel, listener) => syncListeners.set(channel, listener),
      }).pipe(
        Layer.provide(
          Layer.succeed(ElectronWindow.ElectronWindow, {
            main: Effect.succeed(main),
          } as unknown as ElectronWindow.ElectronWindow["Service"]),
        ),
      ),
    ),
  );
  const invoke = (event: DesktopIpc.DesktopIpcInvokeEvent) =>
    Effect.promise(() =>
      Promise.resolve(invokeListeners.get("test:secret")!(event, undefined)).then(
        (value) => ({ ok: true, value }),
        () => ({ ok: false }),
      ),
    );
  const invokeSync = (event: DesktopIpc.DesktopIpcInvokeEvent) =>
    Effect.sync(() => {
      const syncEvent: DesktopIpc.DesktopIpcSyncEvent = { ...event, returnValue: undefined };
      syncListeners.get("test:secret-sync")!(syncEvent);
      return syncEvent.returnValue;
    });
  return { install, invoke, invokeSync, handlerRuns: () => handlerRuns };
};

it.effect("runs privileged handlers only for the main window's top frame", () =>
  Effect.scoped(
    Effect.gen(function* () {
      const channels = registerSecretChannels(Option.some(mainWindow));
      yield* channels.install;

      expect(yield* channels.invoke(fromPreviewGuest)).toEqual({ ok: false });
      expect(yield* channels.invoke(fromSubframe)).toEqual({ ok: false });
      expect(yield* channels.invokeSync(fromPreviewGuest)).toBeNull();
      expect(yield* channels.invokeSync(fromSubframe)).toBeNull();
      expect(channels.handlerRuns()).toBe(0);

      expect(yield* channels.invoke(fromMainWindow)).toEqual({ ok: true, value: "secret" });
      expect(yield* channels.invokeSync(fromMainWindow)).toBe("secret");
      expect(channels.handlerRuns()).toBe(2);
    }),
  ),
);

it.effect("rejects every sender while no main window exists", () =>
  Effect.scoped(
    Effect.gen(function* () {
      const channels = registerSecretChannels(Option.none());
      yield* channels.install;

      expect(yield* channels.invoke(fromMainWindow)).toEqual({ ok: false });
      expect(yield* channels.invokeSync(fromMainWindow)).toBeNull();
      expect(channels.handlerRuns()).toBe(0);
    }),
  ),
);
