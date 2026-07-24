/**
 * Types TypeScript du moteur de découverte Mbolo.
 *
 * Ce fichier représente exactement les données actuellement
 * exposées par DiscoveryProfileSerializer dans Django.
 *
 * Principe de sécurité :
 *
 * le frontend ne doit pas inventer, supposer ou réclamer
 * des champs que le backend n'expose pas.
 *
 * Données volontairement absentes :
 *
 * - adresse e-mail ;
 * - numéro de téléphone ;
 * - date de naissance exacte ;
 * - identifiant du compte utilisateur ;
 * - préférences privées ;
 * - informations administratives.
 */

import type { ProfilePhoto } from "./profilePhotos";

/**
 * Profil public visible dans le moteur de découverte.
 *
 * Les noms utilisent le format snake_case parce qu'ils
 * correspondent directement au JSON envoyé par Django.
 */
export interface DiscoveryProfile {
  /**
   * Identifiant UUID public du profil.
   *
   * Il ne s'agit pas de l'identifiant du compte User.
   */
  id: string;

  /**
   * Nom public choisi par la personne.
   */
  display_name: string;

  /**
   * Âge calculé côté backend.
   *
   * La date de naissance exacte n'est jamais transmise.
   */
  age: number;

  /**
   * Genre public du profil.
   *
   * Sa valeur exacte dépend des choix définis dans Django.
   */
  gender: string;

  /**
   * Ville affichée dans le moteur de découverte.
   */
  city: string;

  /**
   * Description publique du profil.
   */
  biography: string;

  /**
   * Intention relationnelle publique.
   */
  dating_intent: string;

  /**
   * Indique que la vérification humaine du profil a été approuvée.
   */
  is_verified: boolean;

  /**
   * Photos publiques déjà nettoyées et réencodées par Django.
   *
   * Le tableau peut être vide. L'interface affiche alors les initiales.
   */
  photos: ProfilePhoto[];

  interests: string[];
  interest_labels: string[];
  common_interests: string[];
  common_interest_labels: string[];
  compatibility_score: number;
}

/**
 * Format standard de pagination Django REST Framework.
 *
 * DiscoveryPagination hérite de PageNumberPagination.
 */
export interface DiscoveryPaginatedResponse {
  /**
   * Nombre total de profils disponibles.
   */
  count: number;

  /**
   * URL de la page suivante.
   *
   * null signifie qu'il n'existe aucune page suivante.
   */
  next: string | null;

  /**
   * URL de la page précédente.
   *
   * null signifie que nous sommes sur la première page.
   */
  previous: string | null;

  /**
   * Profils contenus dans la page courante.
   */
  results: DiscoveryProfile[];
}

/**
 * Paramètres autorisés par l'API de découverte.
 */
export interface DiscoveryQueryParameters {
  /**
   * Numéro de la page demandée.
   */
  page?: number;

  /**
   * Nombre de profils demandés.
   *
   * Le backend limite cette valeur à 50.
   */
  pageSize?: number;
}
