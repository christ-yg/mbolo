
import type {
  BlockedUsersPaginatedResponse,
  ProfileReportPayload,
  ProfileSafetyActionResponse,
  UserReportsPaginatedResponse,
} from "../types/safety";

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

async function readError(response: Response): Promise<string> {
  try {
    const data = await response.json() as {
      detail?: string | string[];
      non_field_errors?: string[];
    };

    if (typeof data.detail === "string") {
      return data.detail;
    }

    if (Array.isArray(data.detail)) {
      return data.detail.join(" ");
    }

    if (Array.isArray(data.non_field_errors)) {
      return data.non_field_errors.join(" ");
    }
  } catch {
    // Réponse non JSON.
  }

  return "Cette action n’a pas pu être effectuée.";
}

async function postJson<T>(
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
      ...(csrfToken ? {"X-CSRFToken": csrfToken} : {}),
    },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    throw new Error(await readError(response));
  }

  return response.json() as Promise<T>;
}

export async function blockProfile(
  profileId: string,
): Promise<ProfileSafetyActionResponse> {
  return postJson<ProfileSafetyActionResponse>(
    `/api/v1/safety/profiles/${encodeURIComponent(profileId)}/block/`,
    {confirm: true},
  );
}

export async function reportProfile(
  profileId: string,
  payload: ProfileReportPayload,
): Promise<ProfileSafetyActionResponse> {
  return postJson<ProfileSafetyActionResponse>(
    `/api/v1/safety/profiles/${encodeURIComponent(profileId)}/report/`,
    payload,
  );
}

export async function getBlockedUsers(
  page = 1,
  pageSize = 20,
): Promise<BlockedUsersPaginatedResponse> {
  const params = new URLSearchParams({
    page: String(page),
    page_size: String(pageSize),
  });

  const response = await fetch(
    `/api/v1/safety/blocks/?${params.toString()}`,
    {
      method: "GET",
      credentials: "include",
      headers: {Accept: "application/json"},
    },
  );

  if (!response.ok) {
    throw new Error(await readError(response));
  }

  return response.json() as Promise<BlockedUsersPaginatedResponse>;
}

export async function unblockUser(
  blockId: string,
): Promise<void> {
  const csrfToken = readCookie("csrftoken");

  const response = await fetch(
    `/api/v1/safety/blocks/${encodeURIComponent(blockId)}/`,
    {
      method: "DELETE",
      credentials: "include",
      headers: {
        Accept: "application/json",
        ...(csrfToken ? {"X-CSRFToken": csrfToken} : {}),
      },
    },
  );

  if (!response.ok) {
    throw new Error(await readError(response));
  }
}

export async function getMyReports(
  page = 1,
  pageSize = 20,
): Promise<UserReportsPaginatedResponse> {
  const params = new URLSearchParams({
    page: String(page),
    page_size: String(pageSize),
  });

  const response = await fetch(
    `/api/v1/safety/reports/?${params.toString()}`,
    {
      method: "GET",
      credentials: "include",
      headers: {Accept: "application/json"},
    },
  );

  if (!response.ok) {
    throw new Error(await readError(response));
  }

  return response.json() as Promise<UserReportsPaginatedResponse>;
}
