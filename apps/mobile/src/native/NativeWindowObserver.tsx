export function NativeWindowObserver(_props: {
  /** Whether this window's navigation hears opened links yet (Android holds them until then). */
  readonly hearsLinks: boolean;
  /** Whether this window's navigation container is ready to open them. */
  readonly navigationReady: boolean;
  readonly onChange: (state: "active" | "closed") => void;
}) {
  return null;
}

/** Android delivers a link a window held to that window alone. */
export function listenForHeldLinks(_windowId: number, _listener: (url: string) => void) {
  return () => {};
}
