/**
 * Service API du moteur de découverte Mbolo.
 *
 * Ce fichier centralise la communication avec :
 *
 *     GET /api/v1/profiles/discovery/
 *
 * Les composants React ne doivent pas appeler Axios directement.
 * Ils utilisent ce service afin de conserver :
 *
 * - une URL centralisée ;
 * - un typage strict ;
 * - une gestion cohérente des paramètres ;
 * - une architecture facilement testable.
 */

import type {
  DiscoveryPaginatedResponse,
  DiscoveryQueryParameters,
} from "../types/discovery";

import { httpClient } from "./httpClient";

/**
 * Taille utilisée par défaut dans l'interface.
 *
 * Le backend accepte 20 profils par défaut et impose
 * un maximum de 50.
 *
 * Nous demandons ici 10 profils afin de limiter :
 *
 * - le volume de données transférées ;
 * - le temps de chargement ;
 * - la quantité de profils présents en mémoire ;
 * - l'exposition massive de données.
 */
export const DEFAULT_DISCOVERY_PAGE_SIZE = 10;

/**
 * Récupère une page de profils compatibles.
 */
export async function getDiscoveryProfiles(
  parameters: DiscoveryQueryParameters = {},
): Promise<DiscoveryPaginatedResponse> {
  /**
   * Validation défensive côté frontend.
   *
   * Le backend reste l'autorité finale, mais nous évitons
   * d'envoyer volontairement des valeurs incohérentes.
   */
  const requestedPage =
    typeof parameters.page === "number" &&
    Number.isInteger(parameters.page) &&
    parameters.page > 0
      ? parameters.page
      : 1;

  const requestedPageSize =
    typeof parameters.pageSize === "number" &&
    Number.isInteger(parameters.pageSize) &&
    parameters.pageSize > 0
      ? Math.min(parameters.pageSize, 50)
      : DEFAULT_DISCOVERY_PAGE_SIZE;

  const response =
    await httpClient.get<DiscoveryPaginatedResponse>(
      "/v1/profiles/discovery/",
      {
        params: {
          page: requestedPage,
          page_size: requestedPageSize,
        },
      },
    );

  return response.data;
}
