import { HeaderHeightContext } from "@react-navigation/elements";
import { useState, type ReactNode } from "react";
import { StyleSheet, View, type ColorValue } from "react-native";
import { SafeAreaProvider, SafeAreaView } from "react-native-safe-area-context";
import { NativeColumnLayoutMetricsContext } from "./native-layout-metrics";
import type { NativeLayoutMetrics } from "../lib/reserved-regions";
import { NativeLayoutObserver } from "./NativeLayoutObserver";
import { NativeColumnLeavesHorizontalInsets } from "./v5-workspace-context";

export function NativeColumnContent(props: {
  readonly children: ReactNode;
  readonly primary?: boolean;
  readonly insetHorizontally?: boolean;
  readonly backgroundColor?: ColorValue;
}) {
  const [metrics, setMetrics] = useState<NativeLayoutMetrics | null>(null);
  const leavesInsets = props.insetHorizontally === false;
  return (
    <View
      className={props.primary ? "flex-1 bg-drawer" : "flex-1 bg-screen"}
      style={
        props.backgroundColor === undefined ? undefined : { backgroundColor: props.backgroundColor }
      }
    >
      <SafeAreaProvider style={{ flex: 1 }}>
        <SafeAreaView edges={leavesInsets ? [] : ["left", "right"]} style={{ flex: 1 }}>
          {/* Observe the inset body. UIKit can reserve other columns in its safe area. Content
              that runs under those insets still reports the inset body, so layouts sized from
              these metrics don't change. */}
          <View style={{ flex: 1 }}>
            {leavesInsets ? (
              <SafeAreaView
                edges={["left", "right"]}
                pointerEvents="none"
                style={StyleSheet.absoluteFill}
              >
                <View style={{ flex: 1 }}>
                  <NativeLayoutObserver onChange={setMetrics} />
                </View>
              </SafeAreaView>
            ) : (
              <NativeLayoutObserver onChange={setMetrics} />
            )}
            <NativeColumnLayoutMetricsContext value={metrics}>
              <HeaderHeightContext value={metrics?.safeArea.top ?? undefined}>
                <NativeColumnLeavesHorizontalInsets value={leavesInsets}>
                  {props.children}
                </NativeColumnLeavesHorizontalInsets>
              </HeaderHeightContext>
            </NativeColumnLayoutMetricsContext>
          </View>
        </SafeAreaView>
      </SafeAreaProvider>
    </View>
  );
}
