export interface PremiumEntitlements {
  unlimited_likes: boolean;
  see_likers: boolean;
  advanced_filters: boolean;
  rewind_pass: boolean;
  read_receipts: boolean;
  priority_profile: boolean;
  incognito_mode: boolean;
  priority_support: boolean;
  profile_boost: boolean;
  boosts_per_window: number;
  super_like: boolean;
  super_likes_per_day: number;
}

export interface SubscriptionState {
  plan: "free" | "plus" | "prestige";
  plan_name: string;
  status: string;
  is_premium: boolean;
  starts_at: string | null;
  ends_at: string | null;
  auto_renew: boolean;
  entitlements: PremiumEntitlements;
}

export interface PremiumPlan {
  code: "free" | "plus" | "prestige";
  name: string;
  description: string;
  features: string[];
  price_label: string;
  amount_xaf: number;
  payment_available: boolean;
}

export interface PremiumPaymentMethod {
  code: "airtel_money" | "moov_money" | "bank_card";
  name: string;
  description: string;
  available: boolean;
}

export interface PremiumOverview {
  subscription: SubscriptionState;
  plans: PremiumPlan[];
  payment_methods: PremiumPaymentMethod[];
  currency: "XAF";
  payment_notice: string;
  privacy: PremiumPrivacyState;
  boost: ProfileBoostState;
}

export interface PremiumPrivacyState {
  incognito_enabled: boolean;
  incognito_available: boolean;
  effective_incognito: boolean;
}

export interface ProfileBoostState {
  entitled: boolean;
  active: boolean;
  active_until: string | null;
  duration_minutes: number;
  allowance_per_7_days: number;
  remaining: number;
  next_available_at: string | null;
}


export type PremiumPaymentStatus =
  | "created"
  | "pending"
  | "succeeded"
  | "failed"
  | "canceled"
  | "expired";

export interface PremiumPaymentTransaction {
  id: string;
  plan: "plus" | "prestige";
  plan_name: string;
  method: "airtel_money" | "moov_money" | "bank_card";
  method_name: string;
  status: PremiumPaymentStatus;
  amount_xaf: number;
  currency: "XAF";
  provider: string;
  provider_reference: string;
  created_at: string;
  updated_at: string;
  verified_at: string | null;
  can_confirm_in_test_mode: boolean;
}

export interface PremiumPaymentConfirmation {
  transaction: PremiumPaymentTransaction;
  subscription: SubscriptionState;
}

export interface PremiumPaymentHistory {
  transactions: PremiumPaymentTransaction[];
}
