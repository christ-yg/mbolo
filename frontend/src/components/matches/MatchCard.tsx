/**
 * Carte premium d'un match Mbolo.
 *
 * La carte affiche uniquement les informations publiques fournies par
 * MatchSerializer. Elle ne tente jamais de déduire ou d'exposer une donnée
 * privée absente de la réponse Django.
 */

import type { MatchItem } from "../../types/matches";


interface MatchCardProps {
  match: MatchItem;
  onOpenConversation: () => void;
  onOpenProfile: () => void;
  onRequestUnmatch: () => void;
}


function formatPublicValue(value: string): string {
  const labels: Record<string, string> = {
    man: "Homme",
    woman: "Femme",
    non_binary: "Non binaire",
    friendship: "Amitié",
    discussion: "Discussion",
    serious_relationship: "Relation sérieuse",
    casual_relationship: "Relation sans engagement",
    libreville: "Libreville",
    owendo: "Owendo",
    akanda: "Akanda",
    moanda: "Moanda",
    oyem: "Oyem",
    lambarene: "Lambaréné",
  };

  return (
    labels[value] ??
    value
      .replaceAll("_", " ")
      .replace(/^./, (character) => character.toUpperCase())
  );
}


function getInitials(displayName: string): string {
  const parts = displayName
    .trim()
    .split(/\s+/)
    .filter(Boolean)
    .slice(0, 2);

  if (parts.length === 0) {
    return "M";
  }

  return parts
    .map((part) => part.charAt(0).toUpperCase())
    .join("");
}


function getPrimaryPhotoUrl(match: MatchItem): string | null {
  const photo = [...match.other_profile.photos]
    .sort(
      (first, second) =>
        Number(second.is_primary) - Number(first.is_primary) ||
        first.position - second.position,
    )
    .find((item) => Boolean(item.image_url));

  return photo?.image_url ?? null;
}


function formatMatchDate(createdAt: string): string {
  const date = new Date(createdAt);

  if (Number.isNaN(date.getTime())) {
    return "Date non disponible";
  }

  return new Intl.DateTimeFormat("fr-FR", {
    day: "numeric",
    month: "short",
    year: "numeric",
  }).format(date);
}


export function MatchCard({
  match,
  onOpenConversation,
  onOpenProfile,
  onRequestUnmatch,
}: MatchCardProps) {
  const profile = match.other_profile;
  const primaryPhotoUrl = getPrimaryPhotoUrl(match);

  return (
    <article className="match-premium-card">
      <div className="match-premium-card__visual">
        {primaryPhotoUrl ? (
          <img
            className="match-premium-card__photo"
            src={primaryPhotoUrl}
            alt={`Photo principale de ${profile.display_name}`}
          />
        ) : (
          <div
            className="match-premium-card__initials"
            aria-hidden="true"
          >
            {getInitials(profile.display_name)}
          </div>
        )}

        <div className="match-premium-card__overlay" />

        <span className="match-premium-card__badge">
          Match réciproque
        </span>

        <button
          type="button"
          className="match-premium-card__menu"
          onClick={onRequestUnmatch}
          aria-label={`Gérer le match avec ${profile.display_name}`}
          title="Gérer ce match"
        >
          ⋯
        </button>

        <div className="match-premium-card__identity">
          <div className="match-premium-card__name-row">
            <h2>
              {profile.display_name}
              {profile.age !== null ? <span>, {profile.age}</span> : null}
            </h2>

            {profile.is_verified ? (
              <span
                className="match-premium-card__verified"
                title="Profil vérifié"
                aria-label="Profil vérifié"
              >
                ✓
              </span>
            ) : null}
          </div>

          <p>
            {formatPublicValue(profile.city)} · {formatPublicValue(profile.dating_intent)}
          </p>
        </div>
      </div>

      <div className="match-premium-card__content">
        <div className="match-premium-card__meta-row">
          <span>Connectés le {formatMatchDate(match.created_at)}</span>
          <span>{formatPublicValue(profile.gender)}</span>
        </div>

        <p className="match-premium-card__biography">
          {profile.biography ||
            "Cette personne n'a pas encore ajouté de présentation publique."}
        </p>

        <div className="match-premium-card__privacy">
          <span aria-hidden="true">◇</span>
          <p>
            Conversation privée disponible uniquement pour ce match actif.
          </p>
        </div>

        <div className="match-premium-card__actions">
          <button
            type="button"
            className="match-premium-card__message"
            onClick={onOpenConversation}
          >
            Envoyer un message
            <span aria-hidden="true">→</span>
          </button>

          <button
            type="button"
            className="match-premium-card__profile"
            onClick={onOpenProfile}
          >
            Voir le profil
          </button>
        </div>
      </div>
    </article>
  );
}
