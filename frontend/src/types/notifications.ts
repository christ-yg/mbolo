
/**
 * Types publics du centre de notifications Mbolo.
 */

export type NotificationKind =
  | "message"
  | "match"
  | "like"
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
