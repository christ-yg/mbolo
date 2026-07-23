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
import { ForgotPasswordPage } from "../pages/auth/ForgotPasswordPage";
import { ResetPasswordPage } from "../pages/auth/ResetPasswordPage";
import { RegisterPage } from "../pages/auth/RegisterPage";
import { VerifyEmailPage } from "../pages/auth/VerifyEmailPage";
import { DiscoveryPage } from "../pages/discovery/DiscoveryPage";
import { HomePage } from "../pages/home/HomePage";
import { ReceivedLikesPage } from "../pages/likes/ReceivedLikesPage";
import { MatchesPage } from "../pages/matches/MatchesPage";
import { MessagesPage } from "../pages/messages/MessagesPage";
import { ConversationPage } from "../pages/messages/ConversationPage";
import { NotFoundPage } from "../pages/NotFoundPage";
import { NotificationsPage } from "../pages/notifications/NotificationsPage";
import { ProfileDetailPage } from "../pages/profiles/ProfileDetailPage";
import { ProfileEditPage } from "../pages/profile/ProfileEditPage";
import { ProfilePhotosPage } from "../pages/profile/ProfilePhotosPage";
import { SafetyPage } from "../pages/settings/SafetyPage";
import { AccountSecurityPage } from "../pages/settings/AccountSecurityPage";
import { PrivacyCenterPage } from "../pages/settings/PrivacyCenterPage";
import { BlockedUsersPage } from "../pages/settings/BlockedUsersPage";
import { DiscoveryPreferencesPage } from "../pages/settings/DiscoveryPreferencesPage";

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
        path: "/forgot-password",
        element: <ForgotPasswordPage />,
      },
      {
        path: "/reset-password",
        element: <ResetPasswordPage />,
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
      {
        path: "/likes-received",
        element: (
          <ProtectedRoute>
            <ReceivedLikesPage />
          </ProtectedRoute>
        ),
      },
      {
        path: "/profiles/:profileId",
        element: (
          <ProtectedRoute>
            <ProfileDetailPage />
          </ProtectedRoute>
        ),
      },
      {
        path: "/profile/edit",
        element: (
          <ProtectedRoute>
            <ProfileEditPage />
          </ProtectedRoute>
        ),
      },
      {
        path: "/profile/photos",
        element: (
          <ProtectedRoute>
            <ProfilePhotosPage />
          </ProtectedRoute>
        ),
      },
      {
        path: "/messages",
        element: (
          <ProtectedRoute>
            <MessagesPage />
          </ProtectedRoute>
        ),
      },
      {
        path: "/messages/:conversationId",
        element: (
          <ProtectedRoute>
            <ConversationPage />
          </ProtectedRoute>
        ),
      },

      {
        path: "/notifications",
        element: (
          <ProtectedRoute>
            <NotificationsPage />
          </ProtectedRoute>
        ),
      },
      {
        path: "/blocked-users",
        element: (
          <ProtectedRoute>
            <BlockedUsersPage />
          </ProtectedRoute>
        ),
      },
      {
        path: "/account/security",
        element: (
          <ProtectedRoute>
            <AccountSecurityPage />
          </ProtectedRoute>
        ),
      },
      {
        path: "/account/privacy",
        element: (
          <ProtectedRoute>
            <PrivacyCenterPage />
          </ProtectedRoute>
        ),
      },
      {
        path: "/discovery-preferences",
        element: (
          <ProtectedRoute>
            <DiscoveryPreferencesPage />
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
