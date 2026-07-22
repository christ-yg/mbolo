
export type PreferenceGender =
  | "man"
  | "woman"
  | "non_binary"
  | "prefer_not_to_say";

export type PreferenceCity =
  | "libreville"
  | "port_gentil"
  | "franceville"
  | "oyem"
  | "moanda"
  | "lambarene"
  | "mouila"
  | "tchibanga"
  | "koulamoutou"
  | "makokou"
  | "bitam"
  | "other";

export type PreferenceDatingIntent =
  | "serious_relationship"
  | "friendship"
  | "discussion"
  | "marriage"
  | "not_sure";

export interface DiscoveryPreferences {
  id: string;
  minimum_age: number;
  maximum_age: number;
  preferred_genders: PreferenceGender[];
  preferred_cities: PreferenceCity[];
  preferred_dating_intents: PreferenceDatingIntent[];
  maximum_distance_km: number;
  only_verified_profiles: boolean;
  only_profiles_with_photos: boolean;
  created_at: string;
  updated_at: string;
}

export type UpdateDiscoveryPreferencesPayload = Pick<
  DiscoveryPreferences,
  | "minimum_age"
  | "maximum_age"
  | "preferred_genders"
  | "preferred_cities"
  | "preferred_dating_intents"
  | "maximum_distance_km"
  | "only_verified_profiles"
  | "only_profiles_with_photos"
>;
