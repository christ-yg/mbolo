
/**
 * Types publics du centre de notifications Mbolo.
 */

export type NotificationKind =
  | "message"
  | "match"
  | "like"
  | "super_like"
  | "security"
  | "system";

export interface NotificationItem {
  id: string;
  kind: NotificationKind;
  title: string;
  body: string;
  target_path: string;
  is_read: boolean;
  read_at: string | null;
  created_at: string;
}

export interface NotificationsPaginatedResponse {
  count: number;
  next: string | null;
  previous: string | null;
  results: NotificationItem[];
}

export interface NotificationUnreadCountResponse {
  unread_count: number;
}

export interface MarkAllNotificationsReadResponse {
  marked_count: number;
  read_at: string;
}

export interface NotificationPreferences {
  notifications_enabled: boolean;
  messages_enabled: boolean;
  matches_enabled: boolean;
  likes_enabled: boolean;
  security_enabled: true;
  quiet_hours_enabled: boolean;
  quiet_start: string;
  quiet_end: string;
  timezone_offset_minutes: number;
  updated_at: string;
}

export type NotificationPreferencesUpdate = Omit<
  NotificationPreferences,
  "security_enabled" | "updated_at"
>;
