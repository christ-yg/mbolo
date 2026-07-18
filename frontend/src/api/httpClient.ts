/**
 * Client HTTP centralisé de Mbolo.
 *
 * Toutes les communications avec Django doivent passer
 * par cette instance Axios.
 *
 * Nous évitons ainsi de répéter :
 *
 * - l'adresse de l'API ;
 * - l'envoi des cookies ;
 * - les paramètres CSRF ;
 * - les en-têtes communs ;
 * - le délai maximal des requêtes.
 */

import axios from "axios";

import { env } from "../config/env";

/**
 * Instance Axios dédiée à l'API Mbolo.
 */
export const httpClient = axios.create({
  /**
   * Préfixe local utilisé par toutes les requêtes.
   *
   * Exemple :
   *
   *     /api
   */
  baseURL: env.apiBaseUrl,

  /**
   * Autorise le navigateur à joindre les cookies de session
   * aux requêtes lorsque le contexte le permet.
   *
   * Ce paramètre sera également utile lorsque l'architecture
   * passera derrière un reverse proxy de production.
   */
  withCredentials: true,

  /**
   * Axios lit le cookie Django nommé "csrftoken".
   */
  xsrfCookieName: "csrftoken",

  /**
   * Axios place le jeton dans l'en-tête reconnu par Django.
   */
  xsrfHeaderName: "X-CSRFToken",

  /**
   * Délai maximal d'une requête : quinze secondes.
   *
   * Une requête ne doit pas rester bloquée indéfiniment.
   */
  timeout: 15_000,

  /**
   * Type de réponse attendu par défaut.
   */
  responseType: "json",

  headers: {
    /**
     * Indique au serveur que le frontend attend du JSON.
     */
    Accept: "application/json",

    /**
     * Ne pas définir globalement Content-Type ici.
     *
     * Axios doit pouvoir choisir automatiquement :
     *
     * - application/json ;
     * - multipart/form-data pour les photos.
     */
  },
});

/**
 * Intercepteur des requêtes sortantes.
 *
 * Il renforce certaines règles avant l'envoi.
 */
httpClient.interceptors.request.use((config) => {
  /**
   * Les URLs absolues sont refusées dans les appels métier.
   *
   * Tous les services doivent utiliser des chemins relatifs,
   * par exemple :
   *
   *     /v1/auth/login/
   *
   * Cela réduit le risque d'envoyer une requête vers une origine
   * externe à cause d'une valeur mal construite.
   */
  if (
    typeof config.url === "string" &&
    /^https?:\/\//i.test(config.url)
  ) {
    return Promise.reject(
      new Error(
        "Les URLs absolues sont interdites dans le client API Mbolo.",
      ),
    );
  }

  return config;
});
