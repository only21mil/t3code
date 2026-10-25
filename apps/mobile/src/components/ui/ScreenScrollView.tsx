import { createContext, use, type ComponentProps, type ReactNode } from "react";
import { Platform, StyleSheet } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";
import { withUniwind } from "uniwind";
import { cn } from "../../lib/cn";
import { NativeScrollView as ScrollView } from "../../native/NativeScrollViewMarker";
import { NativeColumnLeavesHorizontalInsets } from "../../native/v5-workspace-context";

export const ScreenScrollViewBottomInset = createContext(0);
/**
 * The screen's surface class. UIKit's scroll-edge material under the header takes the scroll
 * view's own color; a clear scroll view gets the system's near-white bar over the screen's surface.
 */
export const ScreenScrollViewSurface = createContext<string | undefined>(undefined);

const InsetContent = withUniwind(SafeAreaView);

/**
 * A list's content inside its scroll view: takes the column's left and right safe areas
 * natively when the column leaves them to the screen (see ScreenScrollView).
 */
/**
 * Overlays above a screen whose column leaves its left and right safe areas to it: a layer that
 * fills the screen minus those safe areas, applied natively. Children position against it.
 */
export function ColumnInsetLayer(props: { readonly children: ReactNode }) {
  return Platform.OS === "ios" && use(NativeColumnLeavesHorizontalInsets) ? (
    <SafeAreaView
      edges={["left", "right"]}
      mode="margin"
      pointerEvents="box-none"
      style={StyleSheet.absoluteFill}
    >
      {props.children}
    </SafeAreaView>
  ) : (
    props.children
  );
}

export function ColumnInsetContent(props: { readonly children: ReactNode }) {
  return Platform.OS === "ios" && use(NativeColumnLeavesHorizontalInsets) ? (
    <InsetContent edges={["left", "right"]} style={{ flexGrow: 1 }}>
      {props.children}
    </InsetContent>
  ) : (
    props.children
  );
}

export function ScreenScrollView(props: ComponentProps<typeof ScrollView>) {
  const bottomInset = use(ScreenScrollViewBottomInset);
  const surface = use(ScreenScrollViewSurface);
  // The scroll view spans the column and its content takes the left and right safe areas
  // natively, the way UIKit insets table rows, so folds and rotation move both in one layout.
  const insetContent = Platform.OS === "ios" && use(NativeColumnLeavesHorizontalInsets);
  const { children, contentContainerClassName, contentContainerStyle, ...scrollViewProps } = props;
  return (
    <ScrollView
      {...scrollViewProps}
      className={Platform.OS === "ios" && surface ? cn(surface, props.className) : props.className}
      contentInset={
        Platform.OS === "ios" && bottomInset > 0
          ? { ...props.contentInset, bottom: (props.contentInset?.bottom ?? 0) + bottomInset }
          : props.contentInset
      }
      {...(insetContent
        ? { contentContainerStyle: { flexGrow: 1 } }
        : {
            contentContainerClassName,
            contentContainerStyle: [
              contentContainerStyle,
              Platform.OS === "android" && {
                width: "100%",
                maxWidth: 720,
                alignSelf: "center",
              },
            ],
          })}
    >
      {insetContent ? (
        <InsetContent
          edges={["left", "right"]}
          className={contentContainerClassName}
          style={contentContainerStyle}
        >
          {children}
        </InsetContent>
      ) : (
        children
      )}
    </ScrollView>
  );
}
