/**
 * Événement minimal affiché dans le journal de sécurité du compte.
 */
export interface AccountSecurityEvent {
  id: string;
  event: string;
  outcome: string;
  reason: string;
  createdAt: string;
}
