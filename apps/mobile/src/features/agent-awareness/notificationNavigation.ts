import { deviceEvent, deviceNavigate, deviceRegister, deviceClear, devicePath } from "./deviceEvidence";
import { useEffect, useLayoutEffect, useRef } from "react";
import * as Notifications from "expo-notifications";
import { useLinkTo } from "@react-navigation/native";

import { setAndroidThreadOnScreen } from "./androidNotifications";
import { foregroundNotificationBehavior } from "./foregroundNotificationBehavior";
import { routeAgentNotificationResponseOnce, threadDeepLinkOnScreen } from "./notificationPayload";
import { consumeLastAgentNotificationResponse } from "./notificationResponseConsumer";

export function useAgentNotificationNavigation(pathname: string): void {
  const linkTo = useLinkTo();
  devicePath(pathname);
  const handledResponseIds = useRef(new Set<string>());
  const deepLinkOnScreen = useRef<string | null>(null);
  useLayoutEffect(() => {
    const thread = threadDeepLinkOnScreen(pathname);
    deepLinkOnScreen.current = thread;
    setAndroidThreadOnScreen(thread);
  }, [pathname]);

  useEffect(() => {
    Notifications.setNotificationHandler({
      handleNotification: (notification) =>
        Promise.resolve(foregroundNotificationBehavior(notification, deepLinkOnScreen.current)),
    });
    return () => {
      Notifications.setNotificationHandler(null);
    };
  }, []);

  useEffect(() => {
    const handleResponse = (response: Notifications.NotificationResponse): void => {
      deviceEvent("route", response);
      routeAgentNotificationResponseOnce({
        handledResponseIds: handledResponseIds.current,
        response,
        navigate: (deepLink) => deviceNavigate(response, deepLink, linkTo),
      });
    };

    const subscription = Notifications.addNotificationResponseReceivedListener((r) => { deviceEvent("listener", r); try { handleResponse(r); } catch { deviceEvent("listener error", r); } });
    const consume = () => consumeLastAgentNotificationResponse({
      getLastResponse: async () => { const r = await Notifications.getLastNotificationResponseAsync(); if(r) deviceEvent("initial", r); return r; },
      clearLastResponse: async () => { await Notifications.clearLastNotificationResponseAsync(); deviceClear(); },
      handleResponse,
    });

    deviceRegister(consume);
    void consume();
    return () => {
      subscription.remove();
    };
  }, [linkTo]);
}
