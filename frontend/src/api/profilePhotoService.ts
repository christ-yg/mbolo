import type {
  ProfilePhoto,
  ProfilePhotoListResponse,
  ProfilePhotoMutationResponse,
} from "../types/profilePhotos";

export class ProfilePhotoApiError extends Error {
  public constructor(message: string) {
    super(message);
    this.name = "ProfilePhotoApiError";
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

function findMessage(value: unknown): string | null {
  if (typeof value === "string") return value;
  if (Array.isArray(value)) {
    const messages = value.filter((item): item is string => typeof item === "string");
    return messages.length > 0 ? messages.join(" ") : null;
  }
  if (value && typeof value === "object") {
    for (const nested of Object.values(value as Record<string, unknown>)) {
      const message = findMessage(nested);
      if (message) return message;
    }
  }
  return null;
}

async function throwApiError(response: Response): Promise<never> {
  let message = "L’opération sur la photo a échoué.";
  try {
    const payload = await response.json() as unknown;
    message = findMessage(payload) ?? message;
  } catch {
    // On conserve un message générique sans exposer le serveur.
  }
  throw new ProfilePhotoApiError(message);
}

export async function getMyProfilePhotos(): Promise<ProfilePhotoListResponse> {
  const response = await fetch("/api/v1/profiles/photos/", {
    method: "GET",
    credentials: "include",
    headers: {Accept: "application/json"},
  });
  if (!response.ok) return throwApiError(response);
  return response.json() as Promise<ProfilePhotoListResponse>;
}

export async function uploadProfilePhoto(
  image: File,
  isPrimary: boolean,
): Promise<ProfilePhotoMutationResponse> {
  const data = new FormData();
  data.append("image", image);
  data.append("is_primary", isPrimary ? "true" : "false");

  const response = await fetch("/api/v1/profiles/photos/", {
    method: "POST",
    credentials: "include",
    headers: {
      Accept: "application/json",
      "X-CSRFToken": readCookie("csrftoken"),
    },
    body: data,
  });
  if (!response.ok) return throwApiError(response);
  return response.json() as Promise<ProfilePhotoMutationResponse>;
}

export async function setPrimaryProfilePhoto(
  photoId: string,
): Promise<ProfilePhotoMutationResponse> {
  const response = await fetch(`/api/v1/profiles/photos/${photoId}/`, {
    method: "PATCH",
    credentials: "include",
    headers: {
      Accept: "application/json",
      "Content-Type": "application/json",
      "X-CSRFToken": readCookie("csrftoken"),
    },
    body: JSON.stringify({is_primary: true}),
  });
  if (!response.ok) return throwApiError(response);
  return response.json() as Promise<ProfilePhotoMutationResponse>;
}

export async function deleteProfilePhoto(photoId: string): Promise<void> {
  const response = await fetch(`/api/v1/profiles/photos/${photoId}/`, {
    method: "DELETE",
    credentials: "include",
    headers: {
      Accept: "application/json",
      "X-CSRFToken": readCookie("csrftoken"),
    },
  });
  if (!response.ok) return throwApiError(response);
}

export function sortProfilePhotos(photos: ProfilePhoto[]): ProfilePhoto[] {
  return [...photos].sort((first, second) => first.position - second.position);
}
