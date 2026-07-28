import type {
  PremiumOverview,
  PremiumPrivacyState,
  PremiumPaymentConfirmation,
  PremiumPaymentHistory,
  PremiumPaymentTransaction,
  ProfileBoostState,
} from "../types/premium";

import { httpClient } from "./httpClient";


export async function getPremiumOverview(): Promise<PremiumOverview> {
  const response = await httpClient.get<{
    data: PremiumOverview;
  }>("/v1/premium/overview/");

  return response.data.data;
}

export async function activateProfileBoost(): Promise<ProfileBoostState> {
  const response = await httpClient.post<{ data: ProfileBoostState }>(
    "/v1/premium/boost/",
    {},
  );
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


export async function createPremiumCheckout(
  plan: "plus" | "prestige",
  method: "airtel_money" | "moov_money" | "bank_card",
): Promise<PremiumPaymentTransaction> {
  const response = await httpClient.post<{
    data: PremiumPaymentTransaction;
  }>("/v1/premium/payments/checkout/", {
    plan,
    method,
  });
  return response.data.data;
}

export async function confirmPremiumPaymentTest(
  transactionId: string,
): Promise<PremiumPaymentConfirmation> {
  const response = await httpClient.post<{
    data: PremiumPaymentConfirmation;
  }>("/v1/premium/payments/confirm-test/", {
    transaction_id: transactionId,
  });
  return response.data.data;
}

export async function cancelPremiumPayment(
  transactionId: string,
): Promise<PremiumPaymentTransaction> {
  const response = await httpClient.post<{
    data: PremiumPaymentTransaction;
  }>("/v1/premium/payments/cancel/", {
    transaction_id: transactionId,
  });
  return response.data.data;
}

export async function getPremiumPaymentHistory(): Promise<PremiumPaymentHistory> {
  const response = await httpClient.get<{
    data: PremiumPaymentHistory;
  }>("/v1/premium/payments/history/");
  return response.data.data;
}
