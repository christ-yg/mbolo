/**
 * Types TypeScript liés aux interactions et aux matchs Mbolo.
 *
 * Ces structures correspondent au contrat actuellement exposé
 * par l'application Django "interactions".
 */

/**
 * Décisions autorisées par le backend.
 */
export type InteractionDecision = "like" | "pass";

/**
 * Données envoyées à Django pour enregistrer une interaction.
 *
 * L'acteur n'est jamais envoyé par React :
 * Django le détermine à partir de request.user.
 */
export interface CreateInteractionPayload {
  target_profile_id: string;
  decision: InteractionDecision;
}

/**
 * Réponse retournée après la création ou la mise à jour
 * d'une interaction.
 */
export interface InteractionResponse {
  interaction_id: string;
  decision: InteractionDecision;

  /**
   * true lorsque l'interaction vient d'être créée.
   * false lorsqu'une interaction existante a été actualisée.
   */
  interaction_created: boolean;

  /**
   * true lorsque les deux profils se sont mutuellement aimés.
   */
  matched: boolean;

  /**
   * true lorsqu'un nouveau match vient d'être créé.
   */
  match_created: boolean;

  /**
   * Identifiant du match lorsqu'un match existe.
   */
  match_id: string | null;
}

/**
 * Informations minimales utilisées par la fenêtre de nouveau match.
 *
 * Nous ne recopions volontairement aucune donnée privée.
 */
export interface MatchCelebrationData {
  matchId: string | null;
  profileId: string;
  displayName: string;
}



/**
 * Like reçu volontairement masqué pour le compte gratuit.
 */
export interface ReceivedLikeItem {
  interaction_id: string;
  city: string;
  age_range: string;
  dating_intent: string;
  has_photo: boolean;
  received_at: string;
  is_identity_revealed: boolean;
  profile_id: string | null;
  display_name: string | null;
  image_url: string | null;
}


export interface ReceivedLikesPaginatedResponse {
  count: number;
  next: string | null;
  previous: string | null;
  results: ReceivedLikeItem[];
}


export interface RespondToReceivedLikePayload {
  decision: InteractionDecision;
}


export interface ReceivedLikeActionResult {
  decision: InteractionDecision;
  matched: boolean;
  match_created: boolean;
  match_id: string | null;
  revealed_profile: {
    id: string;
    display_name: string;
    age: number | null;
    city: string;
    biography: string;
    dating_intent: string;
    photos: Array<{
      id: string;
      image_url: string | null;
      position: number;
      is_primary: boolean;
    }>;
  } | null;
}



export interface UnmatchResponse {
  match_id: string;
  conversation_id: string | null;
  deactivated: boolean;
  message: string;
}
