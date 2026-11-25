import { requireNativeView, requireOptionalNativeModule } from "expo";
import { useEffect, useEffectEvent } from "react";
import { DeviceEventEmitter, type NativeSyntheticEvent, type ViewProps } from "react-native";

import { useAppWindowId } from "../lib/appWindows";

type WindowState = "active" | "closed";

interface ObserverProps extends ViewProps {
  readonly windowId: number;
  readonly onWindowStateChange: (
    event: NativeSyntheticEvent<{ readonly state: WindowState }>,
  ) => void;
}

// Binaries from before multiple windows have no observer and only ever one window.
const Observer = requireOptionalNativeModule("T3WindowState")
  ? requireNativeView<ObserverProps>("T3WindowState")
  : null;

/**
 * Reports when the activity of the React root it is mounted in gains focus, or is destroyed. Back
 * and opened links reach JS app-wide; T3WindowReactActivityDelegate first sends the id of the
 * window they came from on the same channel, so that window is the active one when they arrive.
 */
export function NativeWindowObserver(props: { readonly onChange: (state: WindowState) => void }) {
  const windowId = useAppWindowId();
  const onChange = useEffectEvent(props.onChange);
  // oxlint-disable-next-line t3code/no-unreasoned-state-sync -- native code names the window Back or a link came from just before it reaches JS
  useEffect(() => {
    const subscription = DeviceEventEmitter.addListener("T3WindowInUse", (id: number) => {
      if (id === windowId) onChange("active");
    });
    return () => subscription.remove();
  }, [windowId]);
  return Observer ? (
    <Observer
      pointerEvents="none"
      windowId={windowId}
      onWindowStateChange={(event) => props.onChange(event.nativeEvent.state)}
      style={{ position: "absolute", width: 0, height: 0 }}
    />
  ) : null;
}
