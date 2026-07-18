/**
 * Configuration centralisée du frontend Mbolo.
 *
 * L'application ne doit pas lire directement import.meta.env
 * dans plusieurs composants.
 *
 * Tous les paramètres publics sont :
 *
 * - récupérés ;
 * - validés ;
 * - normalisés ;
 * - exposés depuis ce fichier unique.
 */

/**
 * Retourne une variable d'environnement obligatoire.
 *
 * Une erreur explicite est déclenchée au démarrage lorsqu'une
 * variable est absente ou vide.
 */
function getRequiredEnvironmentVariable(
  variableName: keyof ImportMetaEnv,
): string {
  const value = import.meta.env[variableName];

  if (typeof value !== "string" || value.trim() === "") {
    throw new Error(
      `La variable d'environnement ${String(variableName)} est obligatoire.`,
    );
  }

  return value.trim();
}

/**
 * Supprime les barres obliques finales d'une URL ou d'un chemin.
 *
 * Exemples :
 *
 *     /api/                         devient /api
 *     http://127.0.0.1:8000/        devient http://127.0.0.1:8000
 *
 * Cela empêche la création involontaire d'URLs contenant "//".
 */
function removeTrailingSlashes(value: string): string {
  return value.replace(/\/+$/, "");
}

/**
 * Vérifie que le préfixe public de l'API est un chemin local.
 *
 * En développement et dans l'architecture de production envisagée,
 * le frontend doit appeler l'API par le même domaine.
 *
 * Exemple accepté :
 *
 *     /api
 *
 * Cette règle réduit les risques d'envoyer accidentellement
 * les cookies ou les jetons CSRF vers un domaine externe.
 */
function validateApiBaseUrl(value: string): string {
  const normalizedValue = removeTrailingSlashes(value);

  if (!normalizedValue.startsWith("/")) {
    throw new Error(
      "VITE_API_BASE_URL doit être un chemin local commençant par '/'.",
    );
  }

  if (normalizedValue.startsWith("//")) {
    throw new Error(
      "VITE_API_BASE_URL ne doit pas être une URL réseau commençant par '//'.",
    );
  }

  return normalizedValue;
}

/**
 * Configuration immuable du frontend.
 *
 * Object.freeze empêche une modification accidentelle pendant
 * l'exécution de l'application.
 */
export const env = Object.freeze({
  /**
   * Préfixe utilisé par Axios.
   *
   * Valeur actuelle :
   *
   *     /api
   */
  apiBaseUrl: validateApiBaseUrl(
    getRequiredEnvironmentVariable("VITE_API_BASE_URL"),
  ),

  /**
   * Environnement Vite courant :
   *
   * - development ;
   * - production ;
   * - test éventuel.
   */
  mode: import.meta.env.MODE,

  /**
   * Vrai uniquement pendant le développement.
   */
  isDevelopment: import.meta.env.DEV,

  /**
   * Vrai uniquement après compilation de production.
   */
  isProduction: import.meta.env.PROD,
});
