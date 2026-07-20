/**
 * Service HTTP de la page Mes matchs.
 *
 * Toutes les requêtes passent par le client Axios centralisé
 * afin de conserver :
 *
 * - l'adresse de base de l'API ;
 * - les cookies de session Django ;
 * - les délais réseau ;
 * - les paramètres communs.
 */

import { httpClient } from "./httpClient";

import type {
  GetMatchesParameters,
  MatchesPaginatedResponse,
} from "../types/matches";

/**
 * Nombre de matchs demandé par défaut.
 *
 * Le backend utilise également 20 par défaut.
 */
export const DEFAULT_MATCHES_PAGE_SIZE = 20;

/**
 * Charge une page de matchs actifs appartenant
 * exclusivement à l'utilisateur connecté.
 */
export async function getMatches(
  parameters: GetMatchesParameters = {},
): Promise<MatchesPaginatedResponse> {
  const page = parameters.page ?? 1;

  const pageSize =
    parameters.pageSize ?? DEFAULT_MATCHES_PAGE_SIZE;

  const response =
    await httpClient.get<MatchesPaginatedResponse>(
      "/v1/matches/",
      {
        params: {
          page,
          page_size: pageSize,
        },
      },
    );

  return response.data;
}
