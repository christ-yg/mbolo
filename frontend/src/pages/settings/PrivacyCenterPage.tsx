/**
 * Centre de confidentialité premium de Mbolo.
 *
 * Cette page permet à l'utilisateur :
 * - de comprendre les grands principes de traitement de ses données ;
 * - d'exporter une copie portable de ses informations personnelles ;
 * - de supprimer définitivement son compte avec double confirmation.
 *
 * Les appels API existants sont volontairement conservés. Le backend reste
 * l'autorité finale pour toutes les opérations sensibles.
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

const PRIVACY_PRINCIPLES = [
  {
    number: "01",
    eyebrow: "Minimisation",
    title: "Seulement les données utiles",
    description:
      "Mbolo limite la collecte aux informations nécessaires au fonctionnement, à la sécurité et à la qualité des rencontres.",
  },
  {
    number: "02",
    eyebrow: "Contrôle",
    title: "Des choix pilotés par toi",
    description:
      "Tu peux consulter ton profil, gérer ta visibilité, exporter tes données et demander l’effacement de ton compte.",
  },
  {
    number: "03",
    eyebrow: "Protection",
    title: "Les secrets restent secrets",
    description:
      "Les mots de passe, cookies, secrets de session et notes internes de sécurité ne sont jamais exposés dans ton export.",
  },
] as const;

export function PrivacyCenterPage() {
  const [password, setPassword] = useState("");
  const [confirmation, setConfirmation] = useState("");
  const [isExporting, setIsExporting] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);
  const [isFinalConfirmationOpen, setIsFinalConfirmationOpen] = useState(false);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  const canRequestDeletion = useMemo(
    () => (
      password.trim().length > 0
      && confirmation === REQUIRED_CONFIRMATION
      && !isExporting
      && !isDeleting
    ),
    [confirmation, isDeleting, isExporting, password],
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
          <p className="privacy-center-eyebrow">Tes droits et tes données</p>
          <h1 id="privacy-title">Garder le contrôle reste essentiel.</h1>
          <p className="privacy-center-hero__description">
            Consulte les principes de confidentialité de Mbolo, télécharge une
            copie de tes informations et exerce tes droits depuis un espace
            privé, lisible et protégé.
          </p>

          <div className="privacy-center-hero__actions">
            <button
              className="privacy-center-button privacy-center-button--primary"
              type="button"
              disabled={isExporting || isDeleting}
              onClick={() => void handleExport()}
            >
              {isExporting ? "Préparation de l’export…" : "Exporter mes données"}
              <span aria-hidden="true">→</span>
            </button>

            <Link
              className="privacy-center-button privacy-center-button--secondary"
              to="/account/security"
            >
              Centre de sécurité
            </Link>
          </div>
        </div>

        <aside className="privacy-center-trust-card">
          <div className="privacy-center-trust-card__mark" aria-hidden="true">M</div>
          <p className="privacy-center-trust-card__label">Confidentialité par conception</p>
          <h2>Ce qui est privé reste privé.</h2>
          <p>
            Les actions sensibles sont validées côté serveur. Une simple
            navigation ou redirection ne peut ni exporter ni supprimer ton compte.
          </p>
          <ul>
            <li>Export sans secrets d’authentification</li>
            <li>Suppression avec double confirmation</li>
            <li>Données des autres membres exclues</li>
          </ul>
        </aside>
      </section>

      <section className="privacy-center-status" aria-live="polite" aria-atomic="true">
        {message ? (
          <div className="privacy-center-alert privacy-center-alert--success">
            <span aria-hidden="true">✓</span>
            <p>{message}</p>
          </div>
        ) : null}

        {error ? (
          <div className="privacy-center-alert privacy-center-alert--error" role="alert">
            <span aria-hidden="true">!</span>
            <p>{error}</p>
          </div>
        ) : null}
      </section>

      <section className="privacy-center-principles" aria-labelledby="privacy-principles-title">
        <div className="privacy-center-section-heading">
          <div>
            <p className="privacy-center-eyebrow">Principes Mbolo</p>
            <h2 id="privacy-principles-title">Une confidentialité compréhensible.</h2>
          </div>
          <p>
            Les protections sont conçues pour rester claires avant même qu’une
            action sensible soit lancée.
          </p>
        </div>

        <div className="privacy-center-principles__grid">
          {PRIVACY_PRINCIPLES.map((principle) => (
            <article className="privacy-center-principle-card" key={principle.number}>
              <div className="privacy-center-principle-card__topline">
                <span>{principle.number}</span>
                <small>{principle.eyebrow}</small>
              </div>
              <h3>{principle.title}</h3>
              <p>{principle.description}</p>
            </article>
          ))}
        </div>
      </section>

      <section className="privacy-center-export" aria-labelledby="privacy-export-title">
        <div className="privacy-center-export__intro">
          <p className="privacy-center-eyebrow">Portabilité</p>
          <h2 id="privacy-export-title">Une copie claire de tes informations.</h2>
          <p>
            Le fichier JSON est généré côté serveur et contient les éléments
            utiles pour comprendre ton compte et ton activité sur Mbolo.
          </p>
        </div>

        <div className="privacy-center-export__details">
          <div className="privacy-center-info-panel">
            <span className="privacy-center-info-panel__icon" aria-hidden="true">✓</span>
            <div>
              <h3>Informations incluses</h3>
              <ul>
                <li>Compte, profil et préférences</li>
                <li>Interactions, matchs et messages envoyés</li>
                <li>Données utiles à la compréhension de ton activité</li>
              </ul>
            </div>
          </div>

          <div className="privacy-center-info-panel privacy-center-info-panel--muted">
            <span className="privacy-center-info-panel__icon" aria-hidden="true">—</span>
            <div>
              <h3>Informations volontairement exclues</h3>
              <ul>
                <li>Mot de passe, cookie ou secret d’authentification</li>
                <li>Adresse IP exacte ou clé technique interne</li>
                <li>Données appartenant aux autres membres</li>
              </ul>
            </div>
          </div>
        </div>

        <div className="privacy-center-export__footer">
          <p>
            <strong>Protection active :</strong> téléchargement non mis en cache
            et calculé selon les droits de ta session actuelle.
          </p>
          <button
            className="privacy-center-button privacy-center-button--primary"
            type="button"
            disabled={isExporting || isDeleting}
            onClick={() => void handleExport()}
          >
            {isExporting ? "Préparation…" : "Télécharger mon export"}
            <span aria-hidden="true">↓</span>
          </button>
        </div>
      </section>

      <section className="privacy-center-danger" aria-labelledby="privacy-delete-title">
        <div className="privacy-center-danger__intro">
          <p className="privacy-center-eyebrow privacy-center-eyebrow--danger">Zone sensible</p>
          <h2 id="privacy-delete-title">Supprimer définitivement mon compte.</h2>
          <p>
            Cette action efface ton identité Mbolo et les données personnelles
            associées. Elle est irréversible et exige ton mot de passe, une phrase
            exacte puis une confirmation finale.
          </p>

          <div className="privacy-center-danger__summary">
            <span aria-hidden="true">!</span>
            <p>
              Ton profil, tes photos, tes préférences, tes interactions et tes
              matchs seront notamment concernés.
            </p>
          </div>
        </div>

        <form className="privacy-center-danger__form" onSubmit={handleDeleteFormSubmit}>
          <div className="privacy-center-field">
            <label htmlFor="privacy-current-password">Mot de passe actuel</label>
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
            <label htmlFor="privacy-delete-confirmation">Phrase de confirmation</label>
            <p className="privacy-center-field__help">
              Recopie exactement : <strong>{REQUIRED_CONFIRMATION}</strong>
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

          <button
            className="privacy-center-button privacy-center-button--danger"
            type="submit"
            disabled={!canRequestDeletion}
          >
            {isDeleting ? "Suppression en cours…" : "Continuer vers la confirmation"}
            <span aria-hidden="true">→</span>
          </button>
        </form>
      </section>

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
            <span className="privacy-center-modal__icon" aria-hidden="true">!</span>
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
