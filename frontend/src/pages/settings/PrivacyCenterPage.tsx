/**
 * Centre de confidentialité Mbolo.
 *
 * Cette page permet à l'utilisateur :
 * - d'exporter une copie portable de ses données personnelles ;
 * - de comprendre quelles informations sont incluses ou exclues ;
 * - de supprimer définitivement son compte avec une double confirmation.
 *
 * Les appels API existants sont conservés. La refonte concerne
 * principalement l'expérience utilisateur, l'accessibilité et la sécurité
 * des actions sensibles.
 */

import {
  type FormEvent,
  useMemo,
  useState,
} from "react";
import { Link } from "react-router-dom";

import { normalizeApiError } from "../../api/apiError";
import {
  downloadPersonalData,
  permanentlyDeleteAccount,
} from "../../api/authService";

import "./PrivacyCenterPage.css";


const REQUIRED_CONFIRMATION = "SUPPRIMER DEFINITIVEMENT";


export function PrivacyCenterPage() {
  const [password, setPassword] = useState("");
  const [confirmation, setConfirmation] = useState("");
  const [isExporting, setIsExporting] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);
  const [isFinalConfirmationOpen, setIsFinalConfirmationOpen] = useState(false);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  /**
   * Le bouton de suppression reste désactivé tant que les deux conditions
   * locales minimales ne sont pas remplies.
   *
   * Le backend demeure l'autorité finale : il vérifie encore le mot de passe,
   * la phrase de confirmation et les droits de la session.
   */
  const canRequestDeletion = useMemo(
    () => (
      password.trim().length > 0
      && confirmation === REQUIRED_CONFIRMATION
      && !isExporting
      && !isDeleting
    ),
    [
      confirmation,
      isDeleting,
      isExporting,
      password,
    ],
  );


  async function handleExport() {
    if (isExporting || isDeleting) {
      return;
    }

    setIsExporting(true);
    setMessage("");
    setError("");

    try {
      await downloadPersonalData();
      setMessage(
        "Ton export JSON a été préparé et téléchargé de manière sécurisée.",
      );
    } catch (caught: unknown) {
      setError(normalizeApiError(caught).message);
    } finally {
      setIsExporting(false);
    }
  }


  function handleDeleteFormSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setMessage("");
    setError("");

    if (confirmation !== REQUIRED_CONFIRMATION) {
      setError(`Écris exactement ${REQUIRED_CONFIRMATION}.`);
      return;
    }

    if (password.trim().length === 0) {
      setError("Saisis ton mot de passe actuel.");
      return;
    }

    if (isDeleting || isExporting) {
      return;
    }

    /**
     * Une seconde confirmation visuelle est demandée avant l'appel API.
     * Aucune suppression n'est effectuée à cette étape.
     */
    setIsFinalConfirmationOpen(true);
  }


  async function confirmPermanentDeletion() {
    if (!canRequestDeletion) {
      setIsFinalConfirmationOpen(false);
      return;
    }

    setIsDeleting(true);
    setError("");
    setMessage("");

    try {
      await permanentlyDeleteAccount({
        current_password: password,
        confirmation,
      });

      /**
       * Après la suppression, la session n'est plus exploitable.
       * Une navigation complète vers l'accueil évite de conserver un ancien
       * état React ou une donnée sensible dans la mémoire de l'application.
       */
      window.location.assign("/");
    } catch (caught: unknown) {
      setError(normalizeApiError(caught).message);
      setIsDeleting(false);
      setIsFinalConfirmationOpen(false);
    }
  }


  return (
    <main className="privacy-center-page">
      <section className="privacy-center-hero" aria-labelledby="privacy-title">
        <div className="privacy-center-hero__content">
          <p className="privacy-center-eyebrow">
            Tes droits et tes données
          </p>

          <h1 id="privacy-title">
            Centre de confidentialité
          </h1>

          <p className="privacy-center-hero__description">
            Télécharge une copie portable de tes informations ou exerce ton
            droit à l’effacement depuis un espace clair, privé et sécurisé.
          </p>

          <Link
            className="privacy-center-back-link"
            to="/account/security"
          >
            <span aria-hidden="true">←</span>
            Retour à la sécurité du compte
          </Link>
        </div>

        <aside className="privacy-center-trust-card">
          <span className="privacy-center-trust-card__icon" aria-hidden="true">
            ◇
          </span>

          <div>
            <p className="privacy-center-trust-card__label">
              Contrôle personnel
            </p>
            <strong>
              Tes choix restent entre tes mains
            </strong>
            <p>
              Les opérations sensibles sont vérifiées côté serveur et ne sont
              jamais déclenchées par une simple navigation.
            </p>
          </div>
        </aside>
      </section>

      <section
        className="privacy-center-status"
        aria-live="polite"
        aria-atomic="true"
      >
        {message ? (
          <div className="privacy-center-alert privacy-center-alert--success">
            <span aria-hidden="true">✓</span>
            <p>{message}</p>
          </div>
        ) : null}

        {error ? (
          <div
            className="privacy-center-alert privacy-center-alert--error"
            role="alert"
          >
            <span aria-hidden="true">!</span>
            <p>{error}</p>
          </div>
        ) : null}
      </section>

      <div className="privacy-center-grid">
        <section
          className="privacy-center-card privacy-center-card--export"
          aria-labelledby="privacy-export-title"
        >
          <header className="privacy-center-card__header">
            <span className="privacy-center-card__icon" aria-hidden="true">
              ↓
            </span>

            <div>
              <p className="privacy-center-eyebrow">
                Portabilité
              </p>
              <h2 id="privacy-export-title">
                Exporter mes données
              </h2>
            </div>
          </header>

          <p className="privacy-center-card__intro">
            Reçois un fichier JSON structuré contenant les informations liées
            à ton utilisation de Mbolo.
          </p>

          <div className="privacy-center-info-block">
            <p className="privacy-center-info-block__title">
              Informations incluses
            </p>

            <ul className="privacy-center-check-list">
              <li>Compte, profil et préférences</li>
              <li>Interactions, matchs et messages envoyés</li>
              <li>Données utiles à la compréhension de ton activité</li>
            </ul>
          </div>

          <div className="privacy-center-info-block">
            <p className="privacy-center-info-block__title">
              Informations exclues
            </p>

            <ul className="privacy-center-check-list privacy-center-check-list--muted">
              <li>Aucun mot de passe, cookie ou secret d’authentification</li>
              <li>Aucune adresse IP exacte ni clé technique interne</li>
              <li>Aucune donnée appartenant aux autres membres</li>
            </ul>
          </div>

          <div className="privacy-center-security-note">
            <span aria-hidden="true">✓</span>
            <p>
              Fichier généré côté serveur et téléchargement non mis en cache.
            </p>
          </div>

          <button
            className="privacy-center-button privacy-center-button--primary"
            type="button"
            disabled={isExporting || isDeleting}
            onClick={() => void handleExport()}
          >
            {isExporting ? "Préparation de l’export…" : "Télécharger mes données"}
            <span aria-hidden="true">→</span>
          </button>
        </section>

        <form
          className="privacy-center-card privacy-center-card--danger"
          onSubmit={handleDeleteFormSubmit}
          aria-labelledby="privacy-delete-title"
        >
          <header className="privacy-center-card__header">
            <span
              className="privacy-center-card__icon privacy-center-card__icon--danger"
              aria-hidden="true"
            >
              !
            </span>

            <div>
              <p className="privacy-center-eyebrow privacy-center-eyebrow--danger">
                Zone sensible
              </p>
              <h2 id="privacy-delete-title">
                Supprimer mon compte
              </h2>
            </div>
          </header>

          <p className="privacy-center-card__intro">
            Cette action efface définitivement ton identité Mbolo et les
            données personnelles associées. Elle ne peut pas être annulée.
          </p>

          <div className="privacy-center-danger-summary">
            <p className="privacy-center-info-block__title">
              Seront notamment supprimés
            </p>

            <ul className="privacy-center-check-list privacy-center-check-list--danger">
              <li>Ton profil et tes photos</li>
              <li>Tes préférences et tes interactions</li>
              <li>Tes matchs et les données associées au compte</li>
            </ul>
          </div>

          <div className="privacy-center-field">
            <label htmlFor="privacy-current-password">
              Mot de passe actuel
            </label>

            <input
              id="privacy-current-password"
              type="password"
              autoComplete="current-password"
              value={password}
              disabled={isDeleting}
              onChange={(event) => setPassword(event.target.value)}
              placeholder="Saisis ton mot de passe"
            />
          </div>

          <div className="privacy-center-field">
            <label htmlFor="privacy-delete-confirmation">
              Phrase de confirmation
            </label>

            <p className="privacy-center-field__help">
              Recopie exactement :
              {" "}
              <strong>{REQUIRED_CONFIRMATION}</strong>
            </p>

            <input
              id="privacy-delete-confirmation"
              type="text"
              autoComplete="off"
              spellCheck={false}
              value={confirmation}
              disabled={isDeleting}
              onChange={(event) => setConfirmation(event.target.value)}
              placeholder={REQUIRED_CONFIRMATION}
            />
          </div>

          <div className="privacy-center-danger-note">
            <span aria-hidden="true">!</span>
            <p>
              Une dernière confirmation sera demandée avant l’effacement.
            </p>
          </div>

          <button
            className="privacy-center-button privacy-center-button--danger"
            type="submit"
            disabled={!canRequestDeletion}
          >
            {isDeleting ? "Suppression en cours…" : "Continuer vers la confirmation"}
            <span aria-hidden="true">→</span>
          </button>
        </form>
      </div>

      {isFinalConfirmationOpen ? (
        <div
          className="privacy-center-modal"
          role="dialog"
          aria-modal="true"
          aria-labelledby="privacy-final-confirmation-title"
        >
          <button
            type="button"
            className="privacy-center-modal__backdrop"
            aria-label="Fermer la confirmation"
            disabled={isDeleting}
            onClick={() => setIsFinalConfirmationOpen(false)}
          />

          <section className="privacy-center-modal__content">
            <span className="privacy-center-modal__icon" aria-hidden="true">
              !
            </span>

            <p className="privacy-center-eyebrow privacy-center-eyebrow--danger">
              Confirmation finale
            </p>

            <h2 id="privacy-final-confirmation-title">
              Supprimer définitivement ce compte ?
            </h2>

            <p>
              Ton profil, tes photos et les données associées seront effacés.
              Cette décision est irréversible.
            </p>

            <div className="privacy-center-modal__actions">
              <button
                className="privacy-center-button privacy-center-button--secondary"
                type="button"
                disabled={isDeleting}
                onClick={() => setIsFinalConfirmationOpen(false)}
              >
                Annuler
              </button>

              <button
                className="privacy-center-button privacy-center-button--danger"
                type="button"
                disabled={isDeleting}
                onClick={() => void confirmPermanentDeletion()}
              >
                {isDeleting ? "Suppression…" : "Oui, supprimer définitivement"}
              </button>
            </div>
          </section>
        </div>
      ) : null}
    </main>
  );
}
