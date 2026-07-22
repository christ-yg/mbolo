
import { httpClient } from "./httpClient";
import type { PublicProfileDetail } from "../types/profileDetail";

export async function getPublicProfileDetail(
  profileId: string,
): Promise<PublicProfileDetail> {
  const response =
    await httpClient.get<PublicProfileDetail>(
      `/v1/profiles/public/${encodeURIComponent(profileId)}/`,
    );

  return response.data;
}
