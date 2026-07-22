/** Hub singleton du canal temps réel global du compte. */

import {
  AccountSocket,
  type AccountSocketEvent,
  type AccountSocketState,
} from "./accountSocket";

type Listener = () => void;

interface AccountRealtimeSnapshot {
  state: AccountSocketState;
  unreadCount: number;
  notificationUnreadCount: number;
  lastEvent: AccountSocketEvent | null;
  revision: number;
}

class AccountRealtimeHub {
  private socket: AccountSocket | null = null;
  private activeUserId: string | null = null;
  private listeners = new Set<Listener>();
  private snapshot: AccountRealtimeSnapshot = {
    state: "closed",
    unreadCount: 0,
    notificationUnreadCount: 0,
    lastEvent: null,
    revision: 0,
  };

  start(userId: string): void {
    if (this.activeUserId === userId && this.socket !== null) {
      return;
    }
    this.stop();
    this.activeUserId = userId;
    this.socket = new AccountSocket(
      (event) => this.handleEvent(event),
      (state) => {
        this.snapshot = { ...this.snapshot, state };
        this.emit();
      },
    );
    this.socket.connect();
  }

  stop(): void {
    this.socket?.close();
    this.socket = null;
    this.activeUserId = null;
    this.snapshot = {
      state: "closed",
      unreadCount: 0,
      notificationUnreadCount: 0,
      lastEvent: null,
      revision: this.snapshot.revision + 1,
    };
    this.emit();
  }

  refreshUnreadCount(): boolean {
    return this.socket?.send({ event: "unread.refresh" }) ?? false;
  }

  subscribe(listener: Listener): () => void {
    this.listeners.add(listener);
    return () => this.listeners.delete(listener);
  }

  getSnapshot(): AccountRealtimeSnapshot {
    return this.snapshot;
  }

  private handleEvent(event: AccountSocketEvent): void {
    const rawUnreadCount = event.unread_count;
    const unreadCount =
      typeof rawUnreadCount === "number" && Number.isFinite(rawUnreadCount)
        ? Math.max(0, Math.floor(rawUnreadCount))
        : this.snapshot.unreadCount;

    const rawNotificationUnreadCount =
      event.notification_unread_count;

    const notificationUnreadCount =
      typeof rawNotificationUnreadCount === "number" &&
      Number.isFinite(rawNotificationUnreadCount)
        ? Math.max(
            0,
            Math.floor(rawNotificationUnreadCount),
          )
        : this.snapshot.notificationUnreadCount;

    this.snapshot = {
      ...this.snapshot,
      unreadCount,
      notificationUnreadCount,
      lastEvent: event,
      revision: this.snapshot.revision + 1,
    };
    this.emit();
  }

  private emit(): void {
    for (const listener of this.listeners) {
      listener();
    }
  }
}

export const accountRealtimeHub = new AccountRealtimeHub();
