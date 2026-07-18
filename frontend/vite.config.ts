/**
 * Configuration Vite du frontend Mbolo.
 *
 * Cette configuration assure notamment :
 *
 * - la compilation React ;
 * - le proxy local vers Django ;
 * - le refus d'un proxy mal configuré ;
 * - l'utilisation de 127.0.0.1 en développement.
 */

import { defineConfig, loadEnv } from "vite";
import react from "@vitejs/plugin-react";

/**
 * Exporte une configuration dépendant du mode Vite courant.
 *
 * Les variables sont chargées depuis :
 *
 * - .env ;
 * - .env.local ;
 * - les fichiers spécifiques au mode éventuel.
 */
export default defineConfig(({ mode }) => {
  const environment = loadEnv(
    mode,
    process.cwd(),
    "",
  );

  const proxyTarget =
    environment.VITE_API_PROXY_TARGET?.trim();

  /**
   * Le proxy ne doit jamais démarrer avec une cible vide.
   *
   * Une erreur immédiate est plus sûre qu'un serveur qui fonctionne
   * partiellement ou transmet les requêtes vers une mauvaise adresse.
   */
  if (!proxyTarget) {
    throw new Error(
      "VITE_API_PROXY_TARGET est obligatoire pour démarrer Vite.",
    );
  }

  /**
   * En développement local, nous exigeons une URL HTTP ou HTTPS.
   */
  if (
    !proxyTarget.startsWith("http://") &&
    !proxyTarget.startsWith("https://")
  ) {
    throw new Error(
      "VITE_API_PROXY_TARGET doit commencer par http:// ou https://.",
    );
  }

  return {
    plugins: [react()],

    server: {
      /**
       * Limite le serveur de développement à la machine locale.
       *
       * Nous ne l'exposons pas automatiquement sur tout le réseau.
       */
      host: "127.0.0.1",

      /**
       * Port standard choisi pour le frontend Mbolo.
       */
      port: 5173,

      /**
       * Empêche Vite de choisir silencieusement un autre port
       * si 5173 est déjà occupé.
       */
      strictPort: true,

      proxy: {
        /**
         * Toutes les requêtes commençant par /api sont transmises
         * au backend Django.
         *
         * Exemple navigateur :
         *
         *     http://127.0.0.1:5173/api/v1/csrf/
         *
         * Requête réelle Django :
         *
         *     http://127.0.0.1:8000/api/v1/csrf/
         */
        "/api": {
          target: proxyTarget,

          /**
           * Adapte l'en-tête Host à la cible Django.
           */
          changeOrigin: true,

          /**
           * En développement HTTP local, aucun certificat TLS
           * n'est impliqué.
           */
          secure: false,
        },
      },
    },

    preview: {
      host: "127.0.0.1",
      port: 4173,
      strictPort: true,
    },
  };
});
