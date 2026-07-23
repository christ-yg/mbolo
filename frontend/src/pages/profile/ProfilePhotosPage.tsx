import {
  useEffect,
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

const MAX_PHOTOS = 6;
const MAX_BYTES = 8 * 1024 * 1024;
const ACCEPTED_TYPES = new Set(["image/jpeg", "image/png", "image/webp"]);

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

  useEffect(() => {
    let isActive = true;
    void getMyProfilePhotos()
      .then((result) => {
        if (isActive) setPhotos(sortProfilePhotos(result.results));
      })
      .catch((error: unknown) => {
        if (isActive) setErrorMessage(error instanceof Error ? error.message : "Chargement impossible.");
      })
      .finally(() => {
        if (isActive) setIsLoading(false);
      });
    return () => { isActive = false; };
  }, []);

  useEffect(() => {
    return () => {
      if (previewUrl) URL.revokeObjectURL(previewUrl);
    };
  }, [previewUrl]);

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
      setSuccessMessage("Photo ajoutée et sécurisée avec succès.");
      if (previewUrl) URL.revokeObjectURL(previewUrl);
      setSelectedFile(null);
      setPreviewUrl(null);
      if (inputReference.current) inputReference.current.value = "";
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
      // Le backend peut automatiquement désigner une nouvelle photo
      // principale après la suppression. On recharge donc la galerie afin
      // d'afficher exactement l'état enregistré dans PostgreSQL.
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
    return <main className="profile-photos-state">Chargement de tes photos…</main>;
  }

  return (
    <main className="profile-photos-page">
      <header className="profile-photos-page__header">
        <div>
          <p className="section-heading__eyebrow">Ton image sur Mbolo</p>
          <h1>Mes photos</h1>
          <p>Ajoute jusqu’à six photos authentiques. Mbolo vérifie, nettoie et réencode chaque image en WebP.</p>
        </div>
        <div className="profile-photos-page__counter">
          <strong>{photos.length}/{MAX_PHOTOS}</strong>
          <span>photos ajoutées</span>
        </div>
      </header>

      <section className="profile-photo-upload">
        <div className="profile-photo-upload__copy">
          <p className="section-heading__eyebrow">Ajouter une photo</p>
          <h2>Choisis une image nette</h2>
          <p>JPEG, PNG ou WebP · 8 Mo maximum · au moins 320 × 320 pixels.</p>
          <input
            ref={inputReference}
            type="file"
            accept="image/jpeg,image/png,image/webp"
            disabled={photos.length >= MAX_PHOTOS || isWorking}
            onChange={(event) => selectFile(event.target.files?.[0] ?? null)}
          />
        </div>

        <div className="profile-photo-upload__preview">
          {previewUrl ? <img src={previewUrl} alt="Aperçu avant envoi" /> : <span aria-hidden="true">+</span>}
          <button type="button" disabled={!selectedFile || isWorking} onClick={() => void handleUpload()}>
            {isWorking ? "Traitement…" : "Ajouter cette photo"}
          </button>
        </div>
      </section>

      {errorMessage ? <p className="profile-photos-message profile-photos-message--error" role="alert">{errorMessage}</p> : null}
      {successMessage ? <p className="profile-photos-message profile-photos-message--success" role="status">{successMessage}</p> : null}

      <section className="profile-photos-gallery" aria-label="Galerie du profil">
        {photos.length === 0 ? (
          <div className="profile-photos-empty">
            <h2>Ta galerie est vide</h2>
            <p>La première photo ajoutée deviendra automatiquement ta photo principale.</p>
          </div>
        ) : photos.map((photo) => (
          <article className="profile-photo-card" key={photo.id}>
            <div className="profile-photo-card__image">
              {photo.image_url ? <img src={photo.image_url} alt={`Photo ${photo.position + 1} du profil`} /> : <span>Image indisponible</span>}
              {photo.is_primary ? <strong>Principale</strong> : null}
            </div>
            <div className="profile-photo-card__actions">
              <button type="button" disabled={photo.is_primary || isWorking} onClick={() => void handlePrimary(photo)}>
                {photo.is_primary ? "Photo principale" : "Définir comme principale"}
              </button>
              <button type="button" disabled={isWorking} onClick={() => setDeleteTarget(photo)}>Supprimer</button>
            </div>
          </article>
        ))}
      </section>

      <div className="profile-photos-page__footer">
        <Link to="/profile/edit">← Retour à mon profil</Link>
      </div>

      {deleteTarget ? (
        <div className="profile-photo-dialog-backdrop" role="presentation">
          <section className="profile-photo-dialog" role="dialog" aria-modal="true" aria-labelledby="delete-photo-title">
            <p className="section-heading__eyebrow">Confirmation</p>
            <h2 id="delete-photo-title">Supprimer cette photo ?</h2>
            <p>Cette action retirera définitivement la photo de ton profil.</p>
            <div>
              <button type="button" disabled={isWorking} onClick={() => setDeleteTarget(null)}>Annuler</button>
              <button type="button" disabled={isWorking} onClick={() => void confirmDeletion()}>{isWorking ? "Suppression…" : "Supprimer"}</button>
            </div>
          </section>
        </div>
      ) : null}
    </main>
  );
}
