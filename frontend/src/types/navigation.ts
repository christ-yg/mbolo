/**
 * Types liés à la navigation publique de Mbolo.
 */

/**
 * Représente un lien visible dans la barre de navigation.
 */
export interface NavigationItem {
  /**
   * Texte affiché à l'utilisateur.
   */
  label: string;

  /**
   * Destination React Router.
   */
  href: string;
}
