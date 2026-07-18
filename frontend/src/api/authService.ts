/**
 * Service d'authentification du frontend Mbolo.
 *
 * Toutes les pages React doivent utiliser ce service au lieu
 * d'appeler directement Axios.
 *
 * Cette séparation apporte plusieurs avantages :
 *
 * - centralisation des URLs ;
 * - centralisation de la protection CSRF ;
 * - typage des requêtes et réponses ;
 * - code React plus lisible ;
 * - maintenance plus facile ;
 * - réduction des erreurs de sécurité.
 */

import type { ApiSuccessResponse } from "../types/api";
import type {
  AuthenticatedUser,
  LoginPayload,
  LoginResponseData,
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
 * Convertit une représentation utilisateur retournée par Django
 * en structure stable utilisée par React.
 */
function mapAuthenticatedUser(
  data: LoginResponseData | RegisterResponseData,
): AuthenticatedUser {
  return {
    id: data.id,
    email: data.email,
    isEmailVerified: data.isEmailVerified,
  };
}

/**
 * Crée un nouveau compte.
 *
 * Étapes :
 *
 * 1. récupération du jeton CSRF ;
 * 2. envoi des informations à Django ;
 * 3. transformation de la réponse ;
 * 4. retour des données minimales du compte.
 */
export async function registerUser(
  payload: RegisterPayload,
): Promise<AuthenticatedUser> {
  const csrfToken = await ensureCsrfToken();

  const response = await httpClient.post<
    ApiSuccessResponse<RegisterResponseData>
  >(
    "/v1/auth/register/",
    payload,
    {
      headers: {
        "X-CSRFToken": csrfToken,
      },
    },
  );

  return mapAuthenticatedUser(response.data.data);
}

/**
 * Confirme l'adresse e-mail à partir d'un jeton signé.
 *
 * Le jeton est envoyé dans le corps JSON et non conservé
 * dans localStorage ou sessionStorage.
 */
export async function verifyEmailAddress(
  payload: VerifyEmailPayload,
): Promise<VerifyEmailResponseData> {
  const csrfToken = await ensureCsrfToken();

  const response = await httpClient.post<
    ApiSuccessResponse<VerifyEmailResponseData>
  >(
    "/v1/auth/email-verification/confirm/",
    payload,
    {
      headers: {
        "X-CSRFToken": csrfToken,
      },
    },
  );

  return response.data.data;
}

/**
 * Ouvre une session Django.
 *
 * Le backend :
 *
 * - vérifie les identifiants ;
 * - vérifie l'état du compte ;
 * - crée une session ;
 * - renouvelle l'identifiant de session ;
 * - retourne les informations minimales du compte.
 */
export async function loginUser(
  payload: LoginPayload,
): Promise<AuthenticatedUser> {
  const csrfToken = await ensureCsrfToken();

  const response = await httpClient.post<
    ApiSuccessResponse<LoginResponseData>
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
   * Django peut renouveler le contexte de session après la connexion.
   *
   * Nous supprimons donc la copie CSRF conservée en mémoire.
   * Un nouveau jeton sera demandé avant la prochaine opération sensible.
   */
  clearInMemoryCsrfToken();

  return mapAuthenticatedUser(response.data.data);
}

/**
 * Ferme la session Django courante.
 */
export async function logoutUser(): Promise<void> {
  const csrfToken = await ensureCsrfToken();

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
 * Une réponse 401 ou 403 signifie généralement qu'aucune session
 * authentifiée n'est disponible.
 */
export async function getCurrentUser(): Promise<AuthenticatedUser> {
  const response = await httpClient.get<
    ApiSuccessResponse<AuthenticatedUser>
  >(
    "/v1/auth/me/",
  );

  return response.data.data;
}
