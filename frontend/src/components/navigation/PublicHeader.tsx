/**
 * En-tête principal de l'application Mbolo.
 *
 * Le contenu de la navigation dépend de la session Django :
 *
 * Utilisateur anonyme :
 *
 * - Accueil ;
 * - Sécurité ;
 * - Se connecter ;
 * - Créer un compte.
 *
 * Utilisateur authentifié :
 *
 * - Accueil ;
 * - Découvrir ;
 * - Mes matchs ;
 * - Messages ;
 * - Sécurité ;
 * - identité du compte ;
 * - bouton de déconnexion.
 */

import {
  useCallback,
  useEffect,
  useState,
} from "react";
import {
  Link,
  NavLink,
  useNavigate,
} from "react-router-dom";

import { normalizeApiError } from "../../api/apiError";
import { getUnreadMessageCount } from "../../api/messagingService";
import { getNotificationUnreadCount } from "../../api/notificationService";
import { useAuth } from "../../hooks/useAuth";
import { useAccountRealtime } from "../../hooks/useAccountRealtime";

import { BrandLogo } from "../common/BrandLogo";


/**
 * Retourne la classe CSS d'un lien de navigation.
 *
 * React Router transmet automatiquement `isActive`
 * selon l'adresse actuellement affichée.
 */
function getNavigationLinkClass({
  isActive,
}: {
  isActive: boolean;
}): string {
  return isActive
    ? "public-header__nav-link public-header__nav-link--active"
    : "public-header__nav-link";
}


/**
 * En-tête global de Mbolo.
 */
