
import type {
  DiscoveryPreferences,
  UpdateDiscoveryPreferencesPayload,
} from "../types/discoveryPreferences";

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

async function parseResponse<T>(
  response: Response,
): Promise<T> {
  if (!response.ok) {
    let message =
      "Les préférences n’ont pas pu être enregistrées.";

    try {
      const payload = await response.json() as Record<
        string,
        unknown
      >;

      const detail = payload.detail;

      if (typeof detail === "string") {
        message = detail;
      } else {
        const firstValue = Object.values(payload)[0];

        if (
          Array.isArray(firstValue) &&
          typeof firstValue[0] === "string"
        ) {
          message = firstValue.join(" ");
        }
      }
    } catch {
      // Réponse non JSON.
    }

    throw new Error(message);
  }

  return response.json() as Promise<T>;
}

export async function getDiscoveryPreferences():
Promise<DiscoveryPreferences> {
  const response = await fetch(
    "/api/v1/profiles/preferences/me/",
    {
      method: "GET",
      credentials: "include",
      headers: {
        Accept: "application/json",
      },
    },
  );

  return parseResponse<DiscoveryPreferences>(response);
}

export async function updateDiscoveryPreferences(
  payload: UpdateDiscoveryPreferencesPayload,
): Promise<DiscoveryPreferences> {
  const csrfToken = readCookie("csrftoken");

  const response = await fetch(
    "/api/v1/profiles/preferences/me/",
    {
      method: "PATCH",
      credentials: "include",
      headers: {
        Accept: "application/json",
        "Content-Type": "application/json",
        ...(csrfToken
          ? {"X-CSRFToken": csrfToken}
          : {}),
      },
      body: JSON.stringify(payload),
    },
  );

  return parseResponse<DiscoveryPreferences>(response);
}
