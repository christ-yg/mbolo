/**
 * Service API des interactions Mbolo.
 *
 * Endpoint utilisé :
 *
 *     POST /api/v1/interactions/
 *
 * Toutes les requêtes sensibles passent par :
 *
 * - le client Axios centralisé ;
 * - le cookie de session Django ;
 * - la protection CSRF ;
 * - des types TypeScript stricts.
 */

import type {
  CreateInteractionPayload,
  InteractionResponse,
} from "../types/interactions";

import { ensureCsrfToken } from "./csrfService";
import { httpClient } from "./httpClient";

/**
 * Enregistre un like ou un pass.
 */
export async function createInteraction(
  payload: CreateInteractionPayload,
): Promise<InteractionResponse> {
  const csrfToken = await ensureCsrfToken();

  const response = await httpClient.post<InteractionResponse>(
    "/v1/interactions/",
    payload,
    {
      headers: {
        "X-CSRFToken": csrfToken,
      },
    },
  );

  return response.data;
}
