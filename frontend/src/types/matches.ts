/**
 * Types TypeScript correspondant à l'API Django des matchs.
 *
 * Endpoint :
 *
 *     GET /api/v1/matches/
 *
 * Le backend n'expose volontairement que le profil public
 * de l'autre participant.
 */

import type { DiscoveryProfile } from "./discovery";

/**
 * Match actif retourné par Django.
 */
export interface MatchItem {
  /**
   * UUID public du match.
   */
  id: string;

  /**
   * Profil public de l'autre participant.
   *
   * Aucun e-mail, téléphone ou identifiant User n'est exposé.
   */
  other_profile: DiscoveryProfile;

  /**
   * Date ISO de création du match.
   */
  created_at: string;
}

/**
 * Réponse paginée standard de Django REST Framework.
 */
export interface MatchesPaginatedResponse {
  count: number;
  next: string | null;
  previous: string | null;
  results: MatchItem[];
}

/**
 * Paramètres autorisés par l'API.
 */
export interface GetMatchesParameters {
  page?: number;
  pageSize?: number;
}
