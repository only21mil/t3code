export function NativeWindowObserver(_props: {
  /** Whether this window's navigation hears opened links yet (Android holds them until then). */
  readonly hearsLinks: boolean;
  readonly onChange: (state: "active" | "closed") => void;
}) {
  return null;
}
