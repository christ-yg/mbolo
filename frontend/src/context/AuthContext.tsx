/**
 * Contexte global d'authentification Mbolo.
 *
 * Ce fichier centralise l'état de la session pour toute
 * l'application React.
 *
 * Il permet notamment de savoir :
 *
 * - si l'utilisateur est connecté ;
 * - quel compte est connecté ;
 * - si la vérification initiale est terminée ;
 * - comment ouvrir une session ;
 * - comment fermer une session ;
 * - comment recharger les données utilisateur.
 *
 * La session réelle reste gérée par Django dans un cookie.
 * React ne stocke jamais le mot de passe ni l'identifiant
 * de session dans localStorage.
 */

import {
  createContext,
  type PropsWithChildren,
  useCallback,
  useEffect,
  useMemo,
  useState,
} from "react";

import { normalizeApiError } from "../api/apiError";
import { accountRealtimeHub } from "../api/accountRealtime";
import {
  getCurrentUser,
  confirmEmailTwoFactor,
  loginUser,
  logoutUser,
  sendActivityHeartbeat,
} from "../api/authService";

import type {
  AuthenticatedUser,
  EmailTwoFactorConfirmPayload,
  LoginPayload,
  LoginResult,
} from "../types/auth";

/**
 * Structure complète exposée aux composants React.
 */
export interface AuthContextValue {
  /**
   * Utilisateur actuellement connecté.
   *
   * null signifie qu'aucune session authentifiée
   * n'est actuellement disponible.
   */
  user: AuthenticatedUser | null;

  /**
   * Vrai pendant la vérification initiale de la session.
   */
  isInitializing: boolean;

  /**
   * Raccourci pratique dérivé de user.
   */
  isAuthenticated: boolean;

  /**
   * Ouvre une session Django.
   */
  login: (
    payload: LoginPayload,
  ) => Promise<LoginResult>;

  confirmTwoFactor: (
    payload: EmailTwoFactorConfirmPayload,
  ) => Promise<AuthenticatedUser>;

  /**
   * Ferme la session Django.
   */
  logout: () => Promise<void>;

  /**
   * Recharge l'utilisateur courant depuis le backend.
   */
  refreshCurrentUser: () => Promise<AuthenticatedUser | null>;
}

/**
 * Le contexte commence avec undefined.
 *
 * Cela permet au hook useAuth de détecter une utilisation
 * accidentelle en dehors du AuthProvider.
 */
export const AuthContext =
  createContext<AuthContextValue | undefined>(undefined);

/**
 * Fournisseur global d'authentification.
 *
 * Il doit entourer le routeur principal de l'application.
 */
export function AuthProvider({
  children,
}: PropsWithChildren) {
  /**
   * Compte associé à la session courante.
   */
  const [user, setUser] =
    useState<AuthenticatedUser | null>(null);

  /**
   * Pendant l'initialisation, nous ne savons pas encore
   * si une session Django existe.
   */
  const [isInitializing, setIsInitializing] =
    useState(true);

  /**
   * Recharge la session courante depuis Django.
   *
   * Les réponses 401 et 403 signifient ici simplement :
   *
   * - aucune session active ;
   * - utilisateur anonyme.
   *
   * Nous ne les traitons pas comme des erreurs critiques
   * au démarrage de l'application.
   */
  const refreshCurrentUser =
    useCallback(async (): Promise<AuthenticatedUser | null> => {
      try {
        const currentUser = await getCurrentUser();

        setUser(currentUser);

        return currentUser;
      } catch (error: unknown) {
        const normalizedError = normalizeApiError(error);

        if (
          normalizedError.status === 401 ||
          normalizedError.status === 403
        ) {
          setUser(null);

          return null;
        }

        /**
         * En cas de panne réseau ou d'erreur serveur,
         * nous évitons de conserver un ancien utilisateur
         * potentiellement invalide.
         */
        setUser(null);

        throw error;
      }
    }, []);

  /**
   * Vérification automatique au premier affichage.
   */
  useEffect(() => {
    let isComponentMounted = true;

    async function initializeAuthentication(): Promise<void> {
      try {
        await refreshCurrentUser();
      } catch {
        /**
         * L'application reste utilisable en mode anonyme.
         *
         * Les erreurs réseau seront affichées lors des actions
         * nécessitant réellement le backend.
         */
      } finally {
        if (isComponentMounted) {
          setIsInitializing(false);
        }
      }
    }

    void initializeAuthentication();

    /**
     * Empêche une mise à jour d'état si le fournisseur
     * est démonté avant la fin de la requête.
     */
    return () => {
      isComponentMounted = false;
    };
  }, [refreshCurrentUser]);

  /**
   * Canal temps réel global du compte.
   *
   * Il est ouvert uniquement après authentification et fermé dès que
   * la session disparaît. L'identité réelle vient du cookie Django :
   * aucun UUID utilisateur n'est transmis dans l'URL WebSocket.
   */
  useEffect(() => {
    if (user === null) {
      accountRealtimeHub.stop();
      return undefined;
    }

    accountRealtimeHub.start(user.id);

    return () => {
      accountRealtimeHub.stop();
    };
  }, [user]);

  /**
   * Battement de présence.
   *
   * Une requête est envoyée au chargement, au retour sur l’onglet
   * et toutes les 60 secondes pendant une session active.
   */
  useEffect(() => {
    if (user === null) {
      return undefined;
    }

    const sendHeartbeat = (): void => {
      if (document.visibilityState === "visible") {
        void sendActivityHeartbeat().catch(() => {
          // La présence ne doit jamais bloquer l’application.
        });
      }
    };

    sendHeartbeat();

    const intervalIdentifier = window.setInterval(
      sendHeartbeat,
      60_000,
    );

    window.addEventListener("focus", sendHeartbeat);
    document.addEventListener("visibilitychange", sendHeartbeat);

    return () => {
      window.clearInterval(intervalIdentifier);
      window.removeEventListener("focus", sendHeartbeat);
      document.removeEventListener("visibilitychange", sendHeartbeat);
    };
  }, [user]);

  /**
   * Connexion centralisée.
   *
   * Après le succès de Django, l'utilisateur est immédiatement
   * enregistré dans le contexte React.
   */
  const login = useCallback(
    async (
      payload: LoginPayload,
    ): Promise<LoginResult> => {
      const result = await loginUser(payload);
      if (!result.requiresTwoFactor) {
        setUser(result.user);
      }
      return result;
    },
    [],
  );

  const confirmTwoFactor = useCallback(
    async (
      payload: EmailTwoFactorConfirmPayload,
    ): Promise<AuthenticatedUser> => {
      const authenticatedUser =
        await confirmEmailTwoFactor(payload);
      setUser(authenticatedUser);
      return authenticatedUser;
    },
    [],
  );

  /**
   * Déconnexion centralisée.
   *
   * Nous supprimons l'utilisateur local uniquement après
   * la réponse du backend.
   */
  const logout = useCallback(async (): Promise<void> => {
    await logoutUser();

    setUser(null);
  }, []);

  /**
   * useMemo évite de recréer inutilement l'objet de contexte
   * à chaque rendu.
   */
  const contextValue = useMemo<AuthContextValue>(
    () => ({
      user,
      isInitializing,
      isAuthenticated: user !== null,
      login,
      confirmTwoFactor,
      logout,
      refreshCurrentUser,
    }),
    [
      user,
      isInitializing,
      login,
      confirmTwoFactor,
      logout,
      refreshCurrentUser,
    ],
  );

  return (
    <AuthContext.Provider value={contextValue}>
      {children}
    </AuthContext.Provider>
  );
}
