import { type FormEvent, useState } from "react";

import { normalizeApiError } from "../../api/apiError";
import {
  changePassword,
  deactivateAccount,
  revokeOtherSessions,
} from "../../api/authService";

type ActionName = "password" | "sessions" | "deactivate" | null;

export function AccountSecurityPage() {
  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [newPasswordConfirmation, setNewPasswordConfirmation] =
    useState("");
  const [sessionPassword, setSessionPassword] = useState("");
  const [deactivationPassword, setDeactivationPassword] = useState("");
  const [confirmation, setConfirmation] = useState("");
  const [activeAction, setActiveAction] = useState<ActionName>(null);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  function begin(action: ActionName) {
    setActiveAction(action);
    setMessage("");
    setError("");
  }

  async function submitPassword(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (newPassword.length < 12) {
      setError("Le nouveau mot de passe doit contenir au moins 12 caractères.");
      return;
    }
    if (newPassword !== newPasswordConfirmation) {
      setError("Les deux nouveaux mots de passe ne correspondent pas.");
      return;
    }
    begin("password");
    try {
      await changePassword({
        current_password: currentPassword,
        new_password: newPassword,
        new_password_confirmation: newPasswordConfirmation,
      });
      setCurrentPassword("");
      setNewPassword("");
      setNewPasswordConfirmation("");
      setMessage(
        "Mot de passe modifié. Toutes les autres sessions ont été fermées.",
      );
    } catch (caught: unknown) {
      setError(normalizeApiError(caught).message);
    } finally {
      setActiveAction(null);
    }
  }

  async function submitSessions(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    begin("sessions");
    try {
      await revokeOtherSessions({ current_password: sessionPassword });
      setSessionPassword("");
      setMessage("Les autres appareils ont été déconnectés.");
    } catch (caught: unknown) {
      setError(normalizeApiError(caught).message);
    } finally {
      setActiveAction(null);
    }
  }

  async function submitDeactivation(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (confirmation !== "DESACTIVER") {
      setError("Écris exactement DESACTIVER pour confirmer.");
      return;
    }
    begin("deactivate");
    try {
      await deactivateAccount({
        current_password: deactivationPassword,
        confirmation,
      });
      window.location.assign("/");
    } catch (caught: unknown) {
      setError(normalizeApiError(caught).message);
      setActiveAction(null);
    }
  }

  return (
    <main className="account-security-page">
      <section className="account-security-page__hero">
        <p className="section-heading__eyebrow">Protection du compte</p>
        <h1>Sécurité de mon compte</h1>
        <p>
          Contrôle ton mot de passe, tes appareils connectés et l’accès à ton compte.
        </p>
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

      <div className="account-security-grid">
        <form className="security-action-card" onSubmit={submitPassword}>
          <p className="section-heading__eyebrow">Mot de passe</p>
          <h2>Changer mon mot de passe</h2>
          <p>Cette action déconnecte automatiquement tous les autres appareils.</p>
          <label>
            Mot de passe actuel
            <input
              type="password"
              autoComplete="current-password"
              value={currentPassword}
              onChange={(event) => setCurrentPassword(event.target.value)}
            />
          </label>
          <label>
            Nouveau mot de passe
            <input
              type="password"
              autoComplete="new-password"
              value={newPassword}
              onChange={(event) => setNewPassword(event.target.value)}
            />
          </label>
          <label>
            Confirmation
            <input
              type="password"
              autoComplete="new-password"
              value={newPasswordConfirmation}
              onChange={(event) =>
                setNewPasswordConfirmation(event.target.value)
              }
            />
          </label>
          <button disabled={activeAction !== null}>
            {activeAction === "password" ? "Modification…" : "Changer le mot de passe"}
          </button>
        </form>

        <form className="security-action-card" onSubmit={submitSessions}>
          <p className="section-heading__eyebrow">Appareils</p>
          <h2>Fermer les autres sessions</h2>
          <p>Ta session actuelle reste ouverte. Tous les autres appareils sont déconnectés.</p>
          <label>
            Mot de passe actuel
            <input
              type="password"
              autoComplete="current-password"
              value={sessionPassword}
              onChange={(event) => setSessionPassword(event.target.value)}
            />
          </label>
          <button disabled={activeAction !== null}>
            {activeAction === "sessions" ? "Déconnexion…" : "Déconnecter les autres appareils"}
          </button>
        </form>

        <form
          className="security-action-card security-action-card--danger"
          onSubmit={submitDeactivation}
        >
          <p className="section-heading__eyebrow">Zone sensible</p>
          <h2>Désactiver mon compte</h2>
          <p>Ton profil disparaît et toutes tes sessions sont immédiatement fermées.</p>
          <label>
            Mot de passe actuel
            <input
              type="password"
              autoComplete="current-password"
              value={deactivationPassword}
              onChange={(event) => setDeactivationPassword(event.target.value)}
            />
          </label>
          <label>
            Écris DESACTIVER
            <input
              type="text"
              autoComplete="off"
              value={confirmation}
              onChange={(event) => setConfirmation(event.target.value)}
            />
          </label>
          <button disabled={activeAction !== null}>
            {activeAction === "deactivate" ? "Désactivation…" : "Désactiver mon compte"}
          </button>
        </form>
      </div>
    </main>
  );
}
