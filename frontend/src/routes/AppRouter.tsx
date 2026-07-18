/**
 * Routeur principal de Mbolo.
 *
 * createBrowserRouter utilise l'API History du navigateur afin
 * de fournir des URLs propres sans symbole #.
 */

import { createBrowserRouter } from "react-router-dom";

import { PublicLayout } from "../layouts/PublicLayout";
import { LoginPage } from "../pages/auth/LoginPage";
import { RegisterPage } from "../pages/auth/RegisterPage";
import { DiscoveryPage } from "../pages/discovery/DiscoveryPage";
import { HomePage } from "../pages/home/HomePage";
import { NotFoundPage } from "../pages/NotFoundPage";
import { SafetyPage } from "../pages/settings/SafetyPage";

export const appRouter = createBrowserRouter([
  {
    element: <PublicLayout />,
    children: [
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
        path: "/discovery",
        element: <DiscoveryPage />,
      },
      {
        path: "/safety",
        element: <SafetyPage />,
      },
      {
        path: "*",
        element: <NotFoundPage />,
      },
    ],
  },
]);
