/**
 * Carte publique d'un profil affiché dans le moteur
 * de découverte Mbolo.
 *
 * Cette première version ne contient pas encore de photo.
 *
 * Pourquoi ?
 *
 * Le serializer Django DiscoveryProfileSerializer retourne
 * actuellement uniquement :
 *
 * - id ;
 * - display_name ;
 * - age ;
 * - gender ;
 * - city ;
 * - biography ;
 * - dating_intent ;
 * - is_verified.
 *
 * Il ne retourne pas encore de champ photo.
 *
 * Nous utilisons donc les initiales du profil afin de ne pas
 * inventer une donnée absente de l'API.
 */

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
  isActionPending = false,
}: ProfileCardProps) {
  /**
   * Calcul des initiales utilisées dans la partie visuelle.
   */
  const initials = getProfileInitials(
    profile.display_name,
  );

  return (
    <article className="discovery-profile-card">
      {/*
       * Partie visuelle de la carte.
       *
       * Une vraie photo sera intégrée lorsque le backend
       * l'exposera explicitement dans le serializer.
       */}
      <div className="discovery-profile-card__visual">
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

        {/*
         * Initiales utilisées comme représentation provisoire
         * tant que les photos ne sont pas exposées par l'API.
         */}
        <div
          className="discovery-profile-card__initials"
          aria-hidden="true"
        >
          {initials}
        </div>

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
