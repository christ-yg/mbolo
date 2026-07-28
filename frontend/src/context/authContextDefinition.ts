import { createContext } from "react";

import type {
  AuthenticatedUser,
  EmailTwoFactorConfirmPayload,
  LoginPayload,
  LoginResult,
} from "../types/auth";

export interface AuthContextValue {
  user: AuthenticatedUser | null;
  isInitializing: boolean;
  isAuthenticated: boolean;
  login: (payload: LoginPayload) => Promise<LoginResult>;
  confirmTwoFactor: (
    payload: EmailTwoFactorConfirmPayload,
  ) => Promise<AuthenticatedUser>;
  logout: () => Promise<void>;
  refreshCurrentUser: () => Promise<AuthenticatedUser | null>;
}

export const AuthContext =
  createContext<AuthContextValue | undefined>(undefined);
