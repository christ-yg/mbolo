/**
 * Routeur principal de Mbolo.
 *
 * Les routes publiques restent accessibles à tous.
 * Les routes privées sont entourées par ProtectedRoute.
 */

import { createBrowserRouter } from "react-router-dom";

import { ProtectedRoute } from "../components/auth/ProtectedRoute";
import { PublicLayout } from "../layouts/PublicLayout";
import { LoginPage } from "../pages/auth/LoginPage";
import { RegisterPage } from "../pages/auth/RegisterPage";
import { VerifyEmailPage } from "../pages/auth/VerifyEmailPage";
import { DiscoveryPage } from "../pages/discovery/DiscoveryPage";
import { HomePage } from "../pages/home/HomePage";
import { MatchesPage } from "../pages/matches/MatchesPage";
import { NotFoundPage } from "../pages/NotFoundPage";
import { SafetyPage } from "../pages/settings/SafetyPage";

export const appRouter = createBrowserRouter([
  {
    element: <PublicLayout />,

    children: [
      /**
       * Routes publiques.
       */
      {
        path: "/",
        element: <HomePage />,
      },
      {
        path: "/login",
        element: <LoginPage />,
      },
      {
        path: "/register",
        element: <RegisterPage />,
      },
      {
        path: "/verify-email",
        element: <VerifyEmailPage />,
      },
      {
        path: "/safety",
        element: <SafetyPage />,
      },

      /**
       * Route privée.
       *
       * Un visiteur sans session est redirigé vers /login.
       */
      {
        path: "/discovery",
        element: (
          <ProtectedRoute>
            <DiscoveryPage />
          </ProtectedRoute>
        ),
      },

      {
        path: "/matches",
        element: (
          <ProtectedRoute>
            <MatchesPage />
          </ProtectedRoute>
        ),
      },

      /**
       * Toute route inconnue affiche la page 404.
       */
      {
        path: "*",
        element: <NotFoundPage />,
      },
    ],
  },
]);
