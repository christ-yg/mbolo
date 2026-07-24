/**
 * Service API du journal de sécurité du compte.
 */

import type { ApiSuccessResponse } from "../types/api";
import type { AccountSecurityEvent } from "../types/securityEvents";

import { httpClient } from "./httpClient";


type SecurityEventsApiResponse =
  | ApiSuccessResponse<AccountSecurityEvent[]>
  | AccountSecurityEvent[];


export async function getAccountSecurityEvents():
Promise<AccountSecurityEvent[]> {
  const response = await httpClient.get<SecurityEventsApiResponse>(
    "/v1/auth/security/events/",
  );

  const payload = response.data;

  if (
    typeof payload === "object" &&
    payload !== null &&
    !Array.isArray(payload) &&
    "data" in payload
  ) {
    return payload.data;
  }

  return payload as AccountSecurityEvent[];
}
