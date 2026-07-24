import type { ApiSuccessResponse } from "../types/api";
import type { ConnectedDevice } from "../types/connectedDevices";

import { ensureCsrfToken } from "./csrfService";
import { httpClient } from "./httpClient";


type ConnectedDevicesResponse =
  | ApiSuccessResponse<ConnectedDevice[]>
  | ConnectedDevice[];


export async function getConnectedDevices():
Promise<ConnectedDevice[]> {
  const response = await httpClient.get<ConnectedDevicesResponse>(
    "/v1/auth/security/sessions/",
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

  return payload as ConnectedDevice[];
}


export async function revokeConnectedDevice(
  sessionId: string,
  currentPassword: string,
): Promise<void> {
  const csrfToken = await ensureCsrfToken();

  await httpClient.post(
    `/v1/auth/security/sessions/${sessionId}/revoke/`,
    {
      current_password: currentPassword,
    },
    {
      headers: {
        "X-CSRFToken": csrfToken,
      },
    },
  );
}
