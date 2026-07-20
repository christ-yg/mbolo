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
