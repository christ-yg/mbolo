/**
 * Protection des routes privées Mbolo.
 *
 * Ce composant empêche un visiteur anonyme d'accéder
 * aux pages nécessitant une session Django valide.
 */

import type { PropsWithChildren } from "react";
import {
  Navigate,
  useLocation,
} from "react-router-dom";

import { useAuth } from "../../hooks/useAuth";

/**
 * État transmis à la page de connexion.
 *
 * Il permettra plus tard de revenir automatiquement
 * vers la page initialement demandée.
 */
interface LoginRedirectState {
  from: string;
}

export function ProtectedRoute({
  children,
}: PropsWithChildren) {
  const location = useLocation();

  const {
    isAuthenticated,
    isInitializing,
  } = useAuth();

  /**
   * Tant que /auth/me/ n'a pas répondu, nous ne devons
   * ni afficher la page privée ni rediriger trop tôt.
   */
  if (isInitializing) {
    return (
      <main className="auth-loading-page">
        <section
          className="auth-loading-card"
          role="status"
          aria-live="polite"
        >
          <div
            className="auth-loading-card__spinner"
            aria-hidden="true"
          />

          <p>Vérification sécurisée de ta session…</p>
        </section>
      </main>
    );
  }

  /**
   * Aucune session valide :
   * redirection vers la page de connexion.
   */
  if (!isAuthenticated) {
    const redirectState: LoginRedirectState = {
      from: `${location.pathname}${location.search}`,
    };

    return (
      <Navigate
        to="/login"
        replace
        state={redirectState}
      />
    );
  }

  /**
   * Session valide :
   * affichage de la page privée.
   */
  return children;
}
