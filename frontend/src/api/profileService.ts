/**
 * Service HTTP du profil personnel.
 *
 * L'URL ne contient aucun UUID choisi par le navigateur. Django déduit le
 * propriétaire à partir de la session, ce qui limite le risque d'IDOR.
 */

import type {
  EditableProfile,
  ProfileFieldErrors,
  UpdateProfilePayload,
} from "../types/profileEdit";

export class ProfileUpdateError extends Error {
  public readonly fieldErrors: ProfileFieldErrors;

  public constructor(
    message: string,
    fieldErrors: ProfileFieldErrors = {},
  ) {
    super(message);
    this.name = "ProfileUpdateError";
    this.fieldErrors = fieldErrors;
  }
}

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

function firstMessage(value: unknown): string | null {
  if (typeof value === "string") {
    return value;
  }

  if (Array.isArray(value)) {
    const messages = value.filter(
      (item): item is string => typeof item === "string",
    );

    return messages.length > 0 ? messages.join(" ") : null;
  }

  return null;
}

async function parseProfileResponse(
  response: Response,
): Promise<EditableProfile> {
  if (response.ok) {
    return response.json() as Promise<EditableProfile>;
  }

  const fieldErrors: ProfileFieldErrors = {};
  let message = "Le profil n’a pas pu être enregistré.";

  try {
    const payload = await response.json() as Record<string, unknown>;
    const detail = firstMessage(payload.detail);

    if (detail !== null) {
      message = detail;
    }

    for (const [field, value] of Object.entries(payload)) {
      const fieldMessage = firstMessage(value);

      if (fieldMessage !== null) {
        (fieldErrors as Record<string, string>)[field] = fieldMessage;
        if (detail === null) {
          message = fieldMessage;
        }
      }
    }
  } catch {
    // Une réponse non JSON conserve le message générique et n'expose pas
    // d'information technique interne à l'utilisateur.
  }

  throw new ProfileUpdateError(message, fieldErrors);
}

export async function getMyProfile(): Promise<EditableProfile> {
  const response = await fetch("/api/v1/profiles/me/", {
    method: "GET",
    credentials: "include",
    headers: {Accept: "application/json"},
  });

  return parseProfileResponse(response);
}

export async function updateMyProfile(
  payload: UpdateProfilePayload,
): Promise<EditableProfile> {
  const csrfToken = readCookie("csrftoken");

  const response = await fetch("/api/v1/profiles/me/", {
    method: "PATCH",
    credentials: "include",
    headers: {
      Accept: "application/json",
      "Content-Type": "application/json",
      ...(csrfToken ? {"X-CSRFToken": csrfToken} : {}),
    },
    body: JSON.stringify(payload),
  });

  return parseProfileResponse(response);
}
