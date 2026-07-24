/**
 * Types des préférences de sécurité liées aux nouvelles connexions.
 */

export interface LoginAlertEmailPreference {
  loginAlertEmailsEnabled: boolean;
  internalSecurityNotificationsEnabled: true;
}

export interface UpdateLoginAlertEmailPreferencePayload {
  current_password: string;
  enabled: boolean;
}
