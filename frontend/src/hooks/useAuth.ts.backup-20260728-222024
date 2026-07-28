/**
 * Hook d'accès au contexte d'authentification Mbolo.
 *
 * Au lieu d'importer directement AuthContext dans chaque composant,
 * nous utilisons :
 *
 *     const { user, login, logout } = useAuth();
 */

import { useContext } from "react";

import {
  AuthContext,
  type AuthContextValue,
} from "../context/AuthContext";

/**
 * Retourne le contexte global d'authentification.
 *
 * Une erreur explicite est déclenchée si le hook est utilisé
 * en dehors du AuthProvider.
 */
export function useAuth(): AuthContextValue {
  const context = useContext(AuthContext);

  if (context === undefined) {
    throw new Error(
      "useAuth doit être utilisé à l'intérieur du composant AuthProvider.",
    );
  }

  return context;
}
