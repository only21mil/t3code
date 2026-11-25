import { requireNativeView, requireOptionalNativeModule } from "expo";
import type { NativeSyntheticEvent, ViewProps } from "react-native";

type WindowState = "active" | "closed";

interface ObserverProps extends ViewProps {
  readonly onWindowStateChange: (
    event: NativeSyntheticEvent<{ readonly state: WindowState }>,
  ) => void;
}

// Binaries from before multiple windows have no observer and only ever one window.
const Observer = requireOptionalNativeModule("T3WindowState")
  ? requireNativeView<ObserverProps>("T3WindowState")
  : null;

/** Reports when the activity of the React root it is mounted in gains focus, or is destroyed. */
export function NativeWindowObserver(props: { readonly onChange: (state: WindowState) => void }) {
  return Observer ? (
    <Observer
      pointerEvents="none"
      onWindowStateChange={(event) => props.onChange(event.nativeEvent.state)}
      style={{ position: "absolute", width: 0, height: 0 }}
    />
  ) : null;
}
