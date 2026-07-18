/**
 * Types génériques des réponses API Mbolo.
 *
 * Ces types évitent d'utiliser "any" dans la couche réseau.
 */

/**
 * Réponse API standard contenant une donnée métier.
 *
 * Exemple :
 *
 * {
 *   "data": {
 *     "id": "...",
 *     "email": "..."
 *   },
 *   "message": "Opération réussie."
 * }
 */
export interface ApiSuccessResponse<TData> {
  /**
   * Donnée métier retournée par Django.
   */
  data: TData;

  /**
   * Message humain facultatif.
   */
  message?: string;
}

/**
 * Structure normalisée d'une erreur API affichable.
 */
export interface NormalizedApiError {
  /**
   * Code HTTP reçu.
   *
   * La valeur vaut null lorsque la requête n'a pas obtenu
   * de réponse du serveur.
   */
  status: number | null;

  /**
   * Message général destiné à l'utilisateur.
   */
  message: string;

  /**
   * Erreurs de validation associées aux champs.
   *
   * Exemple :
   *
   * {
   *   "email": ["Cette adresse est déjà utilisée."],
   *   "password": ["Le mot de passe est trop faible."]
   * }
   */
  fieldErrors: Record<string, string[]>;

  /**
   * Indique qu'aucune réponse serveur n'a été reçue.
   */
  isNetworkError: boolean;
}

/**
 * Forme possible des erreurs retournées par Django REST Framework.
 *
 * Cette interface reste volontairement flexible, car plusieurs
 * serializers peuvent retourner des noms de champs différents.
 */
export interface ApiErrorPayload {
  message?: string;
  detail?: string;
  error?: string;
  errors?: Record<string, unknown>;
  [key: string]: unknown;
}
