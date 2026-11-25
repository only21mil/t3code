import { StackActions, useFocusEffect, useNavigation } from "@react-navigation/native";
import { useCallback } from "react";
import { Keyboard, Platform } from "react-native";
import { returnToAndroidWorkspaceList } from "../../../lib/android-workspace-navigation";
import { useAppWindowId } from "../../../lib/appWindows";
import { addWindowBackListener } from "../../../lib/backHandler";

export function useWorkspaceBackNavigation() {
  const navigation = useNavigation();
  return () => {
    if (Platform.OS === "android") returnToAndroidWorkspaceList(navigation);
    else if (navigation.canGoBack()) navigation.goBack();
    else navigation.dispatch(StackActions.replace("Home"));
  };
}

export function useAndroidWorkspaceBack() {
  const goBack = useWorkspaceBackNavigation();
  const windowId = useAppWindowId();
  useFocusEffect(
    useCallback(() => {
      if (Platform.OS !== "android") return;
      const subscription = addWindowBackListener(windowId, () => {
        if (Keyboard.isVisible()) Keyboard.dismiss();
        else goBack();
        return true;
      });
      return () => subscription.remove();
    }, [goBack, windowId]),
  );
  return goBack;
}
