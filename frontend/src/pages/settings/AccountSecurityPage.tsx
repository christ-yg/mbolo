import { type FormEvent, useEffect, useState } from "react";
import { Link } from "react-router-dom";

import { normalizeApiError } from "../../api/apiError";
import {
  changePassword,
  deactivateAccount,
  revokeOtherSessions,
  setEmailTwoFactor,
  getLoginActivity,
} from "../../api/authService";
import { useAuth } from "../../hooks/useAuth";
import type { LoginActivity } from "../../types/auth";

type ActionName = "password" | "sessions" | "twoFactor" | "deactivate" | null;

export function AccountSecurityPage() {
  const { user, refreshCurrentUser } = useAuth();
  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [newPasswordConfirmation, setNewPasswordConfirmation] =
    useState("");
  const [sessionPassword, setSessionPassword] = useState("");
  const [deactivationPassword, setDeactivationPassword] = useState("");
  const [confirmation, setConfirmation] = useState("");
  const [twoFactorPassword, setTwoFactorPassword] = useState("");
  const [activeAction, setActiveAction] = useState<ActionName>(null);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [loginActivities, setLoginActivities] =
    useState<LoginActivity[]>([]);

  useEffect(() => {
    void getLoginActivity()
      .then(setLoginActivities)
      .catch(() => {
        // La page de sécurité reste utilisable si l'historique échoue.
      });
  }, []);

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

  async function submitTwoFactor(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    begin("twoFactor");
    try {
      const enabled = await setEmailTwoFactor({
        current_password: twoFactorPassword,
        enabled: !user?.emailTwoFactorEnabled,
      });
      setTwoFactorPassword("");
      await refreshCurrentUser();
      setMessage(
        enabled
          ? "Double authentification activée. Un code sera demandé à la prochaine connexion."
          : "Double authentification désactivée.",
      );
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
        <Link to="/account/privacy">
          Gérer mes données et ma confidentialité →
        </Link>
        <Link to="/profile/verification">
          Vérifier réellement mon profil →
        </Link>
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
        <section className="security-action-card">
          <p className="section-heading__eyebrow">Activité récente</p>
          <h2>Connexions à mon compte</h2>
          <p>
            L’adresse IP exacte n’est jamais affichée ni conservée ici.
            L’empreinte permet seulement de comparer deux connexions.
          </p>
          {loginActivities.length ? (
            <ul className="security-activity-list">
              {loginActivities.map((activity) => (
                <li key={activity.id}>
                  <strong>{activity.device}</strong>
                  <span>
                    {activity.method === "email_2fa"
                      ? "Code e-mail confirmé"
                      : "Mot de passe"}
                    {" · "}
                    {new Intl.DateTimeFormat("fr-FR", {
                      dateStyle: "medium",
                      timeStyle: "short",
                    }).format(new Date(activity.createdAt))}
                  </span>
                  <small>Empreinte réseau : {activity.ipFingerprint || "indisponible"}</small>
                </li>
              ))}
            </ul>
          ) : (
            <p>Aucune connexion récente enregistrée.</p>
          )}
        </section>

        <form className="security-action-card" onSubmit={submitTwoFactor}>
          <p className="section-heading__eyebrow">Connexion renforcée</p>
          <h2>Double authentification par e-mail</h2>
          <p>
            Statut : <strong>
              {user?.emailTwoFactorEnabled ? "activée" : "désactivée"}
            </strong>. Après le mot de passe, Mbolo envoie un code temporaire
            à ton adresse e-mail vérifiée.
          </p>
          <label>
            Mot de passe actuel
            <input
              type="password"
              autoComplete="current-password"
              required
              value={twoFactorPassword}
              onChange={(event) => setTwoFactorPassword(event.target.value)}
            />
          </label>
          <button disabled={activeAction !== null}>
            {activeAction === "twoFactor"
              ? "Mise à jour…"
              : user?.emailTwoFactorEnabled
                ? "Désactiver la double authentification"
                : "Activer la double authentification"}
          </button>
        </form>

        <section className="security-action-card">
          <p className="section-heading__eyebrow">Confiance</p>
          <h2>Badge Profil vérifié</h2>
          <p>
            Envoie un selfie privé pour confirmer que ton visage correspond
            à la photo principale de ton profil.
          </p>
          <Link to="/profile/verification">
            Consulter mon statut de vérification →
          </Link>
        </section>

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
