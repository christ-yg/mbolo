/**
 * Normalisation des erreurs Axios et Django REST Framework.
 *
 * Les composants React ne doivent pas analyser eux-mêmes
 * toutes les formes possibles de réponses réseau.
 */

import axios from "axios";

import type {
  ApiErrorPayload,
  NormalizedApiError,
} from "../types/api";

/**
 * Message générique volontairement neutre.
 *
 * Il évite d'afficher directement une erreur technique interne
 * ou une information trop précise provenant du serveur.
 */
const DEFAULT_ERROR_MESSAGE =
  "Une erreur est survenue. Réessaie dans quelques instants.";

/**
 * Convertit une valeur inconnue en tableau de messages.
 */
function normalizeMessages(value: unknown): string[] {
  if (typeof value === "string") {
    return [value];
  }

  if (Array.isArray(value)) {
    return value
      .filter(
        (item): item is string =>
          typeof item === "string",
      )
      .map((item) => item.trim())
      .filter(Boolean);
  }

  return [];
}

/**
 * Extrait les erreurs correspondant aux champs de formulaire.
 */
function extractFieldErrors(
  payload: ApiErrorPayload,
): Record<string, string[]> {
  const fieldErrors: Record<string, string[]> = {};

  /**
   * Certains endpoints peuvent regrouper les erreurs sous "errors".
   */
  const errorContainer =
    payload.errors &&
    typeof payload.errors === "object" &&
    !Array.isArray(payload.errors)
      ? payload.errors
      : payload;

  for (const [fieldName, value] of Object.entries(
    errorContainer,
  )) {
    /**
     * Ces propriétés sont des messages généraux, pas des champs.
     */
    if (
      fieldName === "message" ||
      fieldName === "detail" ||
      fieldName === "error" ||
      fieldName === "errors"
    ) {
      continue;
    }

    const messages = normalizeMessages(value);

    if (messages.length > 0) {
      fieldErrors[fieldName] = messages;
    }
  }

  return fieldErrors;
}

/**
 * Convertit toute erreur inconnue en structure stable.
 *
 * Avantages :
 *
 * - aucun composant ne dépend directement d'Axios ;
 * - les erreurs réseau sont distinguées des erreurs HTTP ;
 * - les messages techniques ne sont pas affichés automatiquement ;
 * - les erreurs de validation restent associées aux champs.
 */
export function normalizeApiError(
  error: unknown,
): NormalizedApiError {
  if (!axios.isAxiosError<ApiErrorPayload>(error)) {
    return {
      status: null,
      message: DEFAULT_ERROR_MESSAGE,
      fieldErrors: {},
      isNetworkError: false,
    };
  }

  /**
   * Axios n'a reçu aucune réponse :
   *
   * - Django est arrêté ;
   * - le proxy est indisponible ;
   * - une coupure réseau s'est produite.
   */
  if (!error.response) {
    return {
      status: null,
      message:
        "Le service est temporairement indisponible. Vérifie ta connexion puis réessaie.",
      fieldErrors: {},
      isNetworkError: true,
    };
  }

  const payload = error.response.data ?? {};
  const status = error.response.status;

  const serverMessage =
    typeof payload.message === "string"
      ? payload.message
      : typeof payload.detail === "string"
        ? payload.detail
        : typeof payload.error === "string"
          ? payload.error
          : null;

  return {
    status,
    message:
      serverMessage?.trim() ||
      getFallbackMessageForStatus(status),
    fieldErrors: extractFieldErrors(payload),
    isNetworkError: false,
  };
}

/**
 * Produit un message compréhensible selon le statut HTTP.
 *
 * Nous évitons de reprendre aveuglément les messages techniques
 * internes du navigateur ou du serveur.
 */
function getFallbackMessageForStatus(
  status: number,
): string {
  switch (status) {
    case 400:
      return "Certaines informations envoyées sont invalides.";

    case 401:
    case 403:
      return "Cette opération n'est pas autorisée.";

    case 404:
      return "La ressource demandée est introuvable.";

    case 409:
      return "Cette opération entre en conflit avec une donnée existante.";

    case 413:
      return "Le fichier envoyé est trop volumineux.";

    case 429:
      return "Trop de tentatives ont été effectuées. Réessaie plus tard.";

    default:
      if (status >= 500) {
        return "Le serveur rencontre momentanément un problème.";
      }

      return DEFAULT_ERROR_MESSAGE;
  }
}
