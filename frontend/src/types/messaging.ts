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
 * Aucun identifiant d'expéditeur sensible n'est exposé.
 */
export interface MessageItem {
  /**
   * Identifiant UUID public du message.
   */
  id: string;

  /**
   * Contenu textuel du message.
   */
  body: string;

  /**
   * Date de création du message.
   */
  created_at: string;

  /**
   * Date à laquelle le destinataire a lu le message.
   *
   * null signifie que le message n'a pas encore été lu.
   */
  read_at: string | null;

  /**
   * Indique si le message a été lu.
   */
  is_read: boolean;

  /**
   * Indique si le message appartient au compte connecté.
   */
  is_mine: boolean;
}

/**
 * Conversation privée associée à un match actif.
 */

/**
 * Présence publique minimale d'un autre participant.
 */
export interface UserPresence {
  is_online: boolean;
  last_seen_at: string | null;
}

export interface ConversationItem {
  /**
   * Identifiant UUID public de la conversation.
   */
  id: string;

  /**
   * Identifiant UUID du match associé.
   */
  match_id: string;

  /**
   * Profil public de l'autre participant.
   */
  other_profile: DiscoveryProfile;

  /**
   * Dernier message de la conversation.
   *
   * null signifie qu'aucun message n'a encore été envoyé.
   */
  last_message: MessageItem | null;

  /**
   * Nombre de messages reçus et non lus
   * dans cette conversation.
   */
  unread_count: number;

  /**
   * Présence calculée de l’autre participant.
   */
  other_presence: UserPresence;

  /**
   * Date de création de la conversation.
   */
  created_at: string;

  /**
   * Date de dernière activité de la conversation.
   */
  updated_at: string;
}

/**
 * Réponse paginée de la liste des conversations.
 */
export interface ConversationsPaginatedResponse {
  /**
   * Nombre total de conversations.
   */
  count: number;

  /**
   * URL de la page suivante.
   */
  next: string | null;

  /**
   * URL de la page précédente.
   */
  previous: string | null;

  /**
   * Conversations de la page actuelle.
   */
  results: ConversationItem[];
}

/**
 * Réponse paginée de l'historique des messages.
 */
export interface MessagesPaginatedResponse {
  /**
   * Nombre total de messages.
   */
  count: number;

  /**
   * URL de la page suivante.
   */
  next: string | null;

  /**
   * URL de la page précédente.
   */
  previous: string | null;

  /**
   * Messages de la page actuelle.
   */
  results: MessageItem[];
}

/**
 * Paramètres de pagination des conversations.
 */
export interface GetConversationsParameters {
  /**
   * Numéro de page demandé.
   */
  page?: number;

  /**
   * Nombre de conversations par page.
   */
  pageSize?: number;
}

/**
 * Paramètres de pagination des messages.
 */
export interface GetMessagesParameters {
  /**
   * Numéro de page demandé.
   */
  page?: number;

  /**
   * Nombre de messages par page.
   */
  pageSize?: number;
}

/**
 * Données envoyées pour créer ou récupérer
 * une conversation liée à un match.
 */
export interface OpenConversationPayload {
  /**
   * Identifiant UUID du match actif.
   */
  match_id: string;
}

/**
 * Données envoyées pour créer un message.
 */
export interface SendMessagePayload {
  /**
   * Contenu du message.
   */
  body: string;
}

/**
 * Réponse retournée après le marquage
 * d'une conversation comme lue.
 */
export interface MarkConversationReadResponse {
  /**
   * Identifiant UUID de la conversation.
   */
  conversation_id: string;

  /**
   * Nombre de messages marqués comme lus.
   */
  marked_count: number;

  /**
   * Date du marquage comme lu.
   */
  read_at: string;
}

/**
 * Nombre total de messages non lus du compte connecté.
 */
export interface UnreadMessageCountResponse {
  /**
   * Nombre total de messages reçus et non lus.
   */
  unread_count: number;
}
