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

import { useState } from "react";
import {
  Link,
  NavLink,
  useNavigate,
} from "react-router-dom";

import { normalizeApiError } from "../../api/apiError";
import { useAuth } from "../../hooks/useAuth";

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

  const [isLoggingOut, setIsLoggingOut] =
    useState(false);

  const [logoutError, setLogoutError] =
    useState<string | null>(null);


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
                  to="/matches"
                >
                  Mes matchs
                </NavLink>

                <NavLink
                  className={getNavigationLinkClass}
                  to="/messages"
                >
                  Messages
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
