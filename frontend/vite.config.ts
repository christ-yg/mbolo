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

        /**
         * Les connexions WebSocket utilisent elles aussi la même origine
         * que le frontend. Vite relaie ensuite le handshake vers Daphne.
         *
         * Cela reproduit fidèlement l'architecture Nginx de production et
         * garantit l'envoi du cookie de session Django.
         */
        "/ws": {
          target: proxyTarget,
          changeOrigin: true,
          secure: false,
          ws: true,
        },
      },
    },

    build: {
      /**
       * Sépare les bibliothèques principales du code métier Mbolo.
       *
       * Le navigateur peut ainsi conserver les dépendances en cache et
       * télécharger des fichiers plus petits lors des mises à jour.
       */
      rollupOptions: {
        output: {
          manualChunks(id) {
            if (id.includes("node_modules/react-router")) {
              return "router";
            }

            if (
              id.includes("node_modules/react") ||
              id.includes("node_modules/react-dom")
            ) {
              return "react";
            }

            if (id.includes("node_modules/axios")) {
              return "http";
            }

            if (id.includes("node_modules")) {
              return "vendor";
            }

            return undefined;
          },
        },
      },

      /**
       * Un avertissement à 650 kB reste suffisamment strict sans masquer
       * une véritable régression de performance.
       */
      chunkSizeWarningLimit: 650,

      sourcemap: false,
    },

    preview: {
      host: "127.0.0.1",
      port: 4173,
      strictPort: true,
    },
  };
});
