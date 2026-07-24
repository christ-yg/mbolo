import { ensureCsrfToken } from "./csrfService";
import { httpClient } from "./httpClient";
import type {
  SanctionAppealPayload,
  SanctionAppealResult,
} from "../types/sanctionAppeal";

interface AppealResponse {
  data: SanctionAppealResult;
  message: string;
}

export async function submitSanctionAppeal(
  payload: SanctionAppealPayload,
): Promise<AppealResponse> {
  await ensureCsrfToken();
  const response = await httpClient.post<AppealResponse>(
    "/v1/safety/sanction-appeals/",
    payload,
  );
  return response.data;
}
