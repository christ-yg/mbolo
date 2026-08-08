/** Routeur principal de Mbolo. */

import type { ReactNode } from "react";
import { createBrowserRouter } from "react-router-dom";

import { ProtectedRoute } from "../components/auth/ProtectedRoute";
import { PublicLayout } from "../layouts/PublicLayout";
import { AccessibilityPage } from "../pages/accessibility/AccessibilityPage";
import { AboutPage } from "../pages/about/AboutPage";
import { MySpacePage } from "../pages/account/MySpacePage";
import { ForgotPasswordPage } from "../pages/auth/ForgotPasswordPage";
import { LoginPage } from "../pages/auth/LoginPage";
import { RegisterPage } from "../pages/auth/RegisterPage";
import { ResetPasswordPage } from "../pages/auth/ResetPasswordPage";
import { SanctionAppealPage } from "../pages/auth/SanctionAppealPage";
import { VerifyEmailPage } from "../pages/auth/VerifyEmailPage";
import { ContactPage } from "../pages/contact/ContactPage";
import { DiscoveryPage } from "../pages/discovery/DiscoveryPage";
import { HelpPage } from "../pages/help/HelpPage";
import { HomePage } from "../pages/home/HomePage";
import { HowItWorksPage } from "../pages/howItWorks/HowItWorksPage";
import { LegalPage } from "../pages/legal/LegalPage";
import { ReceivedLikesPage } from "../pages/likes/ReceivedLikesPage";
import { MatchesPage } from "../pages/matches/MatchesPage";
import { ConversationPage } from "../pages/messages/ConversationPage";
import { MessagesPage } from "../pages/messages/MessagesPage";
import { NotFoundPage } from "../pages/NotFoundPage";
import { NotificationsPage } from "../pages/notifications/NotificationsPage";
import { PremiumPage } from "../pages/premium/PremiumPage";
import { ProfileEditPage } from "../pages/profile/ProfileEditPage";
import { ProfilePhotosPage } from "../pages/profile/ProfilePhotosPage";
import { ProfileVerificationPage } from "../pages/profile/ProfileVerificationPage";
import { ProfileDetailPage } from "../pages/profiles/ProfileDetailPage";
import { AccountSecurityPage } from "../pages/settings/AccountSecurityPage";
import { BlockedUsersPage } from "../pages/settings/BlockedUsersPage";
import { DiscoveryPreferencesPage } from "../pages/settings/DiscoveryPreferencesPage";
import { PrivacyCenterPage } from "../pages/settings/PrivacyCenterPage";
import { ReportsPage } from "../pages/settings/ReportsPage";
import { SafetyPage } from "../pages/settings/SafetyPage";

function protectedPage(page: ReactNode) {
  return <ProtectedRoute>{page}</ProtectedRoute>;
}

export const appRouter = createBrowserRouter([
  {
    element: <PublicLayout />,
    children: [
      { path: "/", element: <HomePage /> },
      { path: "/about", element: <AboutPage /> },
      { path: "/how-it-works", element: <HowItWorksPage /> },
      { path: "/help", element: <HelpPage /> },
      { path: "/contact", element: <ContactPage /> },
      { path: "/accessibility", element: <AccessibilityPage /> },
      { path: "/login", element: <LoginPage /> },
      { path: "/register", element: <RegisterPage /> },
      { path: "/forgot-password", element: <ForgotPasswordPage /> },
      { path: "/reset-password", element: <ResetPasswordPage /> },
      { path: "/verify-email", element: <VerifyEmailPage /> },
      { path: "/safety", element: <SafetyPage /> },
      { path: "/sanction-appeal", element: <SanctionAppealPage /> },
      { path: "/legal/:document", element: <LegalPage /> },

      { path: "/discovery", element: protectedPage(<DiscoveryPage />) },
      { path: "/matches", element: protectedPage(<MatchesPage />) },
      { path: "/likes-received", element: protectedPage(<ReceivedLikesPage />) },
      { path: "/profiles/:profileId", element: protectedPage(<ProfileDetailPage />) },
      { path: "/account", element: protectedPage(<MySpacePage />) },
      { path: "/profile/edit", element: protectedPage(<ProfileEditPage />) },
      { path: "/profile/photos", element: protectedPage(<ProfilePhotosPage />) },
      { path: "/profile/verification", element: protectedPage(<ProfileVerificationPage />) },
      { path: "/messages", element: protectedPage(<MessagesPage />) },
      { path: "/messages/:conversationId", element: protectedPage(<ConversationPage />) },
      { path: "/notifications", element: protectedPage(<NotificationsPage />) },
      { path: "/blocked-users", element: protectedPage(<BlockedUsersPage />) },
      { path: "/reports", element: protectedPage(<ReportsPage />) },
      { path: "/account/security", element: protectedPage(<AccountSecurityPage />) },
      { path: "/account/privacy", element: protectedPage(<PrivacyCenterPage />) },
      { path: "/premium", element: protectedPage(<PremiumPage />) },
      { path: "/discovery-preferences", element: protectedPage(<DiscoveryPreferencesPage />) },
      { path: "*", element: <NotFoundPage /> },
    ],
  },
]);
