/**
 * Service d'authentification du frontend Mbolo.
 *
 * Toutes les communications avec Django passent par ce fichier.
 *
 * Responsabilités :
 *
 * - créer un compte ;
 * - confirmer une adresse e-mail ;
 * - ouvrir une session ;
 * - fermer une session ;
 * - récupérer l'utilisateur actuellement connecté ;
 * - normaliser les différentes formes de réponses du backend.
 */

import type { ApiSuccessResponse } from "../types/api";

import type {
  AuthenticatedUser,
  ChangePasswordPayload,
  CurrentPasswordPayload,
  DeactivateAccountPayload,
  DeleteAccountPayload,
  LoginPayload,
  LoginResponseData,
  PasswordResetConfirmPayload,
  PasswordResetRequestPayload,
  RegisterPayload,
  RegisterResponseData,
  VerifyEmailPayload,
  VerifyEmailResponseData,
} from "../types/auth";

import {
  clearInMemoryCsrfToken,
  ensureCsrfToken,
} from "./csrfService";

import { httpClient } from "./httpClient";


/**
 * Certaines routes Django renvoient :
 *
 * {
 *   "data": {
 *     ...
 *   }
 * }
 *
 * tandis que d'autres peuvent renvoyer directement :
 *
 * {
 *   "id": "...",
 *   "email": "..."
 * }
 *
 * Ce type permet de prendre en charge les deux formes.
 */
type AuthenticationApiResponse<T> =
  | ApiSuccessResponse<T>
  | T;


/**
 * Vérifie qu'une valeur est un objet JavaScript exploitable.
 */
function isRecord(
  value: unknown,
): value is Record<string, unknown> {
  return (
    typeof value === "object" &&
    value !== null
  );
}


/**
 * Extrait la propriété `data` lorsqu'elle existe.
 *
 * Exemple enveloppé :
 *
 * {
 *   "data": {
 *     "id": "...",
 *     "email": "..."
 *   }
 * }
 *
 * Exemple direct :
 *
 * {
 *   "id": "...",
 *   "email": "..."
 * }
 */
function unwrapResponseData<T>(
  payload: AuthenticationApiResponse<T>,
): T {
  if (
    isRecord(payload) &&
    "data" in payload &&
    payload.data !== undefined &&
    payload.data !== null
  ) {
    return payload.data as T;
  }

  return payload as T;
}


/**
 * Convertit la représentation utilisateur retournée par Django
 * vers la structure stable utilisée par React.
 *
 * Le backend peut utiliser :
 *
 * - is_email_verified ;
 * - isEmailVerified.
 *
 * Le frontend expose toujours :
 *
 * - isEmailVerified.
 */
function mapAuthenticatedUser(
  data:
    | LoginResponseData
    | RegisterResponseData
    | AuthenticatedUser,
): AuthenticatedUser {
  const record =
    data as unknown as Record<string, unknown>;

  const id =
    typeof record.id === "string"
      ? record.id
      : "";

  const email =
    typeof record.email === "string"
      ? record.email
      : "";

  const isEmailVerified =
    typeof record.isEmailVerified === "boolean"
      ? record.isEmailVerified
      : typeof record.is_email_verified === "boolean"
        ? record.is_email_verified
        : false;

  if (!id || !email) {
    throw new Error(
      "La réponse d’authentification reçue du serveur est incomplète.",
    );
  }

  return {
    id,
    email,
    isEmailVerified,
  };
}


/**
 * Crée un nouveau compte.
 */
export async function registerUser(
  payload: RegisterPayload,
): Promise<AuthenticatedUser> {
  const csrfToken =
    await ensureCsrfToken();

  const response = await httpClient.post<
    AuthenticationApiResponse<RegisterResponseData>
  >(
    "/v1/auth/register/",
    payload,
    {
      headers: {
        "X-CSRFToken": csrfToken,
      },
    },
  );

  const responseData =
    unwrapResponseData(response.data);

  return mapAuthenticatedUser(responseData);
}


/**
 * Confirme une adresse e-mail à partir du jeton signé
 * transmis dans le corps JSON.
 */
export async function verifyEmailAddress(
  payload: VerifyEmailPayload,
): Promise<VerifyEmailResponseData> {
  const csrfToken =
    await ensureCsrfToken();

  const response = await httpClient.post<
    AuthenticationApiResponse<VerifyEmailResponseData>
  >(
    "/v1/auth/email-verification/confirm/",
    payload,
    {
      headers: {
        "X-CSRFToken": csrfToken,
      },
    },
  );

  return unwrapResponseData(response.data);
}


/**
 * Ouvre une session Django.
 */
