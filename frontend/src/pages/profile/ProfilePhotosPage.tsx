import {
  useEffect,
  useMemo,
  useRef,
  useState,
} from "react";
import { Link } from "react-router-dom";

import {
  deleteProfilePhoto,
  getMyProfilePhotos,
  setPrimaryProfilePhoto,
  sortProfilePhotos,
  uploadProfilePhoto,
} from "../../api/profilePhotoService";
import type { ProfilePhoto } from "../../types/profilePhotos";

import "./ProfilePhotosPage.css";

const MAX_PHOTOS = 6;
const MAX_BYTES = 8 * 1024 * 1024;
const ACCEPTED_TYPES = new Set(["image/jpeg", "image/png", "image/webp"]);

function formatFileSize(bytes: number): string {
  if (bytes < 1024 * 1024) return `${Math.max(1, Math.round(bytes / 1024))} Ko`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} Mo`;
}

function getModerationTone(status: ProfilePhoto["moderation_status"]): string {
  if (status === "approved") return "approved";
  if (status === "rejected") return "rejected";
  return "pending";
}

export function ProfilePhotosPage() {
  const inputReference = useRef<HTMLInputElement | null>(null);
  const [photos, setPhotos] = useState<ProfilePhoto[]>([]);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [deleteTarget, setDeleteTarget] = useState<ProfilePhoto | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isWorking, setIsWorking] = useState(false);
  const [errorMessage, setErrorMessage] = useState("");
  const [successMessage, setSuccessMessage] = useState("");

  const approvedCount = useMemo(
    () => photos.filter((photo) => photo.moderation_status === "approved").length,
    [photos],
  );

  const pendingCount = useMemo(
    () => photos.filter((photo) => photo.moderation_status === "pending").length,
    [photos],
  );

  const primaryPhoto = useMemo(
    () => photos.find((photo) => photo.is_primary) ?? null,
    [photos],
  );

  useEffect(() => {
    let isActive = true;

    void getMyProfilePhotos()
      .then((result) => {
        if (isActive) setPhotos(sortProfilePhotos(result.results));
      })
      .catch((error: unknown) => {
        if (isActive) {
          setErrorMessage(error instanceof Error ? error.message : "Chargement impossible.");
        }
      })
      .finally(() => {
        if (isActive) setIsLoading(false);
      });

    return () => {
      isActive = false;
    };
  }, []);

  useEffect(() => {
    return () => {
      if (previewUrl) URL.revokeObjectURL(previewUrl);
    };
  }, [previewUrl]);

  function resetSelectedFile(): void {
    if (previewUrl) URL.revokeObjectURL(previewUrl);
    setSelectedFile(null);
    setPreviewUrl(null);
    if (inputReference.current) inputReference.current.value = "";
  }

  function selectFile(file: File | null): void {
    setErrorMessage("");
    setSuccessMessage("");

    if (previewUrl) URL.revokeObjectURL(previewUrl);

    if (!file) {
      setSelectedFile(null);
      setPreviewUrl(null);
      return;
    }

    if (!ACCEPTED_TYPES.has(file.type)) {
      setErrorMessage("Choisis une image JPEG, PNG ou WebP.");
      setSelectedFile(null);
      setPreviewUrl(null);
      return;
    }

    if (file.size > MAX_BYTES) {
      setErrorMessage("La photo ne doit pas dépasser 8 Mo.");
      setSelectedFile(null);
      setPreviewUrl(null);
      return;
    }

    setSelectedFile(file);
    setPreviewUrl(URL.createObjectURL(file));
  }

  async function handleUpload(): Promise<void> {
    if (!selectedFile || isWorking || photos.length >= MAX_PHOTOS) return;

    setIsWorking(true);
    setErrorMessage("");
    setSuccessMessage("");

    try {
      const result = await uploadProfilePhoto(selectedFile, photos.length === 0);
      setPhotos((current) => sortProfilePhotos([...current, result.data]));
      setSuccessMessage("Photo ajoutée. Elle sera visible après validation par la modération.");
      resetSelectedFile();
    } catch (error: unknown) {
      setErrorMessage(error instanceof Error ? error.message : "Envoi impossible.");
    } finally {
      setIsWorking(false);
    }
  }

  async function handlePrimary(photo: ProfilePhoto): Promise<void> {
    if (photo.is_primary || isWorking) return;

    setIsWorking(true);
    setErrorMessage("");
    setSuccessMessage("");

    try {
      const result = await setPrimaryProfilePhoto(photo.id);
      setPhotos((current) => current.map((item) => ({
        ...item,
        is_primary: item.id === result.data.id,
      })));
      setSuccessMessage("Photo principale mise à jour.");
    } catch (error: unknown) {
      setErrorMessage(error instanceof Error ? error.message : "Modification impossible.");
    } finally {
      setIsWorking(false);
    }
  }

  async function confirmDeletion(): Promise<void> {
    if (!deleteTarget || isWorking) return;

    setIsWorking(true);
    setErrorMessage("");
    setSuccessMessage("");

    try {
      await deleteProfilePhoto(deleteTarget.id);

      // Le backend peut désigner automatiquement une nouvelle photo principale.
      // On recharge donc la galerie pour afficher exactement l'état enregistré.
      const refreshed = await getMyProfilePhotos();
      setPhotos(sortProfilePhotos(refreshed.results));
      setDeleteTarget(null);
      setSuccessMessage("Photo supprimée.");
    } catch (error: unknown) {
      setErrorMessage(error instanceof Error ? error.message : "Suppression impossible.");
    } finally {
      setIsWorking(false);
    }
  }

  if (isLoading) {
    return (
      <main className="profile-photos-state" aria-live="polite">
        <span className="profile-photos-state__mark" aria-hidden="true">M</span>
        <strong>Chargement de ta galerie…</strong>
      </main>
    );
  }

  const hasReachedLimit = photos.length >= MAX_PHOTOS;

  return (
    <main className="profile-photos-page">
      <section className="profile-photos-hero">
        <div className="profile-photos-hero__copy">
          <p className="profile-photos-kicker">Ton image sur Mbolo</p>
          <h1>Construis une galerie qui te ressemble.</h1>
          <p className="profile-photos-hero__lead">
            Ajoute jusqu’à six photos authentiques. Chaque image passe par un contrôle technique puis une vérification avant d’être affichée aux autres membres.
          </p>
          <div className="profile-photos-hero__badges" aria-label="Protections appliquées">
            <span>✓ Fichiers contrôlés côté serveur</span>
            <span>✓ Visibilité après modération</span>
            <span>✓ Suppression définitive sur demande</span>
          </div>
        </div>

        <aside className="profile-photos-hero__summary" aria-label="Résumé de la galerie">
          <span className="profile-photos-summary__icon" aria-hidden="true">◇</span>
          <strong>{photos.length}/{MAX_PHOTOS}</strong>
          <span>photos ajoutées</span>
          <div className="profile-photos-summary__stats">
            <span><b>{approvedCount}</b> approuvée{approvedCount > 1 ? "s" : ""}</span>
            <span><b>{pendingCount}</b> en attente</span>
          </div>
        </aside>
      </section>

      <section className="profile-photo-upload" aria-labelledby="profile-photo-upload-title">
        <div className="profile-photo-upload__copy">
          <p className="profile-photos-kicker">Nouvelle photo</p>
          <h2 id="profile-photo-upload-title">Choisis une image nette et récente.</h2>
          <p>
            JPEG, PNG ou WebP · 8 Mo maximum · au moins 320 × 320 pixels. La première photo devient automatiquement la photo principale.
          </p>

          <div className="profile-photo-upload__rules">
            <span>Visage clairement visible</span>
            <span>Une seule personne de préférence</span>
            <span>Pas de contenu trompeur ou illégal</span>
          </div>

          <input
            ref={inputReference}
            id="profile-photo-input"
            className="profile-photo-upload__native-input"
            type="file"
            accept="image/jpeg,image/png,image/webp"
            disabled={hasReachedLimit || isWorking}
            onChange={(event) => selectFile(event.target.files?.[0] ?? null)}
          />

          <label
            className={`profile-photo-upload__picker${hasReachedLimit ? " profile-photo-upload__picker--disabled" : ""}`}
            htmlFor="profile-photo-input"
            aria-disabled={hasReachedLimit || isWorking}
          >
            <span aria-hidden="true">＋</span>
            <strong>{hasReachedLimit ? "Limite atteinte" : "Sélectionner une photo"}</strong>
            <small>{hasReachedLimit ? "Supprime une photo pour en ajouter une nouvelle." : "Choisir un fichier depuis ton appareil"}</small>
          </label>
        </div>

        <div className="profile-photo-upload__preview-card">
          <div className="profile-photo-upload__preview">
            {previewUrl ? (
              <img src={previewUrl} alt="Aperçu local avant envoi" />
            ) : primaryPhoto?.image_url ? (
              <img src={primaryPhoto.image_url} alt="Photo principale actuelle" />
            ) : (
              <div className="profile-photo-upload__placeholder" aria-hidden="true">M</div>
            )}
          </div>

          <div className="profile-photo-upload__preview-copy">
            <p className="profile-photos-kicker">Aperçu privé</p>
            <h3>{selectedFile ? selectedFile.name : "Ta prochaine photo apparaîtra ici"}</h3>
            <p>
              {selectedFile
                ? `${formatFileSize(selectedFile.size)} · aperçu local, pas encore envoyé`
                : "Aucun fichier n’est transmis tant que tu ne confirmes pas l’envoi."}
            </p>
          </div>

          <div className="profile-photo-upload__actions">
            {selectedFile ? (
              <button type="button" className="profile-photo-button profile-photo-button--ghost" disabled={isWorking} onClick={resetSelectedFile}>
                Annuler
              </button>
            ) : null}
            <button
              type="button"
              className="profile-photo-button profile-photo-button--primary"
              disabled={!selectedFile || isWorking || hasReachedLimit}
              onClick={() => void handleUpload()}
            >
              {isWorking ? "Traitement…" : "Ajouter cette photo"}
            </button>
          </div>
        </div>
      </section>

      {errorMessage ? (
        <p className="profile-photos-message profile-photos-message--error" role="alert">{errorMessage}</p>
      ) : null}

      {successMessage ? (
        <p className="profile-photos-message profile-photos-message--success" role="status">{successMessage}</p>
      ) : null}

      <section className="profile-photos-gallery-section" aria-labelledby="profile-photos-gallery-title">
        <header className="profile-photos-gallery-section__header">
          <div>
            <p className="profile-photos-kicker">Ta galerie</p>
            <h2 id="profile-photos-gallery-title">Choisis l’image qui te représente le mieux.</h2>
          </div>
          <p>
            La photo principale est utilisée en priorité dans Découvrir, les matchs et l’aperçu de ton profil.
          </p>
        </header>

        <div className="profile-photos-gallery" aria-label="Galerie du profil">
          {photos.length === 0 ? (
            <div className="profile-photos-empty">
              <span className="profile-photos-empty__icon" aria-hidden="true">✓</span>
              <p className="profile-photos-kicker">Galerie prête</p>
              <h3>Ajoute ta première photo.</h3>
              <p>Elle deviendra automatiquement ta photo principale et restera privée jusqu’à la validation de la modération.</p>
              <label className="profile-photo-button profile-photo-button--primary" htmlFor="profile-photo-input">
                Sélectionner une photo
              </label>
            </div>
          ) : photos.map((photo, index) => (
            <article className={`profile-photo-card${photo.is_primary ? " profile-photo-card--primary" : ""}`} key={photo.id}>
              <div className="profile-photo-card__image">
                {photo.image_url ? (
                  <img src={photo.image_url} alt={`Photo ${index + 1} du profil`} />
                ) : (
                  <span>Image indisponible</span>
                )}

                <div className="profile-photo-card__topline">
                  <span className={`profile-photo-card__status profile-photo-card__status--${getModerationTone(photo.moderation_status)}`}>
                    {photo.moderation_status_label}
                  </span>
                  <span className="profile-photo-card__position">{String(index + 1).padStart(2, "0")}</span>
                </div>

                {photo.is_primary ? (
                  <strong className="profile-photo-card__primary-badge">Photo principale</strong>
                ) : null}
              </div>

              <div className="profile-photo-card__body">
                <div>
                  <p className="profile-photos-kicker">Photo {index + 1}</p>
                  <h3>{photo.is_primary ? "Ton image principale" : "Photo secondaire"}</h3>
                  <p>
                    {photo.moderation_status === "approved"
                      ? "Cette photo peut être affichée selon la visibilité de ton profil."
                      : photo.moderation_status === "rejected"
                        ? "Cette photo n’est pas visible. Tu peux la supprimer puis en proposer une autre."
                        : "Cette photo reste privée pendant son examen."}
                  </p>
                </div>

                <div className="profile-photo-card__actions">
                  <button
                    type="button"
                    className="profile-photo-button profile-photo-button--secondary"
                    disabled={photo.is_primary || isWorking}
                    onClick={() => void handlePrimary(photo)}
                  >
                    {photo.is_primary ? "Photo principale" : "Définir comme principale"}
                  </button>
                  <button
                    type="button"
                    className="profile-photo-button profile-photo-button--danger"
                    disabled={isWorking}
                    onClick={() => setDeleteTarget(photo)}
                  >
                    Supprimer
                  </button>
                </div>
              </div>
            </article>
          ))}
        </div>
      </section>

      <section className="profile-photos-security-note">
        <div className="profile-photos-security-note__mark" aria-hidden="true">M</div>
        <div>
          <p className="profile-photos-kicker">Confidentialité par conception</p>
          <h2>Une photo en attente n’est jamais publique.</h2>
          <p>
            Le statut de modération est vérifié côté serveur. Une simple modification de l’interface ne peut pas rendre une photo visible.
          </p>
        </div>
        <Link to="/safety">Consulter le centre de sécurité →</Link>
      </section>

      <footer className="profile-photos-page__footer">
        <Link to="/profile/edit">← Retour à mon profil</Link>
      </footer>

      {deleteTarget ? (
        <div className="profile-photo-dialog-backdrop" role="presentation" onMouseDown={() => !isWorking && setDeleteTarget(null)}>
          <section
            className="profile-photo-dialog"
            role="dialog"
            aria-modal="true"
            aria-labelledby="delete-photo-title"
            onMouseDown={(event) => event.stopPropagation()}
          >
            <span className="profile-photo-dialog__icon" aria-hidden="true">!</span>
            <p className="profile-photos-kicker">Confirmation sensible</p>
            <h2 id="delete-photo-title">Supprimer cette photo ?</h2>
            <p>
              Cette action retirera définitivement la photo de ton profil. Si elle est principale, le serveur pourra désigner automatiquement une autre photo.
            </p>
            <div className="profile-photo-dialog__actions">
              <button type="button" className="profile-photo-button profile-photo-button--ghost" disabled={isWorking} onClick={() => setDeleteTarget(null)}>
                Annuler
              </button>
              <button type="button" className="profile-photo-button profile-photo-button--danger-solid" disabled={isWorking} onClick={() => void confirmDeletion()}>
                {isWorking ? "Suppression…" : "Supprimer définitivement"}
              </button>
            </div>
          </section>
        </div>
      ) : null}
    </main>
  );
}
