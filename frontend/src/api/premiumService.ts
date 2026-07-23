import type {
  PremiumOverview,
  PremiumPrivacyState,
} from "../types/premium";

import { httpClient } from "./httpClient";


export async function getPremiumOverview(): Promise<PremiumOverview> {
  const response = await httpClient.get<{
    data: PremiumOverview;
  }>("/v1/premium/overview/");

  return response.data.data;
}

export async function updatePremiumPrivacy(
  incognitoEnabled: boolean,
): Promise<PremiumPrivacyState> {
  const response = await httpClient.patch<{
    data: PremiumPrivacyState;
  }>("/v1/premium/privacy/", {
    incognito_enabled: incognitoEnabled,
  });

  return response.data.data;
}
