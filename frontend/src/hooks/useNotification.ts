import { useContext } from "react";

import {
  NotificationContext,
  type NotificationContextValue,
} from "../context/notificationContextDefinition";

export function useNotification(): NotificationContextValue {
  const context = useContext(NotificationContext);

  if (context === undefined) {
    throw new Error(
      "useNotification doit être utilisé dans NotificationProvider.",
    );
  }

  return context;
}
