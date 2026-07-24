/**
 * Service API des préférences d'alertes de connexion.
 */

import type { ApiSuccessResponse } from "../types/api";
import type {
  LoginAlertEmailPreference,
  UpdateLoginAlertEmailPreferencePayload,
} from "../types/securityAlerts";

import { ensureCsrfToken } from "./csrfService";
import { httpClient } from "./httpClient";


type PreferenceApiResponse =
  | ApiSuccessResponse<LoginAlertEmailPreference>
  | LoginAlertEmailPreference;


function unwrapPreference(
  payload: PreferenceApiResponse,
): LoginAlertEmailPreference {
  if (
    typeof payload === "object" &&
    payload !== null &&
    "data" in payload &&
    payload.data
  ) {
    return payload.data;
  }

  return payload as LoginAlertEmailPreference;
}


export async function getLoginAlertEmailPreference():
Promise<LoginAlertEmailPreference> {
  const response = await httpClient.get<PreferenceApiResponse>(
    "/v1/auth/security/login-alert-emails/",
  );

  return unwrapPreference(response.data);
}


export async function updateLoginAlertEmailPreference(
  payload: UpdateLoginAlertEmailPreferencePayload,
): Promise<LoginAlertEmailPreference> {
  const csrfToken = await ensureCsrfToken();

  const response = await httpClient.patch<PreferenceApiResponse>(
    "/v1/auth/security/login-alert-emails/",
    payload,
    {
      headers: {
        "X-CSRFToken": csrfToken,
      },
    },
  );

  return unwrapPreference(response.data);
}
