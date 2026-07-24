/**
 * Carte publique d'un profil affiché dans le moteur
 * de découverte Mbolo.
 *
 * La photo principale sécurisée est utilisée lorsqu'elle existe.
 * Les initiales restent disponibles comme solution de secours.
 */

import {
  useEffect,
  useMemo,
  useState,
} from "react";

import type { DiscoveryProfile } from "../../types/discovery";

/**
 * Propriétés que le composant ProfileCard doit recevoir.
 */
interface ProfileCardProps {
  /**
   * Profil actuellement affiché.
   */
  profile: DiscoveryProfile;

  /**
   * Position du profil dans la page courante.
   *
   * Exemple :
   *
   * 1 sur 10.
   */
  currentPosition: number;

  /**
   * Nombre total de profils présents dans la page
   * actuellement chargée.
   */
  totalInCurrentPage: number;

  /**
   * Fonction appelée lorsque l'utilisateur choisit
   * de passer ce profil.
   */
  onPass: () => void;

  /**
   * Fonction appelée lorsque l'utilisateur choisit
   * d'aimer ce profil.
   *
   * Cette première version ne crée pas encore
   * l'interaction dans Django.
   */
  onLike: () => void;

  /** Envoie un intérêt Premium distinct et prioritaire. */
  onSuperLike: () => void;
  superLikeLabel: string;
  isSuperLikeDisabled?: boolean;

  /**
   * Indique qu'une action est déjà en cours.
   *
   * Cette propriété permet de bloquer temporairement
   * les boutons afin d'empêcher les doubles clics.
   */
  isActionPending?: boolean;
}

/**
 * Calcule les initiales à partir du nom public.
 *
 * Exemples :
 *
 * "Arielle Mavoungou" devient "AM".
 * "Sarah" devient "S".
 * Une valeur vide devient "M".
 */
function getProfileInitials(displayName: string): string {
  /**
   * trim() supprime les espaces situés au début et à la fin.
   *
   * split(/\s+/) sépare le nom sur un ou plusieurs espaces.
   *
   * filter(Boolean) retire les valeurs vides éventuelles.
   *
   * slice(0, 2) conserve au maximum les deux premiers mots.
   */
  const normalizedParts = displayName
    .trim()
    .split(/\s+/)
    .filter(Boolean)
    .slice(0, 2);

  /**
   * Valeur de secours si aucun nom valide n'est disponible.
   */
  if (normalizedParts.length === 0) {
    return "M";
  }

  /**
   * Nous récupérons la première lettre de chaque partie,
   * puis nous la convertissons en majuscule.
   */
  return normalizedParts
    .map((part) => part.charAt(0).toUpperCase())
    .join("");
}

/**
 * Transforme une valeur technique retournée par Django
 * en texte plus lisible.
 *
 * Exemples :
 *
 * "long_term_relationship"
 * devient :
 * "Long term relationship"
 *
 * "serious-dating"
 * devient :
 * "Serious dating"
 */
function formatChoiceLabel(value: string): string {
  /**
   * Une chaîne vide reçoit un libellé neutre.
   */
  if (!value.trim()) {
    return "Non précisé";
  }

  /**
   * Nous remplaçons :
   *
   * - les underscores ;
   * - les tirets ;
   *
   * par des espaces.
   */
  const normalizedValue = value
    .replaceAll("_", " ")
    .replaceAll("-", " ")
    .trim()
    .toLowerCase();

  /**
   * Première lettre en majuscule.
   */
  return (
    normalizedValue.charAt(0).toUpperCase() +
    normalizedValue.slice(1)
  );
}

/**
 * Composant principal de la carte de profil.
 */
