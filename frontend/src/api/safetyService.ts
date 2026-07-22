
import type {
  ProfileReportPayload,
  ProfileSafetyActionResponse,
} from "../types/safety";


function readCookie(name: string): string {
  const prefix = `${encodeURIComponent(name)}=`;

  for (const rawPart of document.cookie.split(";")) {
    const part = rawPart.trim();

    if (part.startsWith(prefix)) {
      return decodeURIComponent(
        part.slice(prefix.length),
      );
    }
  }

  return "";
}


async function requestJson<T>(
  url: string,
  payload: unknown,
): Promise<T> {
  const csrfToken = readCookie("csrftoken");

  const response = await fetch(url, {
    method: "POST",
    credentials: "include",
    headers: {
      Accept: "application/json",
      "Content-Type": "application/json",
      ...(csrfToken
        ? {"X-CSRFToken": csrfToken}
        : {}),
    },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    let message = "Cette action n’a pas pu être effectuée.";

    try {
      const data = await response.json() as {
        detail?: string | string[];
        non_field_errors?: string[];
      };

      if (typeof data.detail === "string") {
        message = data.detail;
      } else if (Array.isArray(data.detail)) {
        message = data.detail.join(" ");
      } else if (
        Array.isArray(data.non_field_errors)
      ) {
        message = data.non_field_errors.join(" ");
      }
    } catch {
      // Conserve le message générique.
    }

    throw new Error(message);
  }

  return response.json() as Promise<T>;
}


export async function blockProfile(
  profileId: string,
): Promise<ProfileSafetyActionResponse> {
  return requestJson<ProfileSafetyActionResponse>(
    `/api/v1/safety/profiles/${encodeURIComponent(profileId)}/block/`,
    {confirm: true},
  );
}


export async function reportProfile(
  profileId: string,
  payload: ProfileReportPayload,
): Promise<ProfileSafetyActionResponse> {
  return requestJson<ProfileSafetyActionResponse>(
    `/api/v1/safety/profiles/${encodeURIComponent(profileId)}/report/`,
    payload,
  );
}
