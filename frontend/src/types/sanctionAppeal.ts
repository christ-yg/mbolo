export interface SanctionAppealPayload {
  email: string;
  password: string;
  message: string;
}

export interface SanctionAppealResult {
  id: string;
  status: "pending";
}
