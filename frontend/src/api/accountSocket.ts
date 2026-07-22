/** Client WebSocket global du compte authentifié Mbolo. */

export type AccountSocketState = "connecting" | "open" | "closed";

export interface AccountSocketEvent {
  event: string;
  [key: string]: unknown;
}

function buildAccountSocketUrl(): string {
  const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
  const configuredHost = import.meta.env.VITE_WEBSOCKET_HOST?.trim();
  const backendHost = configuredHost || "127.0.0.1:8000";
  return `${protocol}//${backendHost}/ws/account/`;
}

export class AccountSocket {
  private readonly onEvent: (event: AccountSocketEvent) => void;
  private readonly onStateChange: (state: AccountSocketState) => void;
  private socket: WebSocket | null = null;
  private reconnectTimer: number | null = null;
  private reconnectAttempt = 0;
  private intentionallyClosed = false;

  constructor(
    onEvent: (event: AccountSocketEvent) => void,
    onStateChange: (state: AccountSocketState) => void,
  ) {
    this.onEvent = onEvent;
    this.onStateChange = onStateChange;
  }

  connect(): void {
    if (
      this.socket?.readyState === WebSocket.OPEN ||
      this.socket?.readyState === WebSocket.CONNECTING
    ) {
      return;
    }

    this.intentionallyClosed = false;
    this.onStateChange("connecting");

    const socket = new WebSocket(buildAccountSocketUrl());
    this.socket = socket;

    socket.onopen = () => {
      if (this.socket !== socket) {
        socket.close(1000, "stale_connection");
        return;
      }
      this.reconnectAttempt = 0;
      this.onStateChange("open");
    };

    socket.onmessage = (messageEvent: MessageEvent) => {
      try {
        const parsed = JSON.parse(String(messageEvent.data)) as AccountSocketEvent;
        if (
          typeof parsed !== "object" ||
          parsed === null ||
          typeof parsed.event !== "string"
        ) {
          return;
        }
        this.onEvent(parsed);
      } catch {
        // Une trame invalide ne doit jamais casser l'application.
      }
    };

    socket.onclose = () => {
      if (this.socket !== socket) {
        return;
      }
      this.socket = null;
      this.onStateChange("closed");
      if (!this.intentionallyClosed) {
        this.scheduleReconnect();
      }
    };

    socket.onerror = () => {
      if (this.socket === socket) {
        socket.close();
      }
    };
  }

  send(event: AccountSocketEvent): boolean {
    if (this.socket?.readyState !== WebSocket.OPEN) {
      return false;
    }
    try {
      this.socket.send(JSON.stringify(event));
      return true;
    } catch {
      return false;
    }
  }

  close(): void {
    this.intentionallyClosed = true;
    if (this.reconnectTimer !== null) {
      window.clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }
    const currentSocket = this.socket;
    this.socket = null;
    if (
      currentSocket &&
      (currentSocket.readyState === WebSocket.OPEN ||
        currentSocket.readyState === WebSocket.CONNECTING)
    ) {
      currentSocket.close(1000, "session_closed");
    }
    this.onStateChange("closed");
  }

  private scheduleReconnect(): void {
    if (this.reconnectTimer !== null) {
      return;
    }
    const delay = Math.min(1000 * 2 ** this.reconnectAttempt, 15000);
    this.reconnectAttempt += 1;
    this.reconnectTimer = window.setTimeout(() => {
      this.reconnectTimer = null;
      if (!this.intentionallyClosed) {
        this.connect();
      }
    }, delay);
  }
}
