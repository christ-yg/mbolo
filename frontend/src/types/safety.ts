
export type ReportReason =
  | "harassment"
  | "fake_profile"
  | "scam"
  | "inappropriate_content"
  | "threat"
  | "spam"
  | "underage_suspicion"
  | "other";

export interface ProfileSafetyActionResponse {
  created: boolean;
  message: string;
  deactivated_matches?: number;
}

export interface ProfileReportPayload {
  reason: ReportReason;
  description: string;
}

export interface BlockedProfilePhoto {
  id: string;
  image_url: string | null;
  position: number;
  is_primary: boolean;
}

export interface BlockedProfileSummary {
  id: string;
  display_name: string;
  age: number | null;
  city: string;
  city_label?: string;
  photos?: BlockedProfilePhoto[];
}

export interface BlockedUserItem {
  id: string;
  blocked_profile: BlockedProfileSummary | null;
  created_at: string;
}

export interface BlockedUsersPaginatedResponse {
  count: number;
  next: string | null;
  previous: string | null;
  results: BlockedUserItem[];
}
