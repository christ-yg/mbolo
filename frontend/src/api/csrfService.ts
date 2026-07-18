/**
 * Service de récupération du jeton CSRF Django.
 *
 * L'appel à l'endpoint :
 *
 *     GET /api/v1/csrf/
 *
 * demande à Django de :
 *
 * - générer ou renouveler le jeton ;
 * - déposer le cookie csrftoken ;
 * - retourner également la valeur dans le JSON.
 */

import type { CsrfTokenResponse } from "../types/auth";

import { httpClient } from "./httpClient";

/**
 * Jeton conservé uniquement en mémoire.
 *
 * Il n'est pas enregistré dans :
 *
 * - localStorage ;
 * - sessionStorage ;
 * - IndexedDB.
 *
 * Le cookie Django reste la source officielle du navigateur.
 */
let inMemoryCsrfToken: string | null = null;

/**
 * Promesse partagée lorsqu'une récupération est déjà en cours.
 *
 * Cette technique évite que plusieurs composants déclenchent
 * simultanément plusieurs requêtes CSRF identiques.
 */
let csrfRequestPromise: Promise<string> | null = null;

/**
 * Récupère un nouveau jeton CSRF auprès de Django.
 */
async function requestCsrfToken(): Promise<string> {
  const response =
    await httpClient.get<CsrfTokenResponse>(
      "/v1/csrf/",
    );

  const token = response.data.csrfToken?.trim();

  if (!token) {
    throw new Error(
      "Le backend n'a retourné aucun jeton CSRF valide.",
    );
  }

  inMemoryCsrfToken = token;

  return token;
}

/**
 * Retourne un jeton CSRF utilisable.
 *
 * Paramètres
 * ----------
 * forceRefresh:
 *     Lorsque true, un nouveau jeton est demandé même si une valeur
 *     existe déjà en mémoire.
 */
export async function ensureCsrfToken(
  forceRefresh = false,
): Promise<string> {
  if (!forceRefresh && inMemoryCsrfToken) {
    return inMemoryCsrfToken;
  }

  if (!forceRefresh && csrfRequestPromise) {
    return csrfRequestPromise;
  }

  csrfRequestPromise = requestCsrfToken();

  try {
    return await csrfRequestPromise;
  } finally {
    csrfRequestPromise = null;
  }
}

/**
 * Supprime uniquement la copie conservée en mémoire.
 *
 * Cela sera utilisé après la déconnexion ou lorsqu'un jeton
 * doit être renouvelé.
 */
export function clearInMemoryCsrfToken(): void {
  inMemoryCsrfToken = null;
}
