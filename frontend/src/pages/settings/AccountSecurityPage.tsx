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
import {
  getLoginAlertEmailPreference,
  updateLoginAlertEmailPreference,
} from "../../api/securityAlertService";
import { getAccountSecurityEvents } from "../../api/securityEventService";
import { ConnectedDevicesCard } from "../../components/security/ConnectedDevicesCard";
import { useAuth } from "../../hooks/useAuth";
import type { LoginActivity } from "../../types/auth";
import type { AccountSecurityEvent } from "../../types/securityEvents";

import "./AccountSecurityPage.css";


type ActionName =
  | "password"
  | "sessions"
  | "twoFactor"
  | "loginAlerts"
  | "deactivate"
  | null;


const securityEventLabels: Record<string, string> = {
  "auth.password_change": "Mot de passe modifié",
  "auth.sessions_revoke": "Autres sessions fermées",
  "auth.email_2fa_settings": "Double authentification mise à jour",
  "auth.login_alert_email_preference": "Alertes par e-mail mises à jour",
  "auth.password_reset_confirm": "Mot de passe réinitialisé",
  "auth.account_deactivate": "Compte désactivé",
};


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
  const [loginAlertPassword, setLoginAlertPassword] = useState("");

  const [loginAlertEmailsEnabled, setLoginAlertEmailsEnabled] =
    useState(true);
  const [
    isLoadingLoginAlertPreference,
    setIsLoadingLoginAlertPreference,
  ] = useState(true);

  const [activeAction, setActiveAction] =
    useState<ActionName>(null);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  const [loginActivities, setLoginActivities] =
    useState<LoginActivity[]>([]);
  const [securityEvents, setSecurityEvents] =
    useState<AccountSecurityEvent[]>([]);


  async function refreshSecurityEvents() {
    try {
      setSecurityEvents(await getAccountSecurityEvents());
    } catch {
      // Le journal secondaire ne doit pas bloquer la page.
    }
  }


  useEffect(() => {
    void getLoginActivity()
      .then(setLoginActivities)
      .catch(() => {
        // La page reste utilisable si l'historique échoue.
      });

    void refreshSecurityEvents();

    void getLoginAlertEmailPreference()
      .then((preference) => {
        setLoginAlertEmailsEnabled(
          preference.loginAlertEmailsEnabled,
        );
      })
      .catch(() => {
        setError(
          "Impossible de charger la préférence des alertes par e-mail.",
        );
      })
      .finally(() => {
        setIsLoadingLoginAlertPreference(false);
      });
  }, []);


  function begin(action: ActionName) {
    setActiveAction(action);
    setMessage("");
    setError("");
  }


  async function submitPassword(
    event: FormEvent<HTMLFormElement>,
  ) {
    event.preventDefault();

    if (newPassword.length < 12) {
      setError(
        "Le nouveau mot de passe doit contenir au moins 12 caractères.",
      );
      return;
    }

    if (newPassword !== newPasswordConfirmation) {
      setError(
        "Les deux nouveaux mots de passe ne correspondent pas.",
      );
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

      await refreshSecurityEvents();

      setMessage(
        "Mot de passe modifié. Toutes les autres sessions ont été fermées.",
      );
    } catch (caught: unknown) {
      setError(normalizeApiError(caught).message);
    } finally {
      setActiveAction(null);
    }
  }


  async function submitSessions(
    event: FormEvent<HTMLFormElement>,
  ) {
    event.preventDefault();
    begin("sessions");

    try {
      await revokeOtherSessions({
        current_password: sessionPassword,
      });

      setSessionPassword("");
      await refreshSecurityEvents();

      setMessage("Les autres appareils ont été déconnectés.");
    } catch (caught: unknown) {
      setError(normalizeApiError(caught).message);
    } finally {
      setActiveAction(null);
    }
  }


  async function submitTwoFactor(
    event: FormEvent<HTMLFormElement>,
  ) {
    event.preventDefault();
    begin("twoFactor");

    try {
      const enabled = await setEmailTwoFactor({
        current_password: twoFactorPassword,
        enabled: !user?.emailTwoFactorEnabled,
      });

      setTwoFactorPassword("");

      await refreshCurrentUser();
      await refreshSecurityEvents();

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


  async function submitLoginAlerts(
    event: FormEvent<HTMLFormElement>,
  ) {
    event.preventDefault();
    begin("loginAlerts");

    try {
      const preference = await updateLoginAlertEmailPreference({
        current_password: loginAlertPassword,
        enabled: !loginAlertEmailsEnabled,
      });

      setLoginAlertPassword("");
      setLoginAlertEmailsEnabled(
        preference.loginAlertEmailsEnabled,
      );

      await refreshSecurityEvents();

      setMessage(
        preference.loginAlertEmailsEnabled
          ? "Les alertes de connexion par e-mail sont activées."
          : (
              "Les alertes par e-mail sont désactivées. " +
              "Les notifications internes restent actives."
            ),
      );
    } catch (caught: unknown) {
      setError(normalizeApiError(caught).message);
    } finally {
      setActiveAction(null);
    }
  }


  async function submitDeactivation(
    event: FormEvent<HTMLFormElement>,
  ) {
    event.preventDefault();

    if (confirmation !== "DESACTIVER") {
      setError(
        "Écris exactement DESACTIVER pour confirmer.",
      );
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
    <main className="account-security-page security-premium-page">
      <section className="security-premium-hero">
        <div className="security-premium-hero__content">
          <p className="section-heading__eyebrow">
            Protection du compte
          </p>

          <h1>Sécurité de mon compte</h1>

          <p className="security-premium-hero__description">
            Gère tes accès, surveille tes connexions et renforce
            la protection de ton identité Mbolo.
          </p>

          <div className="security-premium-hero__actions">
            <Link
              className="security-premium-hero__action"
              to="/account/privacy"
            >
              <span aria-hidden="true">◌</span>
              <span>
                <strong>Confidentialité</strong>
                <small>Gérer mes données personnelles</small>
              </span>
              <span aria-hidden="true">→</span>
            </Link>

            <Link
              className="security-premium-hero__action"
              to="/profile/verification"
            >
              <span aria-hidden="true">✓</span>
              <span>
                <strong>Profil vérifié</strong>
                <small>Renforcer la confiance sur Mbolo</small>
              </span>
              <span aria-hidden="true">→</span>
            </Link>
          </div>
        </div>

        <aside className="security-premium-score">
          <p>Niveau de protection</p>

          <div className="security-premium-score__value">
            <strong>
              {user?.emailTwoFactorEnabled ? "Élevé" : "Standard"}
            </strong>
            <span
              className={[
                "security-premium-score__dot",
                user?.emailTwoFactorEnabled
                  ? "security-premium-score__dot--strong"
                  : "",
              ].join(" ")}
            />
          </div>

          <ul>
            <li>
              <span aria-hidden="true">✓</span>
              Alertes internes actives
            </li>
            <li>
              <span aria-hidden="true">✓</span>
              Historique sécurisé
            </li>
            <li>
              <span aria-hidden="true">
                {user?.emailTwoFactorEnabled ? "✓" : "○"}
              </span>
              Double authentification
            </li>
          </ul>
        </aside>
      </section>

      {message ? (
        <div
          className="form-alert form-alert--success security-premium-alert"
          role="status"
        >
          <span aria-hidden="true">✓</span>
          <p>{message}</p>
        </div>
      ) : null}

      {error ? (
        <div
          className="form-alert form-alert--error security-premium-alert"
          role="alert"
        >
          <span aria-hidden="true">!</span>
          <p>{error}</p>
        </div>
      ) : null}

      <section className="security-premium-section">
        <div className="security-premium-section__heading">
          <div>
            <p className="section-heading__eyebrow">
              Surveillance
            </p>
            <h2>Activité et appareils</h2>
          </div>

          <p>
            Consulte les connexions récentes et garde le contrôle
            sur les sessions ouvertes.
          </p>
        </div>

        <div className="account-security-grid">
          <section className="security-action-card">
            <p className="section-heading__eyebrow">
              Activité récente
            </p>
            <h2>Connexions à mon compte</h2>
            <p>
              L’adresse IP exacte n’est jamais affichée ni conservée.
              L’empreinte sert uniquement à comparer les connexions.
            </p>

            {loginActivities.length ? (
              <ul className="security-activity-list">
                {loginActivities.slice(0, 8).map((activity) => (
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
                      }).format(
                        new Date(activity.createdAt),
                      )}
                    </span>
                    <small>
                      Empreinte réseau :{" "}
                      {activity.ipFingerprint || "indisponible"}
                    </small>
                  </li>
                ))}
              </ul>
            ) : (
              <p>Aucune connexion récente enregistrée.</p>
            )}
          </section>

          <ConnectedDevicesCard />

          <section className="security-action-card">
            <p className="section-heading__eyebrow">
              Journal de sécurité
            </p>
            <h2>Actions sensibles du compte</h2>
            <p>
              Mbolo conserve uniquement le type d’action, son résultat
              et sa date.
            </p>

            {securityEvents.length ? (
              <ul className="security-activity-list">
                {securityEvents.slice(0, 10).map((securityEvent) => (
                  <li key={securityEvent.id}>
                    <strong>
                      {securityEventLabels[securityEvent.event] ??
                        "Action de sécurité"}
                    </strong>
                    <span>
                      {securityEvent.outcome === "success"
                        ? "Réussie"
                        : "Échec"}
                      {" · "}
                      {new Intl.DateTimeFormat("fr-FR", {
                        dateStyle: "medium",
                        timeStyle: "short",
                      }).format(
                        new Date(securityEvent.createdAt),
                      )}
                    </span>
                  </li>
                ))}
              </ul>
            ) : (
              <p>
                Aucune action sensible enregistrée pour le moment.
              </p>
            )}
          </section>
        </div>
      </section>

      <section className="security-premium-section">
        <div className="security-premium-section__heading">
          <div>
            <p className="section-heading__eyebrow">
              Renforcement
            </p>
            <h2>Protection de la connexion</h2>
          </div>

          <p>
            Active les protections supplémentaires adaptées à ton compte.
          </p>
        </div>

        <div className="account-security-grid">
          <form
            className="security-action-card"
            onSubmit={submitTwoFactor}
          >
            <div className="security-card-status">
              <span
                className={[
                  "security-card-status__indicator",
                  user?.emailTwoFactorEnabled
                    ? "security-card-status__indicator--active"
                    : "",
                ].join(" ")}
              />
              {user?.emailTwoFactorEnabled
                ? "Activée"
                : "Désactivée"}
            </div>

            <p className="section-heading__eyebrow">
              Connexion renforcée
            </p>
            <h2>Double authentification par e-mail</h2>
            <p>
              Après le mot de passe, Mbolo envoie un code temporaire
              à ton adresse e-mail vérifiée.
            </p>

            <label>
              Mot de passe actuel
              <input
                type="password"
                autoComplete="current-password"
                required
                value={twoFactorPassword}
                onChange={(event) =>
                  setTwoFactorPassword(event.target.value)
                }
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

          <form
            className="security-action-card"
            onSubmit={submitLoginAlerts}
          >
            <div className="security-card-status">
              <span
                className={[
                  "security-card-status__indicator",
                  loginAlertEmailsEnabled
                    ? "security-card-status__indicator--active"
                    : "",
                ].join(" ")}
              />
              {isLoadingLoginAlertPreference
                ? "Chargement"
                : loginAlertEmailsEnabled
                  ? "Activées"
                  : "Désactivées"}
            </div>

            <p className="section-heading__eyebrow">
              Alertes de sécurité
            </p>
            <h2>Nouvelles connexions par e-mail</h2>
            <p>
              Les notifications internes restent toujours actives,
              même lorsque les e-mails sont désactivés.
            </p>

            <label>
              Mot de passe actuel
              <input
                type="password"
                autoComplete="current-password"
                required
                value={loginAlertPassword}
                onChange={(event) =>
                  setLoginAlertPassword(event.target.value)
                }
              />
            </label>

            <button
              disabled={
                activeAction !== null ||
                isLoadingLoginAlertPreference
              }
            >
              {activeAction === "loginAlerts"
                ? "Mise à jour…"
                : loginAlertEmailsEnabled
                  ? "Désactiver les e-mails d’alerte"
                  : "Activer les e-mails d’alerte"}
            </button>
          </form>

          <section className="security-action-card security-trust-card">
            <div
              className="security-trust-card__icon"
              aria-hidden="true"
            >
              ✓
            </div>

            <p className="section-heading__eyebrow">
              Confiance
            </p>
            <h2>Badge Profil vérifié</h2>
            <p>
              Envoie un selfie privé pour confirmer que ton visage
              correspond à la photo principale de ton profil.
            </p>

            <Link
              className="security-inline-link"
              to="/profile/verification"
            >
              Consulter mon statut
              <span aria-hidden="true">→</span>
            </Link>
          </section>
        </div>
      </section>

      <section className="security-premium-section">
        <div className="security-premium-section__heading">
          <div>
            <p className="section-heading__eyebrow">
              Accès au compte
            </p>
            <h2>Mot de passe et sessions</h2>
          </div>

          <p>
            Modifie tes identifiants ou ferme toutes les autres sessions.
          </p>
        </div>

        <div className="account-security-grid">
          <form
            className="security-action-card"
            onSubmit={submitPassword}
          >
            <p className="section-heading__eyebrow">
              Mot de passe
            </p>
            <h2>Changer mon mot de passe</h2>
            <p>
              Cette action déconnecte automatiquement tous les autres appareils.
            </p>

            <label>
              Mot de passe actuel
              <input
                type="password"
                autoComplete="current-password"
                value={currentPassword}
                onChange={(event) =>
                  setCurrentPassword(event.target.value)
                }
              />
            </label>

            <div className="security-form-row">
              <label>
                Nouveau mot de passe
                <input
                  type="password"
                  autoComplete="new-password"
                  value={newPassword}
                  onChange={(event) =>
                    setNewPassword(event.target.value)
                  }
                />
              </label>

              <label>
                Confirmation
                <input
                  type="password"
                  autoComplete="new-password"
                  value={newPasswordConfirmation}
                  onChange={(event) =>
                    setNewPasswordConfirmation(
                      event.target.value,
                    )
                  }
                />
              </label>
            </div>

            <button disabled={activeAction !== null}>
              {activeAction === "password"
                ? "Modification…"
                : "Changer le mot de passe"}
            </button>
          </form>

          <form
            className="security-action-card"
            onSubmit={submitSessions}
          >
            <p className="section-heading__eyebrow">
              Appareils
            </p>
            <h2>Fermer les autres sessions</h2>
            <p>
              Ta session actuelle reste ouverte. Tous les autres
              appareils seront immédiatement déconnectés.
            </p>

            <label>
              Mot de passe actuel
              <input
                type="password"
                autoComplete="current-password"
                value={sessionPassword}
                onChange={(event) =>
                  setSessionPassword(event.target.value)
                }
              />
            </label>

            <button disabled={activeAction !== null}>
              {activeAction === "sessions"
                ? "Déconnexion…"
                : "Déconnecter les autres appareils"}
            </button>
          </form>
        </div>
      </section>

      <section className="security-danger-zone">
        <div className="security-danger-zone__intro">
          <p className="section-heading__eyebrow">
            Zone sensible
          </p>
          <h2>Désactivation du compte</h2>
          <p>
            Ton profil disparaîtra et toutes tes sessions seront fermées.
            Cette action demande une confirmation explicite.
          </p>
        </div>

        <form
          className="security-danger-zone__form"
          onSubmit={submitDeactivation}
        >
          <label>
            Mot de passe actuel
            <input
              type="password"
              autoComplete="current-password"
              value={deactivationPassword}
              onChange={(event) =>
                setDeactivationPassword(event.target.value)
              }
            />
          </label>

          <label>
            Écris DESACTIVER
            <input
              type="text"
              autoComplete="off"
              value={confirmation}
              onChange={(event) =>
                setConfirmation(event.target.value)
              }
            />
          </label>

          <button disabled={activeAction !== null}>
            {activeAction === "deactivate"
              ? "Désactivation…"
              : "Désactiver mon compte"}
          </button>
        </form>
      </section>
    </main>
  );
}
