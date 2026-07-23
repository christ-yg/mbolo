/**
 * Carte publique d'un match Mbolo.
 *
 * Les seules données affichées sont celles transmises
 * explicitement par MatchSerializer.
 */

import type { MatchItem } from "../../types/matches";

interface MatchCardProps {
  match: MatchItem;
}

/**
 * Convertit certaines valeurs techniques du backend
 * en libellés lisibles.
 */
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
      .replace(/^./, (character) =>
        character.toUpperCase(),
      )
  );
}

/**
 * Génère au maximum deux initiales publiques.
 */
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

function getPrimaryPhotoUrl(
  match: MatchItem,
): string | null {
  const photo = [...match.other_profile.photos]
    .sort(
      (first, second) =>
        Number(second.is_primary) -
          Number(first.is_primary) ||
        first.position - second.position,
    )
    .find((item) => Boolean(item.image_url));

  return photo?.image_url ?? null;
}

/**
 * Formate la date dans la langue du navigateur.
 */
function formatMatchDate(createdAt: string): string {
  const date = new Date(createdAt);

  if (Number.isNaN(date.getTime())) {
    return "Date non disponible";
  }

  return new Intl.DateTimeFormat("fr-FR", {
    day: "numeric",
    month: "long",
    year: "numeric",
  }).format(date);
}

export function MatchCard({
  match,
}: MatchCardProps) {
  const profile = match.other_profile;
  const primaryPhotoUrl = getPrimaryPhotoUrl(match);

  return (
    <article className="match-card">
      <div className="match-card__visual">
        {primaryPhotoUrl ? (
          <img
            className="match-card__photo"
            src={primaryPhotoUrl}
            alt={`Photo principale de ${profile.display_name}`}
          />
        ) : (
          <div
            className="match-card__initials"
            aria-hidden="true"
          >
            {getInitials(profile.display_name)}
          </div>
        )}

        {profile.is_verified ? (
          <span className="match-card__verified">
            <span aria-hidden="true">✓</span>
            Profil vérifié
          </span>
        ) : null}
      </div>

      <div className="match-card__content">
        <p className="section-heading__eyebrow">
          Connexion réciproque
        </p>

        <div className="match-card__title-row">
          <h2>{profile.display_name}</h2>
          <span>{profile.age} ans</span>
        </div>

        <div className="match-card__metadata">
          <span>{formatPublicValue(profile.city)}</span>
          <span>{formatPublicValue(profile.gender)}</span>
          <span>
            {formatPublicValue(
              profile.dating_intent,
            )}
          </span>
        </div>

        <p className="match-card__biography">
          {profile.biography ||
            "Cette personne n'a pas encore ajouté de présentation publique."}
        </p>

        <div className="match-card__footer">
          <div>
            <small>Match créé le</small>
            <strong>
              {formatMatchDate(match.created_at)}
            </strong>
          </div>

          <span
            className="match-card__privacy"
            title="Les informations privées restent protégées."
          >
            ◇ Données privées protégées
          </span>
        </div>
      </div>
    </article>
  );
}
