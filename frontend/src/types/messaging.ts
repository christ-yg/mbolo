/**
 * Types TypeScript de la messagerie privée Mbolo.
 *
 * Ces interfaces correspondent exactement aux données
 * retournées par l'API Django.
 */

import type { DiscoveryProfile } from "./discovery";


/**
 * Message public retourné par le backend.
 *
 * Aucun identifiant d'expéditeur n'est exposé.
 * Le booléen is_mine indique simplement si le message
 * appartient au compte actuellement connecté.
 */
export interface MessageItem {
  id: string;
  body: string;
  created_at: string;
  is_mine: boolean;
}


/**
 * Conversation privée associée à un match actif.
 */
export interface ConversationItem {
  id: string;
  match_id: string;
  other_profile: DiscoveryProfile;
  last_message: MessageItem | null;
  created_at: string;
  updated_at: string;
}


/**
 * Réponse paginée de la liste des conversations.
 */
export interface ConversationsPaginatedResponse {
  count: number;
  next: string | null;
  previous: string | null;
  results: ConversationItem[];
}


/**
 * Réponse paginée de l'historique des messages.
 */
export interface MessagesPaginatedResponse {
  count: number;
  next: string | null;
  previous: string | null;
  results: MessageItem[];
}


/**
 * Paramètres de pagination des conversations.
 */
export interface GetConversationsParameters {
  page?: number;
  pageSize?: number;
}


/**
 * Paramètres de pagination des messages.
 */
export interface GetMessagesParameters {
  page?: number;
  pageSize?: number;
}


/**
 * Données envoyées pour ouvrir une conversation.
 */
export interface OpenConversationPayload {
  match_id: string;
}


/**
 * Données envoyées pour créer un message.
 */
export interface SendMessagePayload {
  body: string;
}