export function PublicHeader() {
  const navigate = useNavigate();

  const {
    user,
    isAuthenticated,
    isInitializing,
    logout,
  } = useAuth();

  const {
    state: accountRealtimeState,
    unreadCount: realtimeUnreadCount,
    notificationUnreadCount:
      realtimeNotificationUnreadCount,
  } = useAccountRealtime();

  const [isLoggingOut, setIsLoggingOut] =
    useState(false);

  const [logoutError, setLogoutError] =
    useState<string | null>(null);

  const [unreadMessageCount, setUnreadMessageCount] =
    useState(0);

  const [
    unreadNotificationCount,
    setUnreadNotificationCount,
  ] = useState(0);

  useEffect(() => {
    if (accountRealtimeState === "open") {
      setUnreadMessageCount(realtimeUnreadCount);
      setUnreadNotificationCount(
        realtimeNotificationUnreadCount,
      );
    }
  }, [
    accountRealtimeState,
    realtimeNotificationUnreadCount,
    realtimeUnreadCount,
  ]);

  const loadUnreadMessageCount =
    useCallback(async (): Promise<void> => {
      if (!isAuthenticated) {
        setUnreadMessageCount(0);
        return;
      }

      try {
        const result = await getUnreadMessageCount();

        setUnreadMessageCount(
          Math.max(0, result.unread_count),
        );
      } catch {
        /**
         * Le compteur ne doit jamais bloquer la navigation.
         *
         * Une panne momentanée du compteur reste donc silencieuse.
         */
      }
    }, [isAuthenticated]);


  const loadUnreadNotificationCount =
    useCallback(async (): Promise<void> => {
      if (!isAuthenticated) {
        setUnreadNotificationCount(0);
        return;
      }

      try {
        const result =
          await getNotificationUnreadCount();

        setUnreadNotificationCount(
          Math.max(0, result.unread_count),
        );
      } catch {
        /**
         * Le centre de notifications ne doit jamais bloquer
         * l'affichage de l'en-tête.
         */
      }
    }, [isAuthenticated]);

  useEffect(() => {
    if (
      isInitializing ||
      !isAuthenticated
    ) {
      setUnreadMessageCount(0);
      setUnreadNotificationCount(0);
      return undefined;
    }

    void loadUnreadMessageCount();
    void loadUnreadNotificationCount();

    const intervalIdentifier =
      window.setInterval(() => {
        if (accountRealtimeState !== "open") {
          void loadUnreadMessageCount();
          void loadUnreadNotificationCount();
        }
      }, 60000);

    function handleCounterRefresh(): void {
      void loadUnreadMessageCount();
      void loadUnreadNotificationCount();
    }

    function handleVisibilityChange(): void {
      if (document.visibilityState === "visible") {
        void loadUnreadMessageCount();
      }
    }

    window.addEventListener(
      "focus",
      handleCounterRefresh,
    );
    window.addEventListener(
      "mbolo:unread-count-changed",
      handleCounterRefresh,
    );
    document.addEventListener(
      "visibilitychange",
      handleVisibilityChange,
    );

    return () => {
      window.clearInterval(intervalIdentifier);
      window.removeEventListener(
        "focus",
        handleCounterRefresh,
      );
      window.removeEventListener(
        "mbolo:unread-count-changed",
        handleCounterRefresh,
      );
      document.removeEventListener(
        "visibilitychange",
        handleVisibilityChange,
      );
    };
  }, [
    isAuthenticated,
    isInitializing,
    loadUnreadMessageCount,
    loadUnreadNotificationCount,
    accountRealtimeState,
  ]);


  /**
   * Ferme la session Django puis redirige vers l'accueil.
   */
  async function handleLogout(): Promise<void> {
    if (isLoggingOut) {
      return;
    }

    setIsLoggingOut(true);
    setLogoutError(null);

    try {
      await logout();

      navigate("/", {
        replace: true,
      });
    } catch (error: unknown) {
      const normalizedError =
        normalizeApiError(error);

      setLogoutError(normalizedError.message);
    } finally {
      setIsLoggingOut(false);
    }
  }


  return (
    <>
      <header className="public-header">
        <div className="public-header__inner">
          <BrandLogo />

          <nav
            className="public-header__navigation"
            aria-label="Navigation principale"
          >
            <NavLink
              className={getNavigationLinkClass}
              to="/"
              end
            >
              Accueil
            </NavLink>

            {isAuthenticated ? (
              <>
                <NavLink
                  className={getNavigationLinkClass}
                  to="/discovery"
                >
                  Découvrir
                </NavLink>

                <NavLink
                  className={getNavigationLinkClass}
                  to="/discovery-preferences"
                >
                  Préférences
                </NavLink>

                <NavLink
                  className={getNavigationLinkClass}
                  to="/matches"
                >
                  Mes matchs
                </NavLink>


                <NavLink
                  className={getNavigationLinkClass}
                  to="/likes-received"
                >
                  Qui m’a liké
                </NavLink>

                <NavLink
                  className={getNavigationLinkClass}
                  to="/messages"
                >
                  <span>Messages</span>

                  {unreadMessageCount > 0 ? (
                    <span
                      className="public-header__unread-badge"
                      aria-label={`${unreadMessageCount} message${unreadMessageCount > 1 ? "s" : ""} non lu${unreadMessageCount > 1 ? "s" : ""}`}
                    >
                      {unreadMessageCount > 99
                        ? "99+"
                        : unreadMessageCount}
                    </span>
                  ) : null}
                </NavLink>


                <NavLink
                  className={getNavigationLinkClass}
                  to="/notifications"
                >
                  <span>Notifications</span>

                  {unreadNotificationCount > 0 ? (
                    <span
                      className="public-header__unread-badge"
                      aria-label={`${unreadNotificationCount} notification${unreadNotificationCount > 1 ? "s" : ""} non lue${unreadNotificationCount > 1 ? "s" : ""}`}
                    >
                      {unreadNotificationCount > 99
                        ? "99+"
                        : unreadNotificationCount}
                    </span>
                  ) : null}
                </NavLink>
              </>
            ) : null}

            <NavLink
              className={getNavigationLinkClass}
              to="/safety"
            >
              Sécurité
            </NavLink>
          </nav>

          <div className="public-header__actions">
            {isInitializing ? (
              /**
               * Pendant GET /auth/me/, nous évitons
               * d'afficher brièvement les mauvais boutons.
               */
              <span
                className="public-header__session-loading"
                role="status"
              >
                Vérification…
              </span>
            ) : isAuthenticated && user ? (
              <div className="public-header__account">
                <div className="public-header__identity">
                  <span
                    className="public-header__avatar"
                    aria-hidden="true"
                  >
                    {user.email
                      .charAt(0)
                      .toUpperCase()}
                  </span>

                  <div className="public-header__identity-text">
                    <small>Compte connecté</small>

                    <span title={user.email}>
                      {user.email}
                    </span>
                  </div>
                </div>

                <button
                  type="button"
                  className="public-header__logout-button"
                  disabled={isLoggingOut}
                  onClick={() => {
                    void handleLogout();
                  }}
                >
                  {isLoggingOut
                    ? "Déconnexion…"
                    : "Se déconnecter"}
                </button>
              </div>
            ) : (
              <>
                <Link
                  className="public-header__login-link"
                  to="/login"
                >
                  Se connecter
                </Link>

                <Link
                  className="public-header__register-link"
                  to="/register"
                >
                  Créer un compte
                </Link>
              </>
            )}
          </div>
        </div>
      </header>

      {logoutError ? (
        <div
          className="global-session-alert"
          role="alert"
        >
          <span aria-hidden="true">!</span>

          <p>{logoutError}</p>

          <button
            type="button"
            aria-label="Fermer le message"
            onClick={() => {
              setLogoutError(null);
            }}
          >
            ×
          </button>
        </div>
      ) : null}
    </>
  );
}
