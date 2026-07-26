import {
  useCallback,
  useEffect,
  useRef,
  useState,
} from "react";
import {
  Link,
  NavLink,
  useLocation,
  useNavigate,
} from "react-router-dom";

import { normalizeApiError } from "../../api/apiError";
import { getUnreadMessageCount } from "../../api/messagingService";
import { getNotificationUnreadCount } from "../../api/notificationService";
import { useAuth } from "../../hooks/useAuth";
import { useAccountRealtime } from "../../hooks/useAccountRealtime";

import { BrandLogo } from "../common/BrandLogo";

import "./PublicHeader.css";


interface NavigationClassArguments {
  isActive: boolean;
}


function getNavigationLinkClass({
  isActive,
}: NavigationClassArguments): string {
  return isActive
    ? "premium-nav__link premium-nav__link--active"
    : "premium-nav__link";
}


function getMobileNavigationLinkClass({
  isActive,
}: NavigationClassArguments): string {
  return isActive
    ? "premium-mobile-nav__link premium-mobile-nav__link--active"
    : "premium-mobile-nav__link";
}


export function PublicHeader() {
  const navigate = useNavigate();
  const location = useLocation();

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

  const [isLoggingOut, setIsLoggingOut] = useState(false);
  const [logoutError, setLogoutError] =
    useState<string | null>(null);
  const [unreadMessageCount, setUnreadMessageCount] =
    useState(0);
  const [
    unreadNotificationCount,
    setUnreadNotificationCount,
  ] = useState(0);
  const [isMobileMenuOpen, setIsMobileMenuOpen] =
    useState(false);
  const [isAccountMenuOpen, setIsAccountMenuOpen] =
    useState(false);

  const accountMenuRef = useRef<HTMLDivElement | null>(null);

  const accountRoutes = [
    "/discovery-preferences",
    "/profile/edit",
    "/profile/photos",
    "/profile/verification",
    "/premium",
    "/likes-received",
    "/account/privacy",
    "/blocked-users",
    "/reports",
  ];

  const isAccountSectionActive = accountRoutes.some(
    (route) => location.pathname.startsWith(route),
  );

  useEffect(() => {
    setIsMobileMenuOpen(false);
    setIsAccountMenuOpen(false);
  }, [location.pathname]);

  useEffect(() => {
    function closeAccountMenuOnOutsideClick(
      event: MouseEvent,
    ): void {
      if (
        accountMenuRef.current &&
        !accountMenuRef.current.contains(event.target as Node)
      ) {
        setIsAccountMenuOpen(false);
      }
    }

    function closeMenusOnEscape(event: KeyboardEvent): void {
      if (event.key === "Escape") {
        setIsAccountMenuOpen(false);
        setIsMobileMenuOpen(false);
      }
    }

    document.addEventListener(
      "mousedown",
      closeAccountMenuOnOutsideClick,
    );
    document.addEventListener(
      "keydown",
      closeMenusOnEscape,
    );

    return () => {
      document.removeEventListener(
        "mousedown",
        closeAccountMenuOnOutsideClick,
      );
      document.removeEventListener(
        "keydown",
        closeMenusOnEscape,
      );
    };
  }, []);

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
        // Le compteur ne doit jamais bloquer l'en-tête.
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
        // Le compteur ne doit jamais bloquer l'en-tête.
      }
    }, [isAuthenticated]);

  useEffect(() => {
    if (isInitializing || !isAuthenticated) {
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
        handleCounterRefresh();
      }
    }

    window.addEventListener("focus", handleCounterRefresh);
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
    accountRealtimeState,
    isAuthenticated,
    isInitializing,
    loadUnreadMessageCount,
    loadUnreadNotificationCount,
  ]);

  async function handleLogout(): Promise<void> {
    if (isLoggingOut) {
      return;
    }

    setIsLoggingOut(true);
    setLogoutError(null);

    try {
      await logout();
      navigate("/", { replace: true });
    } catch (error: unknown) {
      setLogoutError(
        normalizeApiError(error).message,
      );
    } finally {
      setIsLoggingOut(false);
    }
  }

  function renderUnreadBadge(
    count: number,
    singularLabel: string,
  ) {
    if (count <= 0) {
      return null;
    }

    return (
      <span
        className="premium-nav__badge"
        aria-label={`${count} ${singularLabel}${count > 1 ? "s" : ""} non lu${count > 1 ? "s" : ""}`}
      >
        {count > 99 ? "99+" : count}
      </span>
    );
  }

  return (
    <>
      <header className="premium-header">
        <div className="premium-header__inner">
          <div className="premium-header__brand">
            <BrandLogo />
          </div>

          <button
            type="button"
            className="premium-header__mobile-toggle"
            aria-expanded={isMobileMenuOpen}
            aria-controls="mbolo-mobile-navigation"
            aria-label={
              isMobileMenuOpen
                ? "Fermer le menu"
                : "Ouvrir le menu"
            }
            onClick={() => {
              setIsMobileMenuOpen((current) => !current);
            }}
          >
            <span aria-hidden="true" />
            <span aria-hidden="true" />
            <span aria-hidden="true" />
          </button>

          <nav
            className="premium-nav"
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
                  to="/matches"
                >
                  Mes matchs
                </NavLink>
                <NavLink
                  className={getNavigationLinkClass}
                  to="/messages"
                >
                  <span>Messages</span>
                  {renderUnreadBadge(
                    unreadMessageCount,
                    "message",
                  )}
                </NavLink>
                <NavLink
                  className={getNavigationLinkClass}
                  to="/notifications"
                >
                  <span>Notifications</span>
                  {renderUnreadBadge(
                    unreadNotificationCount,
                    "notification",
                  )}
                </NavLink>
                <NavLink
                  className={getNavigationLinkClass}
                  to="/safety"
                >
                  Sécurité
                </NavLink>

                <div
                  className="premium-account-menu"
                  ref={accountMenuRef}
                >
                  <button
                    type="button"
                    className={[
                      "premium-account-menu__trigger",
                      isAccountSectionActive
                        ? "premium-account-menu__trigger--active"
                        : "",
                    ].join(" ")}
                    aria-expanded={isAccountMenuOpen}
                    aria-haspopup="menu"
                    onClick={() => {
                      setIsAccountMenuOpen(
                        (current) => !current,
                      );
                    }}
                  >
                    Mon espace
                    <span
                      className="premium-account-menu__chevron"
                      aria-hidden="true"
                    >
                      ▾
                    </span>
                  </button>

                  {isAccountMenuOpen ? (
                    <div
                      className="premium-account-menu__panel"
                      role="menu"
                    >
                      <div className="premium-account-menu__heading">
                        <span>Personnaliser</span>
                        <small>Profil et préférences</small>
                      </div>

                      <NavLink to="/profile/edit" role="menuitem">
                        Mon profil
                      </NavLink>
                      <NavLink to="/profile/photos" role="menuitem">
                        Mes photos
                      </NavLink>
                      <NavLink
                        to="/profile/verification"
                        role="menuitem"
                      >
                        Vérification
                      </NavLink>
                      <NavLink
                        to="/discovery-preferences"
                        role="menuitem"
                      >
                        Préférences
                      </NavLink>
                      <NavLink to="/premium" role="menuitem">
                        Premium
                      </NavLink>
                      <NavLink
                        to="/likes-received"
                        role="menuitem"
                      >
                        Qui m’a liké
                      </NavLink>

                      <div className="premium-account-menu__separator" />

                      <NavLink
                        to="/account/privacy"
                        role="menuitem"
                      >
                        Confidentialité
                      </NavLink>
                      <NavLink
                        to="/blocked-users"
                        role="menuitem"
                      >
                        Utilisateurs bloqués
                      </NavLink>
                      <NavLink to="/reports" role="menuitem">
                        Mes signalements
                      </NavLink>
                    </div>
                  ) : null}
                </div>
              </>
            ) : (
              <NavLink
                className={getNavigationLinkClass}
                to="/safety"
              >
                Sécurité
              </NavLink>
            )}
          </nav>

          <div className="premium-header__actions">
            {isInitializing ? (
              <span
                className="premium-header__loading"
                role="status"
              >
                Vérification…
              </span>
            ) : isAuthenticated && user ? (
              <div className="premium-header__session">
                <div
                  className="premium-header__avatar"
                  aria-hidden="true"
                >
                  {user.email.charAt(0).toUpperCase()}
                </div>
                <div className="premium-header__identity">
                  <small>Compte connecté</small>
                  <span title={user.email}>
                    {user.email}
                  </span>
                </div>
                <button
                  type="button"
                  className="premium-header__logout"
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
              <div className="premium-header__anonymous-actions">
                <Link
                  className="premium-header__login"
                  to="/login"
                >
                  Se connecter
                </Link>
                <Link
                  className="premium-header__register"
                  to="/register"
                >
                  Créer un compte
                </Link>
              </div>
            )}
          </div>
        </div>

        <nav
          id="mbolo-mobile-navigation"
          className={[
            "premium-mobile-nav",
            isMobileMenuOpen
              ? "premium-mobile-nav--open"
              : "",
          ].join(" ")}
          aria-label="Navigation mobile"
        >
          <NavLink
            className={getMobileNavigationLinkClass}
            to="/"
            end
          >
            Accueil
          </NavLink>

          {isAuthenticated ? (
            <>
              <NavLink
                className={getMobileNavigationLinkClass}
                to="/discovery"
              >
                Découvrir
              </NavLink>
              <NavLink
                className={getMobileNavigationLinkClass}
                to="/matches"
              >
                Mes matchs
              </NavLink>
              <NavLink
                className={getMobileNavigationLinkClass}
                to="/messages"
              >
                Messages
                {renderUnreadBadge(
                  unreadMessageCount,
                  "message",
                )}
              </NavLink>
              <NavLink
                className={getMobileNavigationLinkClass}
                to="/notifications"
              >
                Notifications
                {renderUnreadBadge(
                  unreadNotificationCount,
                  "notification",
                )}
              </NavLink>
              <NavLink
                className={getMobileNavigationLinkClass}
                to="/safety"
              >
                Sécurité
              </NavLink>

              <p className="premium-mobile-nav__section-label">
                Mon espace
              </p>

              <NavLink
                className={getMobileNavigationLinkClass}
                to="/profile/edit"
              >
                Mon profil
              </NavLink>
              <NavLink
                className={getMobileNavigationLinkClass}
                to="/profile/photos"
              >
                Mes photos
              </NavLink>
              <NavLink
                className={getMobileNavigationLinkClass}
                to="/discovery-preferences"
              >
                Préférences
              </NavLink>
              <NavLink
                className={getMobileNavigationLinkClass}
                to="/premium"
              >
                Premium
              </NavLink>
              <NavLink
                className={getMobileNavigationLinkClass}
                to="/likes-received"
              >
                Qui m’a liké
              </NavLink>
              <NavLink
                className={getMobileNavigationLinkClass}
                to="/account/privacy"
              >
                Confidentialité
              </NavLink>

              <button
                type="button"
                className="premium-mobile-nav__logout"
                disabled={isLoggingOut}
                onClick={() => {
                  void handleLogout();
                }}
              >
                {isLoggingOut
                  ? "Déconnexion…"
                  : "Se déconnecter"}
              </button>
            </>
          ) : (
            <>
              <NavLink
                className={getMobileNavigationLinkClass}
                to="/safety"
              >
                Sécurité
              </NavLink>
              <NavLink
                className={getMobileNavigationLinkClass}
                to="/login"
              >
                Se connecter
              </NavLink>
              <NavLink
                className={getMobileNavigationLinkClass}
                to="/register"
              >
                Créer un compte
              </NavLink>
            </>
          )}
        </nav>
      </header>

      {logoutError ? (
        <div className="global-session-alert" role="alert">
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
