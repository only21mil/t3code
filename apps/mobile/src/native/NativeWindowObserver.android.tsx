import { requireNativeView, requireOptionalNativeModule } from "expo";
import { DeviceEventEmitter, type NativeSyntheticEvent, type ViewProps } from "react-native";

import { activateAppWindow, useAppWindowId } from "../lib/appWindows";

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

// Back and opened links reach JS app-wide; T3WindowReactActivityDelegate first sends the id of
// the window they came from on the same channel. Listening from load means a window's id reaches
// native code only once JS can hear it: until then native code keeps Back in that window. The id
// can arrive before its root's own effect opens the window.
DeviceEventEmitter.addListener("T3WindowInUse", (id: number) => activateAppWindow(id));

/** Reports when the activity of the React root it is mounted in gains focus, or is destroyed. */
export function NativeWindowObserver(props: { readonly onChange: (state: WindowState) => void }) {
  const windowId = useAppWindowId();
  return Observer ? (
    <Observer
      pointerEvents="none"
      windowId={windowId}
      onWindowStateChange={(event) => props.onChange(event.nativeEvent.state)}
      style={{ position: "absolute", width: 0, height: 0 }}
    />
  ) : null;
}
