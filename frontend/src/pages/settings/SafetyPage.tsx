/**
 * Page de sécurité et de confidentialité Mbolo.
 *
 * Cette page présente les principales protections du service
 * et permet à l'utilisateur de contrôler les notifications
 * natives de messages.
 */

import {
  useMemo,
  useState,
} from "react";
import { Link } from "react-router-dom";

import {
  type BrowserNotificationPermission,
  useNotification,
} from "../../context/NotificationContext";

function getPermissionExplanation(
  permission: BrowserNotificationPermission,
): string {
  switch (permission) {
    case "granted":
      return (
        "Le navigateur autorise Mbolo à afficher des notifications."
      );

    case "denied":
      return (
        "Le navigateur a bloqué cette autorisation. " +
        "Tu dois la réactiver depuis les paramètres du site."
      );

    case "default":
      return (
        "Aucune décision n’a encore été enregistrée par le navigateur."
      );

    case "unsupported":
      return (
        "Ce navigateur ne prend pas en charge les notifications natives."
      );
  }
}

export function SafetyPage() {
  const {
    browserNotificationsSupported,
    browserNotificationPermission,
    browserNotificationsEnabled,
    enableBrowserNotifications,
    disableBrowserNotifications,
  } = useNotification();

  const [
    isUpdatingNotifications,
    setIsUpdatingNotifications,
  ] = useState(false);

  const [
    notificationFeedback,
    setNotificationFeedback,
  ] = useState<string | null>(null);

  const permissionExplanation =
    useMemo(
      () =>
        getPermissionExplanation(
          browserNotificationPermission,
        ),
      [browserNotificationPermission],
    );

  async function handleEnableNotifications():
  Promise<void> {
    if (isUpdatingNotifications) {
      return;
    }

    setIsUpdatingNotifications(true);
    setNotificationFeedback(null);

    const enabled =
      await enableBrowserNotifications();

    setNotificationFeedback(
      enabled
        ? (
            "Les notifications de messages sont maintenant activées."
          )
        : browserNotificationPermission === "denied"
          ? (
              "L’autorisation reste bloquée dans les paramètres du navigateur."
            )
          : (
              "Les notifications n’ont pas été autorisées."
            ),
    );

    setIsUpdatingNotifications(false);
  }

  function handleDisableNotifications(): void {
    disableBrowserNotifications();

    setNotificationFeedback(
      "Les notifications de messages sont désactivées dans Mbolo.",
    );
  }

  return (
    <main className="safety-page">
      <section className="safety-page__hero">
        <p className="section-heading__eyebrow">
          Sécurité et confiance
        </p>

        <h1>
          La protection des utilisateurs commence dès la conception.
        </h1>

        <p>
          Mbolo utilise des sessions sécurisées, une protection
          CSRF, une limitation anti-abus, une validation stricte
          des données, une isolation des profils et un traitement
          contrôlé des images.
        </p>
      </section>

      <section
        className="safety-settings"
        aria-labelledby="notification-settings-title"
      >
        <div className="safety-settings__content">
          <span
            className="safety-settings__icon"
            aria-hidden="true"
          >
            🔔
          </span>

          <div>
            <p className="safety-settings__eyebrow">
              Préférence locale
            </p>

            <h2 id="notification-settings-title">
              Notifications de nouveaux messages
            </h2>

            <p>
              Mbolo peut t’avertir lorsqu’un nouveau message
              arrive pendant que l’onglet est en arrière-plan.
              Le contenu privé du message n’est jamais affiché
              dans la notification système.
            </p>

            <div className="safety-settings__privacy-note">
              <strong>Confidentialité :</strong>
              <span>
                la notification indique seulement le nom public
                de l’expéditeur et l’existence d’un nouveau message.
              </span>
            </div>
          </div>
        </div>

        <div className="safety-settings__control">
          <div
            className={
              browserNotificationsEnabled
                ? (
                    "safety-settings__status " +
                    "safety-settings__status--enabled"
                  )
                : "safety-settings__status"
            }
          >
            <span aria-hidden="true" />

            <strong>
              {browserNotificationsEnabled
                ? "Activées"
                : "Désactivées"}
            </strong>
          </div>

          <p>{permissionExplanation}</p>

          {!browserNotificationsSupported ? (
            <button
              type="button"
              className="safety-settings__button"
              disabled
            >
              Fonction indisponible
            </button>
          ) : browserNotificationsEnabled ? (
            <button
              type="button"
              className={
                "safety-settings__button " +
                "safety-settings__button--secondary"
              }
              onClick={handleDisableNotifications}
            >
              Désactiver dans Mbolo
            </button>
          ) : (
            <button
              type="button"
              className="safety-settings__button"
              disabled={
                isUpdatingNotifications ||
                browserNotificationPermission === "denied"
              }
              onClick={() => {
                void handleEnableNotifications();
              }}
            >
              {isUpdatingNotifications
                ? "Demande en cours…"
                : browserNotificationPermission === "denied"
                  ? "Autorisation bloquée"
                  : "Activer les notifications"}
            </button>
          )}

          {notificationFeedback ? (
            <p
              className="safety-settings__feedback"
              role="status"
            >
              {notificationFeedback}
            </p>
          ) : null}
        </div>
      </section>

      <section className="safety-account-controls">
        <div>
          <p className="safety-settings__eyebrow">
            Contrôle du compte
          </p>
          <h2>Profils bloqués</h2>
          <p>
            Consulte les profils bloqués et retire un blocage
            lorsque tu le souhaites.
          </p>
        </div>
        <Link to="/blocked-users">
          Gérer les profils bloqués
        </Link>
      </section>

      <section className="safety-principles">
        <article>
          <span aria-hidden="true">01</span>
          <h2>Contrôle des accès</h2>
          <p>
            Chaque conversation est limitée aux deux participants
            d’un match actif et vérifiée côté serveur.
          </p>
        </article>

        <article>
          <span aria-hidden="true">02</span>
          <h2>Données minimales</h2>
          <p>
            Les interfaces exposent seulement les données nécessaires
            au fonctionnement de chaque fonctionnalité.
          </p>
        </article>

        <article>
          <span aria-hidden="true">03</span>
          <h2>Choix de l’utilisateur</h2>
          <p>
            Les notifications natives restent facultatives et peuvent
            être désactivées sans interrompre la messagerie.
          </p>
        </article>
      </section>
    </main>
  );
}
