/**
 * Types liés à l'authentification Mbolo.
 */

/**
 * Utilisateur minimal retourné par l'API.
 *
 * Les champs sensibles comme :
 *
 * - password ;
 * - password_hash ;
 * - permissions internes ;
 * - données administratives ;
 *
 * ne doivent jamais être exposés.
 */
export interface AuthenticatedUser {
  id: string;
  email: string;
  isEmailVerified: boolean;
}

/**
 * Données nécessaires à l'inscription.
 */
export interface RegisterPayload {
  email: string;
  password: string;
  password_confirmation: string;
}

/**
 * Données nécessaires à la connexion.
 */
export interface LoginPayload {
  email: string;
  password: string;
}

/**
 * Réponse de l'endpoint CSRF.
 */
export interface CsrfTokenResponse {
  csrfToken: string;
}

/**
 * Réponse métier d'inscription.
 */
export interface RegisterResponseData {
  id: string;
  email: string;
  isEmailVerified: boolean;
}

/**
 * Réponse métier de connexion.
 *
 * Elle pourra être ajustée si le backend retourne une structure
 * légèrement différente.
 */
export interface LoginResponseData {
  id: string;
  email: string;
  isEmailVerified: boolean;
}
