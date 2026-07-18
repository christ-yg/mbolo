/// <reference types="vite/client" />

/**
 * Variables d'environnement publiques utilisées par Mbolo.
 *
 * TypeScript vérifiera que les variables référencées dans le code
 * correspondent bien à celles déclarées ici.
 */
interface ImportMetaEnv {
  /**
   * Préfixe public utilisé pour les requêtes API.
   *
   * Exemple en développement :
   *
   *     /api
   */
  readonly VITE_API_BASE_URL: string;

  /**
   * Adresse du backend Django utilisé par le proxy Vite.
   *
   * Exemple :
   *
   *     http://127.0.0.1:8000
   */
  readonly VITE_API_PROXY_TARGET: string;
}

/**
 * Extension du type global ImportMeta fourni par Vite.
 */
interface ImportMeta {
  readonly env: ImportMetaEnv;
}
