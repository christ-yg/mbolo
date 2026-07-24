export type ProfileVerificationStatus =
  | "not_submitted"
  | "pending"
  | "approved"
  | "rejected";

export interface ProfileVerificationState {
  status: ProfileVerificationStatus;
  status_label: string;
  can_submit: boolean;
  is_verified: boolean;
  rejection_reason: string;
  submitted_at: string | null;
  reviewed_at: string | null;
  updated_at: string;
}

