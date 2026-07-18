/**
 * En-tête principal de l'application Mbolo.
 *
 * L'en-tête adapte automatiquement son contenu selon
 * l'état de la session Django :
 *
 * Utilisateur anonyme :
 *
 * - lien vers la connexion ;
 * - lien vers l'inscription.
 *
 * Utilisateur authentifié :
 *
 * - lien vers la découverte ;
 * - lien vers la sécurité ;
 * - affichage de l'adresse e-mail ;
 * - bouton de déconnexion.
 *
 * La véritable session reste gérée par Django.
 * React affiche uniquement l'état fourni par AuthContext.
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
 * NavLink fournit automatiquement isActive selon
 * l'URL actuellement affichée.
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

export function PublicHeader() {
  const navigate = useNavigate();

  /**
   * État global de l'authentification.
   */
  const {
    user,
    isAuthenticated,
    isInitializing,
    logout,
  } = useAuth();

  /**
   * Empêche plusieurs clics pendant la déconnexion.
   */
  const [isLoggingOut, setIsLoggingOut] =
    useState(false);

  /**
   * Message affiché lorsqu'une déconnexion échoue.
   */
  const [logoutError, setLogoutError] =
    useState<string | null>(null);

  /**
   * Ferme réellement la session Django.
   *
   * Étapes :
   *
   * 1. récupération du jeton CSRF par authService ;
   * 2. POST vers /api/v1/auth/logout/ ;
   * 3. destruction de la session côté Django ;
   * 4. suppression de l'utilisateur dans AuthContext ;
   * 5. redirection vers la page d'accueil.
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

      setLogoutError(
        normalizedError.message,
      );
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
              <NavLink
                className={getNavigationLinkClass}
                to="/discovery"
              >
                Découvrir
              </NavLink>
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
