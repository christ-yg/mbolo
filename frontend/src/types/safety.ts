
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
