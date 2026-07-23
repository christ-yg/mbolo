import { type FormEvent, useState } from "react";
import { Link } from "react-router-dom";

import { normalizeApiError } from "../../api/apiError";
import {
  downloadPersonalData,
  permanentlyDeleteAccount,
} from "../../api/authService";

export function PrivacyCenterPage() {
  const [password, setPassword] = useState("");
  const [confirmation, setConfirmation] = useState("");
  const [isExporting, setIsExporting] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  async function handleExport() {
    if (isExporting) return;
    setIsExporting(true);
    setMessage("");
    setError("");
    try {
      await downloadPersonalData();
      setMessage("Ton export JSON a été téléchargé.");
    } catch (caught: unknown) {
      setError(normalizeApiError(caught).message);
    } finally {
      setIsExporting(false);
    }
  }

  async function handleDelete(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (confirmation !== "SUPPRIMER DEFINITIVEMENT") {
      setError("Écris exactement SUPPRIMER DEFINITIVEMENT.");
      return;
    }
    if (isDeleting) return;
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
    }
  }

  return (
    <main className="privacy-center-page">
      <section className="privacy-center-page__hero">
        <p className="section-heading__eyebrow">Tes droits et tes données</p>
        <h1>Centre de confidentialité</h1>
        <p>
          Télécharge une copie portable de tes informations ou exerce ton droit
          à l’effacement.
        </p>
        <Link to="/account/security">← Retour à la sécurité du compte</Link>
      </section>

      {message ? (
        <div className="form-alert form-alert--success" role="status">
          <span aria-hidden="true">✓</span><p>{message}</p>
        </div>
      ) : null}
      {error ? (
        <div className="form-alert form-alert--error" role="alert">
          <span aria-hidden="true">!</span><p>{error}</p>
        </div>
      ) : null}

      <div className="privacy-center-grid">
        <section className="privacy-card">
          <p className="section-heading__eyebrow">Portabilité</p>
          <h2>Exporter mes données</h2>
          <p>
            Le fichier JSON contient ton compte, ton profil, tes préférences,
            tes interactions, tes matchs et tes messages envoyés.
          </p>
          <ul>
            <li>Aucun mot de passe ou cookie</li>
            <li>Aucune adresse IP ou clé interne</li>
            <li>Téléchargement non mis en cache</li>
          </ul>
          <button
            type="button"
            disabled={isExporting || isDeleting}
            onClick={() => void handleExport()}
          >
            {isExporting ? "Préparation…" : "Télécharger mes données"}
          </button>
        </section>

        <form
          className="privacy-card privacy-card--danger"
          onSubmit={handleDelete}
        >
          <p className="section-heading__eyebrow">Droit à l’effacement</p>
          <h2>Supprimer définitivement mon compte</h2>
          <p>
            Cette opération supprime ton profil, tes photos et les données
            associées. Elle ne peut pas être annulée.
          </p>
          <label>
            Mot de passe actuel
            <input
              type="password"
              autoComplete="current-password"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
            />
          </label>
          <label>
            Écris SUPPRIMER DEFINITIVEMENT
            <input
              type="text"
              autoComplete="off"
              value={confirmation}
              onChange={(event) => setConfirmation(event.target.value)}
            />
          </label>
          <button disabled={isExporting || isDeleting}>
            {isDeleting ? "Suppression…" : "Supprimer définitivement"}
          </button>
        </form>
      </div>
    </main>
  );
}
