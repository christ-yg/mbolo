/** Accès React au canal temps réel global du compte. */

import { useSyncExternalStore } from "react";

import { accountRealtimeHub } from "../api/accountRealtime";

export function useAccountRealtime() {
  const snapshot = useSyncExternalStore(
    (listener) => accountRealtimeHub.subscribe(listener),
    () => accountRealtimeHub.getSnapshot(),
    () => accountRealtimeHub.getSnapshot(),
  );

  return {
    ...snapshot,
    isConnected: snapshot.state === "open",
    refreshUnreadCount: () => accountRealtimeHub.refreshUnreadCount(),
  };
}
