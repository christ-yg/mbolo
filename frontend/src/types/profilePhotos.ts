/** Types échangés avec l'API sécurisée des photos de profil. */

export interface ProfilePhoto {
  id: string;
  image_url: string | null;
  position: number;
  is_primary: boolean;
  moderation_status: "pending" | "approved" | "rejected";
  moderation_status_label: string;
  created_at: string;
  updated_at: string;
}

export interface ProfilePhotoListResponse {
  results: ProfilePhoto[];
  count: number;
}

export interface ProfilePhotoMutationResponse {
  data: ProfilePhoto;
  message: string;
  processing?: {
    width: number;
    height: number;
    format: "webp";
  };
}
