import { createContext } from "react";

export interface RealtimeNotification {
  id: string;
  kind: "message" | "like" | "match" | "system" | "security";
  title: string;
  body: string;
  targetPath: string;
  displayName: string;
  createdAt: string;
}

export type BrowserNotificationPermission =
  | NotificationPermission
  | "unsupported";

export interface NotificationContextValue {
  notification: RealtimeNotification | null;
  dismissNotification: () => void;
  browserNotificationsSupported: boolean;
  browserNotificationPermission: BrowserNotificationPermission;
  browserNotificationsEnabled: boolean;
  enableBrowserNotifications: () => Promise<boolean>;
  disableBrowserNotifications: () => void;
}

export const NotificationContext =
  createContext<NotificationContextValue | undefined>(undefined);
