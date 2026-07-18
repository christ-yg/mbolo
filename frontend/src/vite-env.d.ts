/// <reference types="vite/client" />

/**
 * Variables d'environnement publiques utilisées par Mbolo.
 *
 * TypeScript vérifiera maintenant que VITE_API_BASE_URL existe
 * dans les variables autorisées.
 */
interface ImportMetaEnv {
  readonly VITE_API_BASE_URL: string;
}

/**
 * Extension du type global ImportMeta fourni par Vite.
 */
interface ImportMeta {
  readonly env: ImportMetaEnv;
}
