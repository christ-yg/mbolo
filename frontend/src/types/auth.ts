/**
 * Types TypeScript liés à l'authentification Mbolo.
 *
 * Ce fichier centralise les structures échangées entre :
 *
 * - les pages React ;
 * - les services API ;
 * - le backend Django.
 *
 * Le typage évite l'utilisation incontrôlée de `any` et permet
 * à TypeScript de détecter plusieurs erreurs avant l'exécution.
 */

/**
 * Représentation minimale d'un utilisateur authentifié.
 *
 * Nous n'exposons jamais ici :
 *
 * - le mot de passe ;
 * - le hash du mot de passe ;
 * - les permissions administratives internes ;
 * - les secrets du compte ;
 * - les données sensibles non nécessaires.
 */
export interface AuthenticatedUser {
  /**
   * Identifiant UUID du compte.
   */
  id: string;

  /**
   * Adresse e-mail normalisée.
   */
  email: string;

  /**
   * Indique si l'adresse e-mail a été confirmée.
   */
  isEmailVerified: boolean;
  emailTwoFactorEnabled: boolean;
}

/**
 * Données envoyées à l'endpoint d'inscription.
 */
export interface RegisterPayload {
  email: string;
  password: string;

  /**
   * Ce nom correspond exactement au champ attendu par Django.
   */
  password_confirmation: string;
  accept_terms: boolean;
  confirm_adult: boolean;
}

/**
 * Données envoyées à l'endpoint de connexion.
 */
export interface LoginPayload {
  email: string;
  password: string;
}

/**
 * Données envoyées à l'endpoint de confirmation d'e-mail.
 */
export interface VerifyEmailPayload {
  /**
   * Jeton signé reçu dans le lien de vérification.
   */
  token: string;
}

/**
 * Réponse de l'endpoint CSRF.
 */
export interface CsrfTokenResponse {
  csrfToken: string;
}

/**
 * Structure utilisateur retournée après l'inscription.
 */
export interface RegisterResponseData {
  id: string;
  email: string;
  isEmailVerified: boolean;
}

/**
 * Structure utilisateur retournée après la connexion.
 */
export interface LoginResponseData {
  id: string;
  email: string;
  isEmailVerified: boolean;
  emailTwoFactorEnabled?: boolean;
}

export interface EmailTwoFactorChallenge {
  requiresTwoFactor: true;
  challengeToken: string;
  maskedEmail: string;
}

export type LoginResult =
  | {
      requiresTwoFactor: false;
      user: AuthenticatedUser;
    }
  | EmailTwoFactorChallenge;

export interface EmailTwoFactorConfirmPayload {
  challenge_token: string;
  code: string;
}

export interface EmailTwoFactorSettingsPayload {
  current_password: string;
  enabled: boolean;
}

export interface LoginActivity {
  id: string;
  method: "password" | "email_2fa";
  device: string;
  ipFingerprint: string;
  createdAt: string;
}

/**
 * Structure retournée après la confirmation de l'e-mail.
 */
export interface VerifyEmailResponseData {
  email: string;
  isEmailVerified: boolean;
}

export interface PasswordResetRequestPayload {
  email: string;
}

export interface PasswordResetConfirmPayload {
  uid: string;
  token: string;
  password: string;
  password_confirmation: string;
}

export interface ChangePasswordPayload {
  current_password: string;
  new_password: string;
  new_password_confirmation: string;
}

export interface CurrentPasswordPayload {
  current_password: string;
}

export interface DeactivateAccountPayload
  extends CurrentPasswordPayload {
  confirmation: string;
}

export interface DeleteAccountPayload {
  current_password: string;
  confirmation: string;
}
