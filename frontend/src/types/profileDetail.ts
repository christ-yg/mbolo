
import type {
  InteractionDecision,
} from "./interactions";


export interface PublicProfilePhoto {
  id: string;
  image_url: string | null;
  position: number;
  is_primary: boolean;
  created_at: string;
  updated_at: string;
}


export interface PublicProfileDetail {
  id: string;
  display_name: string;
  age: number | null;

  gender: string;
  gender_label: string;

  city: string;
  city_label: string;

  biography: string;

  dating_intent: string;
  dating_intent_label: string;

  is_verified: boolean;
  photos: PublicProfilePhoto[];

  relationship:
    | "discovery"
    | "match"
    | "public";

  current_decision:
    | InteractionDecision
    | null;
}