export function ProfileCard({
  profile,
  currentPosition,
  totalInCurrentPage,
  onPass,
  onLike,
  onSuperLike,
  superLikeLabel,
  isSuperLikeDisabled = false,
  isActionPending = false,
}: ProfileCardProps) {
  const [activePhotoIndex, setActivePhotoIndex] =
    useState(0);

  /**
   * Calcul des initiales utilisées dans la partie visuelle.
   */
  const initials = getProfileInitials(
    profile.display_name,
  );

  /**
   * La photo principale est prioritaire.
   *
   * Si une ancienne donnée ne possède pas encore ce marqueur,
   * la première photo ordonnée devient le visuel de secours.
   */
  const visiblePhotos = useMemo(
    () =>
      [...profile.photos]
        .filter((photo) => Boolean(photo.image_url))
        .sort(
          (first, second) =>
            Number(second.is_primary) -
              Number(first.is_primary) ||
            first.position - second.position,
        ),
    [profile.photos],
  );

  const activePhoto =
    visiblePhotos[activePhotoIndex] ?? null;

  /**
   * Chaque nouvelle carte recommence sur sa photo principale.
   */
  useEffect(() => {
    setActivePhotoIndex(0);
  }, [profile.id]);

  function showPreviousPhoto(): void {
    setActivePhotoIndex((current) =>
      current === 0
        ? visiblePhotos.length - 1
        : current - 1,
    );
  }

  function showNextPhoto(): void {
    setActivePhotoIndex((current) =>
      current === visiblePhotos.length - 1
        ? 0
        : current + 1,
    );
  }

  return (
    <article className="discovery-profile-card">
      <div
        className="discovery-profile-card__visual"
        tabIndex={visiblePhotos.length > 1 ? 0 : undefined}
        onKeyDown={(event) => {
          if (event.key === "ArrowLeft") {
            event.preventDefault();
            showPreviousPhoto();
          }

          if (event.key === "ArrowRight") {
            event.preventDefault();
            showNextPhoto();
          }
        }}
      >
        {activePhoto?.image_url ? (
          <img
            className="discovery-profile-card__photo"
            src={activePhoto.image_url}
            alt={
              `Photo ${activePhotoIndex + 1} sur ` +
              `${visiblePhotos.length} de ${profile.display_name}`
            }
          />
        ) : null}
        {/*
         * Indicateur de progression dans la page courante.
         */}
        <div
          className="discovery-profile-card__position"
          aria-label={
            `Profil ${currentPosition} sur ${totalInCurrentPage}`
          }
        >
          {currentPosition}/{totalInCurrentPage}
        </div>

        {/*
         * Badge affiché uniquement lorsque le backend indique
         * que l'adresse e-mail du compte est vérifiée.
         *
         * L'adresse elle-même reste confidentielle.
         */}
        {profile.is_verified ? (
          <div
            className="discovery-profile-card__verified"
            title="Compte avec adresse e-mail vérifiée"
          >
            <span aria-hidden="true">✓</span>

            Profil vérifié
          </div>
        ) : null}

        {!activePhoto?.image_url ? (
          <div
            className="discovery-profile-card__initials"
            aria-hidden="true"
          >
            {initials}
          </div>
        ) : null}

        {visiblePhotos.length > 1 ? (
          <>
            <button
              type="button"
              className={
                "discovery-profile-card__photo-control " +
                "discovery-profile-card__photo-control--previous"
              }
              aria-label="Afficher la photo précédente"
              onClick={showPreviousPhoto}
            >
              ‹
            </button>

            <button
              type="button"
              className={
                "discovery-profile-card__photo-control " +
                "discovery-profile-card__photo-control--next"
              }
              aria-label="Afficher la photo suivante"
              onClick={showNextPhoto}
            >
              ›
            </button>

            <div
              className="discovery-profile-card__photo-dots"
              aria-label={
                `Photo ${activePhotoIndex + 1} sur ` +
                `${visiblePhotos.length}`
              }
            >
              {visiblePhotos.map((photo, index) => (
                <button
                  key={photo.id}
                  type="button"
                  className={
                    index === activePhotoIndex
                      ? "is-active"
                      : ""
                  }
                  aria-label={`Afficher la photo ${index + 1}`}
                  aria-current={
                    index === activePhotoIndex
                      ? "true"
                      : undefined
                  }
                  onClick={() => {
                    setActivePhotoIndex(index);
                  }}
                />
              ))}
            </div>
          </>
        ) : null}

        {/*
         * Identité publique du profil.
         */}
        <div className="discovery-profile-card__visual-copy">
          <p>
            {profile.city.trim() ||
              "Ville non précisée"}
          </p>

          <h2>
            {profile.display_name}

            <span>{profile.age}</span>
          </h2>
        </div>
      </div>

      {/*
       * Partie textuelle et interactive de la carte.
       */}
      <div className="discovery-profile-card__content">
        {/*
         * Métadonnées publiques minimisées.
         */}
        <div className="discovery-profile-card__metadata">
          <span>
            {formatChoiceLabel(profile.gender)}
          </span>

          <span>
            {formatChoiceLabel(
              profile.dating_intent,
            )}
          </span>
        </div>

        {profile.common_interest_labels.length > 0 ? (
          <section className="discovery-profile-card__compatibility">
            <div>
              <p className="section-heading__eyebrow">Compatibilité</p>
              <strong>{profile.compatibility_score}%</strong>
            </div>
            <div>
              {profile.common_interest_labels.map((label) => (
                <span key={label}>{label}</span>
              ))}
            </div>
          </section>
        ) : null}

        {/*
         * Biographie publique du profil.
         */}
        <section className="discovery-profile-card__biography">
          <p className="section-heading__eyebrow">
            À propos
          </p>

          <p>
            {profile.biography.trim() ||
              "Ce profil n’a pas encore ajouté de biographie."}
          </p>
        </section>

        {/*
         * Message pédagogique et rassurant concernant
         * la confidentialité des informations privées.
         */}
        <div className="discovery-profile-card__security-note">
          <span aria-hidden="true">◇</span>

          <p>
            Les informations privées restent masquées
            jusqu’à une connexion réciproque.
          </p>
        </div>

        {/*
         * Actions de découverte.
         *
         * Les boutons sont désactivés lorsqu'une action
         * est déjà en cours.
         */}
        <div className="discovery-profile-card__actions">
          <button
            type="button"
            className="discovery-action-button discovery-action-button--super-like"
            disabled={isActionPending || isSuperLikeDisabled}
            onClick={onSuperLike}
            title="Montre un intérêt particulier à ce profil"
          >
            <span aria-hidden="true">★</span>
            {superLikeLabel}
          </button>

          <button
            type="button"
            className={
              "discovery-action-button " +
              "discovery-action-button--pass"
            }
            disabled={isActionPending}
            onClick={onPass}
          >
            <span aria-hidden="true">×</span>

            Passer
          </button>

          <button
            type="button"
            className={
              "discovery-action-button " +
              "discovery-action-button--like"
            }
            disabled={isActionPending}
            onClick={onLike}
          >
            J’aime

            <span aria-hidden="true">♥</span>
          </button>
        </div>
      </div>
    </article>
  );
}
