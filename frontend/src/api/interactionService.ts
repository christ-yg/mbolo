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
  ReceivedLikeActionResult,
  ReceivedLikesPaginatedResponse,
  RespondToReceivedLikePayload,
  UnmatchResponse,
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



/**
 * Charge les likes reçus encore en attente de réponse.
 */
export async function getReceivedLikes(
  page = 1,
  pageSize = 12,
): Promise<ReceivedLikesPaginatedResponse> {
  const response =
    await httpClient.get<ReceivedLikesPaginatedResponse>(
      "/v1/likes-received/",
      {
        params: {
          page,
          page_size: pageSize,
        },
      },
    );

  return response.data;
}


/**
 * Répond à un like reçu à partir de l’identifiant opaque
 * de l’interaction.
 */
export async function respondToReceivedLike(
  interactionId: string,
  payload: RespondToReceivedLikePayload,
): Promise<ReceivedLikeActionResult> {
  const csrfToken = await ensureCsrfToken();

  const response =
    await httpClient.post<ReceivedLikeActionResult>(
      `/v1/likes-received/${encodeURIComponent(interactionId)}/respond/`,
      payload,
      {
        headers: {
          "X-CSRFToken": csrfToken,
        },
      },
    );

  return response.data;
}



/**
 * Désactive un match sans supprimer physiquement son historique.
 */
export async function deactivateMatch(
  matchId: string,
): Promise<UnmatchResponse> {
  const csrfToken = await ensureCsrfToken();

  const response =
    await httpClient.delete<UnmatchResponse>(
      `/v1/matches/${encodeURIComponent(matchId)}/`,
      {
        headers: {
          "X-CSRFToken": csrfToken,
        },
      },
    );

  return response.data;
}
