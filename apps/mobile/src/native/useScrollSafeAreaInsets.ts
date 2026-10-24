import { useState } from "react";
import { useWindowDimensions } from "react-native";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import { holdExpandedTopInset, type HeldTopInset } from "./holdExpandedTopInset";

/**
 * Safe-area insets for scroll views that set their own top inset. Following the live top while
 * the bar minimizes moves the content under the finger, which UIKit reads as a reversed scroll
 * that restores the bar, and the list stutters between the two.
 */
export function useScrollSafeAreaInsets() {
  const insets = useSafeAreaInsets();
  const { width, height } = useWindowDimensions();
  const [held, setHeld] = useState<HeldTopInset>({ width, height, top: insets.top });
  const next = holdExpandedTopInset(held, { width, height, top: insets.top });
  if (next !== held) setHeld(next);
  return next.top === insets.top ? insets : { ...insets, top: next.top };
}
