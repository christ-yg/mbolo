/**
 * Service HTTP centralisé de la messagerie Mbolo.
 *
 * Toutes les requêtes utilisent le client Axios principal.
 * Les cookies de session Django sont donc automatiquement joints.
 */

import { httpClient } from "./httpClient";

import type {
  ConversationItem,
  ConversationsPaginatedResponse,
  GetConversationsParameters,
  GetMessagesParameters,
  MessageItem,
  MessagesPaginatedResponse,
  OpenConversationPayload,
  SendMessagePayload,
} from "../types/messaging";


export const DEFAULT_CONVERSATIONS_PAGE_SIZE = 20;
export const DEFAULT_MESSAGES_PAGE_SIZE = 50;


/**
 * Charge les conversations actives du compte connecté.
 */
export async function getConversations(
  parameters: GetConversationsParameters = {},
): Promise<ConversationsPaginatedResponse> {
  const response =
    await httpClient.get<ConversationsPaginatedResponse>(
      "/v1/conversations/",
      {
        params: {
          page: parameters.page ?? 1,
          page_size:
            parameters.pageSize ??
            DEFAULT_CONVERSATIONS_PAGE_SIZE,
        },
      },
    );

  return response.data;
}


/**
 * Crée ou récupère la conversation associée à un match actif.
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
 * Charge les messages d'une conversation.
 */
export async function getConversationMessages(
  conversationId: string,
  parameters: GetMessagesParameters = {},
): Promise<MessagesPaginatedResponse> {
  const response =
    await httpClient.get<MessagesPaginatedResponse>(
      `/v1/conversations/${conversationId}/messages/`,
      {
        params: {
          page: parameters.page ?? 1,
          page_size:
            parameters.pageSize ??
            DEFAULT_MESSAGES_PAGE_SIZE,
        },
      },
    );

  return response.data;
}


/**
 * Envoie un message dans une conversation active.
 *
 * Le frontend transmet uniquement le texte.
 * L'expéditeur est déterminé par request.user dans Django.
 */
export async function sendConversationMessage(
  conversationId: string,
  payload: SendMessagePayload,
): Promise<MessageItem> {
  const response =
    await httpClient.post<MessageItem>(
      `/v1/conversations/${conversationId}/messages/`,
      payload,
    );

  return response.data;
}
