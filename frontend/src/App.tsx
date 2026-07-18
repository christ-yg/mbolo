/**
 * Composant racine du frontend Mbolo.
 *
 * L'ordre des fournisseurs est important :
 *
 * AuthProvider
 *     ↓
 * RouterProvider
 *
 * Toutes les pages du routeur peuvent ainsi accéder
 * au contexte global d'authentification.
 */

import { RouterProvider } from "react-router-dom";

import { AuthProvider } from "./context/AuthContext";
import { appRouter } from "./routes/AppRouter";

export default function App() {
  return (
    <AuthProvider>
      <RouterProvider router={appRouter} />
    </AuthProvider>
  );
}
