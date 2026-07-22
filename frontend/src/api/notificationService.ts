
/**
 * Client HTTP du centre de notifications.
 *
 * Les requêtes d'écriture envoient le cookie CSRF Django.
 * credentials: "include" conserve la session Django.
 */

import type {
  MarkAllNotificationsReadResponse,
  NotificationItem,
  NotificationsPaginatedResponse,
  NotificationUnreadCountResponse,
} from "../types/notifications";

function readCookie(name: string): string {
  const prefix = `${encodeURIComponent(name)}=`;

  for (const rawPart of document.cookie.split(";")) {
    const part = rawPart.trim();

    if (part.startsWith(prefix)) {
      return decodeURIComponent(part.slice(prefix.length));
    }
  }

  return "";
}

async function parseJsonResponse<T>(
  response: Response,
): Promise<T> {
  if (!response.ok) {
    let message = "Une erreur est survenue.";

    try {
      const payload = await response.json() as {
        detail?: string;
      };

      if (
        typeof payload.detail === "string" &&
        payload.detail.trim()
      ) {
        message = payload.detail;
      }
    } catch {
      // Une réponse non JSON garde le message générique.
    }

    throw new Error(message);
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return response.json() as Promise<T>;
}

function mutationHeaders(): HeadersInit {
  const csrfToken = readCookie("csrftoken");

  return {
    "Content-Type": "application/json",
    ...(csrfToken
      ? {"X-CSRFToken": csrfToken}
      : {}),
  };
}

export async function getNotifications(
  page = 1,
  pageSize = 20,
): Promise<NotificationsPaginatedResponse> {
  const parameters = new URLSearchParams({
    page: String(page),
    page_size: String(pageSize),
  });

  const response = await fetch(
    `/api/v1/notifications/?${parameters.toString()}`,
    {
      method: "GET",
      credentials: "include",
      headers: {
        Accept: "application/json",
      },
    },
  );

  return parseJsonResponse<NotificationsPaginatedResponse>(
    response,
  );
}

export async function getNotificationUnreadCount():
Promise<NotificationUnreadCountResponse> {
  const response = await fetch(
    "/api/v1/notifications/unread-count/",
    {
      method: "GET",
      credentials: "include",
      headers: {
        Accept: "application/json",
      },
    },
  );

  return parseJsonResponse<NotificationUnreadCountResponse>(
    response,
  );
}

export async function markNotificationRead(
  notificationId: string,
): Promise<NotificationItem> {
  const response = await fetch(
    `/api/v1/notifications/${encodeURIComponent(notificationId)}/read/`,
    {
      method: "POST",
      credentials: "include",
      headers: mutationHeaders(),
      body: "{}",
    },
  );

  return parseJsonResponse<NotificationItem>(response);
}

export async function markAllNotificationsRead():
Promise<MarkAllNotificationsReadResponse> {
  const response = await fetch(
    "/api/v1/notifications/read-all/",
    {
      method: "POST",
      credentials: "include",
      headers: mutationHeaders(),
      body: "{}",
    },
  );

  return parseJsonResponse<MarkAllNotificationsReadResponse>(
    response,
  );
}

export async function deleteNotification(
  notificationId: string,
): Promise<void> {
  const response = await fetch(
    `/api/v1/notifications/${encodeURIComponent(notificationId)}/`,
    {
      method: "DELETE",
      credentials: "include",
      headers: mutationHeaders(),
    },
  );

  await parseJsonResponse<void>(response);
}
