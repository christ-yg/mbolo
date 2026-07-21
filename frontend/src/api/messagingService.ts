/**
 * Service HTTP centralisé de la messagerie privée Mbolo.
 *
 * Ce fichier regroupe toutes les opérations frontend liées :
 *
 * - aux conversations ;
 * - aux messages ;
 * - au marquage des messages comme lus ;
 * - au compteur global des messages non lus.
 *
 * Les cookies de session Django sont automatiquement envoyés
 * par le client HTTP principal.
 */

import { httpClient } from "./httpClient";

import type {
  ConversationItem,
  ConversationsPaginatedResponse,
  GetConversationsParameters,
  GetMessagesParameters,
  MarkConversationReadResponse,
  MessageItem,
  MessagesPaginatedResponse,
  OpenConversationPayload,
  SendMessagePayload,
  UnreadMessageCountResponse,
} from "../types/messaging";

/**
 * Nombre de conversations demandées par défaut.
 */
export const DEFAULT_CONVERSATIONS_PAGE_SIZE = 20;

/**
 * Nombre de messages demandés par défaut.
 */
export const DEFAULT_MESSAGES_PAGE_SIZE = 50;

/**
 * Taille maximale autorisée par le backend
 * pour une page de conversations ou de messages.
 */
export const MAX_MESSAGING_PAGE_SIZE = 50;

/**
 * Normalise une taille de page avant de l'envoyer au backend.
 *
 * Cette fonction évite :
 *
 * - les valeurs négatives ;
 * - la valeur zéro ;
 * - les nombres décimaux ;
 * - les valeurs supérieures à la limite du backend.
 */
function normalizePageSize(
  value: number | undefined,
  defaultValue: number,
): number {
  if (
    value === undefined ||
    !Number.isFinite(value)
  ) {
    return defaultValue;
  }

  const normalizedValue = Math.floor(value);

  if (normalizedValue < 1) {
    return defaultValue;
  }

  return Math.min(
    normalizedValue,
    MAX_MESSAGING_PAGE_SIZE,
  );
}

/**
 * Normalise un numéro de page.
 */
function normalizePage(
  value: number | undefined,
): number {
  if (
    value === undefined ||
    !Number.isFinite(value)
  ) {
    return 1;
  }

  return Math.max(
    1,
    Math.floor(value),
  );
}

/**
 * Charge les conversations actives du compte connecté.
 *
 * Endpoint Django :
 *
 * GET /api/v1/conversations/
 */
export async function getConversations(
  parameters: GetConversationsParameters = {},
): Promise<ConversationsPaginatedResponse> {
  const response =
    await httpClient.get<ConversationsPaginatedResponse>(
      "/v1/conversations/",
      {
        params: {
          page: normalizePage(
            parameters.page,
          ),
          page_size: normalizePageSize(
            parameters.pageSize,
            DEFAULT_CONVERSATIONS_PAGE_SIZE,
          ),
        },
      },
    );

  return response.data;
}

/**
 * Crée ou récupère la conversation associée à un match actif.
 *
 * Endpoint Django :
 *
 * POST /api/v1/conversations/
 *
 * Corps JSON :
 *
 * {
 *   "match_id": "uuid-du-match"
 * }
 */
export async function openConversation(
  payload: OpenConversationPayload,
): Promise<ConversationItem> {
  const response =
    await httpClient.post<ConversationItem>(
      "/v1/conversations/",
      payload,
    );

  return response.data;
}

/**
 * Charge l'historique paginé des messages
 * d'une conversation autorisée.
 *
 * Endpoint Django :
 *
 * GET /api/v1/conversations/<uuid>/messages/
 */
export async function getConversationMessages(
  conversationId: string,
  parameters: GetMessagesParameters = {},
): Promise<MessagesPaginatedResponse> {
  const encodedConversationId =
    encodeURIComponent(conversationId);

  const response =
    await httpClient.get<MessagesPaginatedResponse>(
      `/v1/conversations/${encodedConversationId}/messages/`,
      {
        params: {
          page: normalizePage(
            parameters.page,
          ),
          page_size: normalizePageSize(
            parameters.pageSize,
            DEFAULT_MESSAGES_PAGE_SIZE,
          ),
        },
      },
    );

  return response.data;
}

/**
 * Envoie un message dans une conversation active.
 *
 * Endpoint Django :
 *
 * POST /api/v1/conversations/<uuid>/messages/
 *
 * Corps JSON :
 *
 * {
 *   "body": "Contenu du message"
 * }
 */
export async function sendConversationMessage(
  conversationId: string,
  payload: SendMessagePayload,
): Promise<MessageItem> {
  const encodedConversationId =
    encodeURIComponent(conversationId);

  const response =
    await httpClient.post<MessageItem>(
      `/v1/conversations/${encodedConversationId}/messages/`,
      payload,
    );

  return response.data;
}

/**
 * Marque comme lus tous les messages reçus et non lus
 * dans une conversation.
 *
 * Les messages envoyés par le compte connecté
 * ne sont pas modifiés.
 *
 * Endpoint Django :
 *
 * POST /api/v1/conversations/<uuid>/read/
 */
export async function markConversationAsRead(
  conversationId: string,
): Promise<MarkConversationReadResponse> {
  const encodedConversationId =
    encodeURIComponent(conversationId);

  const response =
    await httpClient.post<MarkConversationReadResponse>(
      `/v1/conversations/${encodedConversationId}/read/`,
      {},
    );

  return response.data;
}

/**
 * Retourne le nombre total de messages reçus
 * et non lus pour le compte connecté.
 *
 * Endpoint Django :
 *
 * GET /api/v1/messages/unread-count/
 */
export async function getUnreadMessageCount():
Promise<UnreadMessageCountResponse> {
  const response =
    await httpClient.get<UnreadMessageCountResponse>(
      "/v1/messages/unread-count/",
    );

  return response.data;
}
