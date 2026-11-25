import { requireNativeView, requireOptionalNativeModule } from "expo";
import type { NativeSyntheticEvent, ViewProps } from "react-native";
import type { NativeLayoutMetrics } from "../lib/reserved-regions";

interface ObserverProps extends ViewProps {
  readonly onMetricsChange?: (event: NativeSyntheticEvent<NativeLayoutMetrics>) => void;
}

// Binaries from before multiple windows have no observer; the app then reads React Native's one
// window size.
const Observer = requireOptionalNativeModule("T3LayoutMetrics")
  ? requireNativeView<ObserverProps>("T3LayoutMetrics")
  : null;

// A screen's own observer reports nothing on Android, as before multiple windows: screens size
// from the window's metrics (native-layout-metrics) or their own layout.
export function NativeLayoutObserver(_props: {
  readonly onChange?: (metrics: NativeLayoutMetrics) => void;
}) {
  return null;
}

/** The React root's own size and safe area: side by side, each window has its own. */
export function NativeWindowLayoutObserver(props: {
  readonly onChange?: (metrics: NativeLayoutMetrics) => void;
}) {
  return Observer ? (
    <Observer
      pointerEvents="none"
      onMetricsChange={props.onChange ? (event) => props.onChange?.(event.nativeEvent) : undefined}
      style={{ position: "absolute", top: 0, bottom: 0, left: 0, right: 0 }}
    />
  ) : null;
}
