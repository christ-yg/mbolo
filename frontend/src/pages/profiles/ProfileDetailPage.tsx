
import {
  useEffect,
  useMemo,
  useState,
} from "react";
import {
  useNavigate,
  useParams,
} from "react-router-dom";

import { normalizeApiError } from "../../api/apiError";
import { getPublicProfileDetail } from "../../api/profileDetailService";
import type { PublicProfileDetail } from "../../types/profileDetail";

type DetailStatus = "loading" | "success" | "error";

export function ProfileDetailPage() {
  const navigate = useNavigate();
  const { profileId = "" } = useParams();

  const [status, setStatus] =
    useState<DetailStatus>("loading");
  const [profile, setProfile] =
    useState<PublicProfileDetail | null>(null);
  const [errorMessage, setErrorMessage] =
    useState("");

  useEffect(() => {
    let isActive = true;

    async function loadProfile(): Promise<void> {
      setStatus("loading");
      setErrorMessage("");

      try {
        const result =
          await getPublicProfileDetail(profileId);

        if (!isActive) {
          return;
        }

        setProfile(result);
        setStatus("success");
      } catch (error: unknown) {
        if (!isActive) {
          return;
        }

        const normalized = normalizeApiError(error);
        setErrorMessage(normalized.message);
        setStatus("error");
      }
    }

    void loadProfile();

    return () => {
      isActive = false;
    };
  }, [profileId]);

  const orderedPhotos = useMemo(
    () =>
      [...(profile?.photos ?? [])].sort(
        (first, second) =>
          Number(second.is_primary) -
            Number(first.is_primary) ||
          first.position - second.position,
      ),
    [profile],
  );

  if (status === "loading") {
    return (
      <main className="profile-detail-page">
        <section className="profile-detail-state">
          Chargement sécurisé du profil…
        </section>
      </main>
    );
  }

  if (status === "error" || profile === null) {
    return (
      <main className="profile-detail-page">
        <section className="profile-detail-state">
          <h1>Profil indisponible</h1>
          <p>
            {errorMessage ||
              "Ce profil n’est pas accessible."}
          </p>
          <button type="button" onClick={() => navigate(-1)}>
            Revenir
          </button>
        </section>
      </main>
    );
  }

  return (
    <main className="profile-detail-page">
      <section className="profile-detail-page__topbar">
        <button type="button" onClick={() => navigate(-1)}>
          ← Retour
        </button>

        <span>
          {profile.relationship === "match"
            ? "Profil d’un match"
            : "Profil public"}
        </span>
      </section>

      <section className="profile-detail-layout">
        <div className="profile-detail-gallery">
          {orderedPhotos.length > 0 ? (
            orderedPhotos.map((photo) => (
              photo.image_url ? (
                <img
                  key={photo.id}
                  src={photo.image_url}
                  alt={`Photo de ${profile.display_name}`}
                  loading="lazy"
                />
              ) : null
            ))
          ) : (
            <div className="profile-detail-gallery__placeholder">
              {profile.display_name.charAt(0).toUpperCase()}
            </div>
          )}
        </div>

        <article className="profile-detail-card">
          <p className="section-heading__eyebrow">
            Rencontre Mbolo
          </p>

          <div className="profile-detail-card__title">
            <h1>{profile.display_name}</h1>
            {profile.is_verified ? (
              <span aria-label="Compte vérifié">✓</span>
            ) : null}
          </div>

          <p className="profile-detail-card__summary">
            {profile.age !== null
              ? `${profile.age} ans`
              : "Âge non précisé"}
            {" · "}
            {profile.city}
          </p>

          <dl className="profile-detail-card__facts">
            <div>
              <dt>Recherche</dt>
              <dd>{profile.dating_intent}</dd>
            </div>
            <div>
              <dt>Genre</dt>
              <dd>{profile.gender}</dd>
            </div>
          </dl>

          <section className="profile-detail-card__bio">
            <h2>À propos</h2>
            <p>
              {profile.biography ||
                "Cette personne n’a pas encore ajouté de biographie."}
            </p>
          </section>

          <div className="profile-detail-card__actions">
            {profile.relationship === "match" ? (
              <button
                type="button"
                onClick={() => navigate("/matches")}
              >
                Voir dans Mes matchs
              </button>
            ) : (
              <button
                type="button"
                onClick={() => navigate("/discovery")}
              >
                Revenir à Découvrir
              </button>
            )}
          </div>
        </article>
      </section>
    </main>
  );
}
