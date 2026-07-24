import { httpClient } from "./httpClient";
import type { ProfileVerificationState } from "../types/profileVerification";

const ENDPOINT = "/v1/profiles/verification/me/";

export async function getProfileVerification(): Promise<ProfileVerificationState> {
  const response = await httpClient.get<ProfileVerificationState>(ENDPOINT);
  return response.data;
}

export async function submitProfileVerification(
  selfie: File,
): Promise<ProfileVerificationState> {
  const formData = new FormData();
  formData.append("selfie", selfie);

  const response = await httpClient.post<ProfileVerificationState>(
    ENDPOINT,
    formData,
  );
  return response.data;
}

