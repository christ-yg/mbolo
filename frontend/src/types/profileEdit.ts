/**
 * Types de la page privée d'édition du profil Mbolo.
 *
 * Les noms des propriétés correspondent exactement au JSON Django REST.
 * Aucun champ sensible du compte (e-mail, mot de passe, permissions) n'est
 * présent : cette page ne manipule que les informations du profil public.
 */

export type ProfileGender =
  | ""
  | "man"
  | "woman"
  | "non_binary"
  | "prefer_not_to_say";

export type ProfileCity =
  | ""
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

export type ProfileDatingIntent =
  | ""
  | "serious_relationship"
  | "friendship"
  | "discussion"
  | "marriage"
  | "not_sure";

export interface EditableProfile {
  id: string;
  display_name: string;
  birth_date: string | null;
  age: number | null;
  gender: ProfileGender;
  city: ProfileCity;
  biography: string;
  dating_intent: ProfileDatingIntent;
  is_discoverable: boolean;
  is_complete: boolean;
  created_at: string;
  updated_at: string;
}

/** Seuls ces champs peuvent être envoyés lors du PATCH. */
export interface UpdateProfilePayload {
  display_name: string;
  birth_date: string | null;
  gender: ProfileGender;
  city: ProfileCity;
  biography: string;
  dating_intent: ProfileDatingIntent;
  is_discoverable: boolean;
}

export type ProfileFieldErrors = Partial<
  Record<keyof UpdateProfilePayload | "non_field_errors", string>
>;