export async function loginUser(
  payload: LoginPayload,
): Promise<AuthenticatedUser> {
  const csrfToken =
    await ensureCsrfToken();

  const response = await httpClient.post<
    AuthenticationApiResponse<LoginResponseData>
  >(
    "/v1/auth/login/",
    payload,
    {
      headers: {
        "X-CSRFToken": csrfToken,
      },
    },
  );

  /**
   * Django peut renouveler le contexte CSRF après la connexion.
   *
   * Nous supprimons donc le jeton gardé en mémoire.
   */
  clearInMemoryCsrfToken();

  const responseData =
    unwrapResponseData(response.data);

  return mapAuthenticatedUser(responseData);
}


/**
 * Ferme la session Django actuellement active.
 */
export async function logoutUser(): Promise<void> {
  const csrfToken =
    await ensureCsrfToken();

  await httpClient.post(
    "/v1/auth/logout/",
    {},
    {
      headers: {
        "X-CSRFToken": csrfToken,
      },
    },
  );

  clearInMemoryCsrfToken();
}


/**
 * Récupère l'utilisateur associé à la session courante.
 *
 * Cette fonction accepte deux formes de réponse :
 *
 * Réponse enveloppée :
 *
 * {
 *   "data": {
 *     "id": "...",
 *     "email": "...",
 *     "is_email_verified": true
 *   }
 * }
 *
 * Réponse directe :
 *
 * {
 *   "id": "...",
 *   "email": "...",
 *   "is_email_verified": true
 * }
 */
export async function getCurrentUser(): Promise<AuthenticatedUser> {
  const response = await httpClient.get<
    AuthenticationApiResponse<
      LoginResponseData | AuthenticatedUser
    >
  >(
    "/v1/auth/me/",
  );

  const responseData =
    unwrapResponseData(response.data);

  return mapAuthenticatedUser(responseData);
}

/**
 * Signale au backend que le compte authentifié est actif.
 */
export async function sendActivityHeartbeat(): Promise<void> {
  const csrfToken = await ensureCsrfToken();

  await httpClient.post(
    "/v1/auth/activity/",
    {},
    {
      headers: {
        "X-CSRFToken": csrfToken,
      },
    },
  );
}

export async function requestPasswordReset(
  payload: PasswordResetRequestPayload,
): Promise<void> {
  const csrfToken = await ensureCsrfToken();
  await httpClient.post(
    "/v1/auth/password-reset/request/",
    payload,
    { headers: { "X-CSRFToken": csrfToken } },
  );
}

export async function confirmPasswordReset(
  payload: PasswordResetConfirmPayload,
): Promise<void> {
  const csrfToken = await ensureCsrfToken();
  await httpClient.post(
    "/v1/auth/password-reset/confirm/",
    payload,
    { headers: { "X-CSRFToken": csrfToken } },
  );
  clearInMemoryCsrfToken();
}

export async function changePassword(
  payload: ChangePasswordPayload,
): Promise<void> {
  const csrfToken = await ensureCsrfToken();
  await httpClient.post(
    "/v1/auth/security/change-password/",
    payload,
    { headers: { "X-CSRFToken": csrfToken } },
  );
  clearInMemoryCsrfToken();
}

export async function revokeOtherSessions(
  payload: CurrentPasswordPayload,
): Promise<void> {
  const csrfToken = await ensureCsrfToken();
  await httpClient.post(
    "/v1/auth/security/revoke-sessions/",
    payload,
    { headers: { "X-CSRFToken": csrfToken } },
  );
}

export async function deactivateAccount(
  payload: DeactivateAccountPayload,
): Promise<void> {
  const csrfToken = await ensureCsrfToken();
  await httpClient.post(
    "/v1/auth/security/deactivate/",
    payload,
    { headers: { "X-CSRFToken": csrfToken } },
  );
  clearInMemoryCsrfToken();
}

export async function downloadPersonalData(): Promise<void> {
  const response = await httpClient.get<Blob>(
    "/v1/auth/privacy/export/",
    { responseType: "blob" },
  );
  const url = URL.createObjectURL(response.data);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = "mbolo-mes-donnees.json";
  document.body.appendChild(anchor);
  anchor.click();
  anchor.remove();
  URL.revokeObjectURL(url);
}

export async function permanentlyDeleteAccount(
  payload: DeleteAccountPayload,
): Promise<void> {
  const csrfToken = await ensureCsrfToken();
  await httpClient.post(
    "/v1/auth/privacy/delete/",
    payload,
    { headers: { "X-CSRFToken": csrfToken } },
  );
  clearInMemoryCsrfToken();
}
