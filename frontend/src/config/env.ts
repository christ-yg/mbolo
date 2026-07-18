/**
 * Configuration centralisée du frontend Mbolo.
 *
 * Nous évitons de lire import.meta.env dans plusieurs composants.
 * Toutes les variables sont validées une seule fois ici.
 */

/**
 * Retourne une variable d'environnement obligatoire.
 *
 * L'application s'arrête avec une erreur explicite lorsque la variable
 * est absente ou vide. Cela évite les erreurs silencieuses.
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
 * Supprime les barres obliques placées à la fin d'une URL.
 *
 * Exemple :
 *
 * http://127.0.0.1:8000/
 *
 * devient :
 *
 * http://127.0.0.1:8000
 */
function removeTrailingSlashes(value: string): string {
  return value.replace(/\/+$/, "");
}

/**
 * Configuration immuable du frontend.
 *
 * Object.freeze empêche les modifications accidentelles pendant
 * l'exécution de l'application.
 */
export const env = Object.freeze({
  apiBaseUrl: removeTrailingSlashes(
    getRequiredEnvironmentVariable("VITE_API_BASE_URL"),
  ),

  mode: import.meta.env.MODE,

  isDevelopment: import.meta.env.DEV,

  isProduction: import.meta.env.PROD,
});
