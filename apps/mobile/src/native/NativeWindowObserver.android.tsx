import { requireNativeView, requireOptionalNativeModule } from "expo";
import {
  BackHandler,
  DeviceEventEmitter,
  type NativeSyntheticEvent,
  type ViewProps,
} from "react-native";

import { activateAppWindow, useAppWindowId, type AppWindowId } from "../lib/appWindows";

type WindowState = "active" | "closed";

interface ObserverProps extends ViewProps {
  readonly windowId: number;
  readonly onWindowStateChange: (
    event: NativeSyntheticEvent<{ readonly state: WindowState }>,
  ) => void;
}

const WindowStateModule = requireOptionalNativeModule<{
  readonly runDefaultBack?: (windowId: AppWindowId) => Promise<void>;
}>("T3WindowState");

// Binaries from before multiple windows have no observer and only ever one window.
const Observer = WindowStateModule ? requireNativeView<ObserverProps>("T3WindowState") : null;

// Back and links reach JS app-wide; T3WindowReactActivityDelegate first sends, on the same
// channel, the id of their window or of a window it starts serving. Listening from load, JS hears
// every id native code knows (until then native code keeps Back and links in that window), even
// one that arrives before its root's effect registers the window.
let announcedWindowId: AppWindowId | null = null;
DeviceEventEmitter.addListener("T3WindowInUse", (id: AppWindowId) => {
  announcedWindowId = id;
  activateAppWindow(id);
});

// The oldest Back listener, so it hears only presses no window took. React Native's own default
// Back would act on whichever window the host serves when this runs, so the window the press came
// from, announced right before it, closes or backgrounds instead; native code drops it if that
// window has closed since.
if (WindowStateModule?.runDefaultBack) {
  BackHandler.addEventListener("hardwareBackPress", () => {
    if (announcedWindowId === null) return false;
    void WindowStateModule.runDefaultBack?.(announcedWindowId);
    return true;
  });
}

/** Reports when the activity of the React root it is mounted in is destroyed. */
export function NativeWindowObserver(props: {
  readonly hearsLinks: boolean;
  readonly onChange: (state: WindowState) => void;
}) {
  const windowId = useAppWindowId();
  return Observer ? (
    <Observer
      pointerEvents="none"
      // Native code delivers a link it held for this window once its navigation can open it.
      windowId={props.hearsLinks ? windowId : 0}
      onWindowStateChange={(event) => props.onChange(event.nativeEvent.state)}
      style={{ position: "absolute", width: 0, height: 0 }}
    />
  ) : null;
}
