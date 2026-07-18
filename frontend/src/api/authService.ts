/**
 * Service d'authentification du frontend Mbolo.
 *
 * Ce fichier constitue l'interface unique entre les composants React
 * et les endpoints Django d'authentification.
 */

import type { ApiSuccessResponse } from "../types/api";
import type {
  AuthenticatedUser,
  LoginPayload,
  LoginResponseData,
  RegisterPayload,
  RegisterResponseData,
} from "../types/auth";

import {
  clearInMemoryCsrfToken,
  ensureCsrfToken,
} from "./csrfService";
import { httpClient } from "./httpClient";

/**
 * Transforme la représentation brute retournée par Django
 * en objet frontend stable.
 *
 * Le backend actuel retourne des noms camelCase dans ses réponses.
 * Cette fonction centralise néanmoins la transformation afin de
 * faciliter une évolution future.
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
 * Crée un nouveau compte utilisateur.
 *
 * Étapes :
 *
 * 1. récupération d'un jeton CSRF ;
 * 2. envoi du formulaire d'inscription ;
 * 3. transformation de la réponse.
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
 * Ouvre une session Django.
 *
 * Le serveur doit :
 *
 * - vérifier les identifiants ;
 * - vérifier l'état du compte ;
 * - créer la session ;
 * - faire tourner l'identifiant de session ;
 * - retourner les données minimales de l'utilisateur.
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
   * La session a changé après la connexion.
   *
   * Nous renouvelons donc notre copie CSRF en mémoire avant
   * la prochaine opération sensible.
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
 * Une réponse 401 ou 403 signifie normalement qu'aucune session
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
