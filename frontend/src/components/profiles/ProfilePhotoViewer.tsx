import { useEffect, useRef, useState } from "react";
import "./ProfilePhotoViewer.css";

type Photo = { id: string; image_url: string };
export function ProfilePhotoViewer({ photos, initialId, name, onClose }: {
  photos: Photo[]; initialId: string; name: string; onClose: () => void;
}) {
  const dialog = useRef<HTMLDialogElement>(null);
  const [index, setIndex] = useState(Math.max(0, photos.findIndex(photo => photo.id === initialId)));
  const [zoom, setZoom] = useState(false);
  const [failed, setFailed] = useState(false);
  const [attempt, setAttempt] = useState(0);
  useEffect(() => {
    const element = dialog.current;
    const previous = document.activeElement as HTMLElement | null;
    const overflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    element?.showModal();
    return () => { element?.close(); document.body.style.overflow = overflow; previous?.focus(); };
  }, []);
  function move(delta: number) {
    setIndex(value => (value + delta + photos.length) % photos.length);
    setZoom(false); setFailed(false); setAttempt(0);
  }
  const photo = photos[index];
  return <dialog ref={dialog} className="profile-photo-viewer" aria-label={`Photos de ${name}`}
    onCancel={event => { event.preventDefault(); onClose(); }}
    onKeyDown={event => {
      if (event.key === "ArrowRight") { event.preventDefault(); move(1); }
      if (event.key === "ArrowLeft") { event.preventDefault(); move(-1); }
    }}>
    <div className="profile-photo-viewer__toolbar">
      <p role="status">Photo {index + 1} sur {photos.length}</p>
      <button type="button" onClick={onClose} autoFocus>Fermer la galerie</button>
    </div>
    <div className="profile-photo-viewer__image">
      {failed ? <div role="alert"><p>Cette photo ne peut pas être chargée.</p><button type="button" onClick={() => { setFailed(false); setAttempt(value => value + 1); }}>Réessayer la photo</button></div>
        : <img key={`${photo.id}-${attempt}`} src={photo.image_url} alt={`Photo ${index + 1} de ${name}`}
          className={zoom ? "is-zoomed" : ""} onError={() => setFailed(true)} />}
    </div>
    <div className="profile-photo-viewer__toolbar">
      <button type="button" disabled={photos.length < 2} onClick={() => move(-1)}>Photo précédente</button>
      <button type="button" disabled={failed} aria-pressed={zoom} onClick={() => setZoom(value => !value)}>{zoom ? "Réduire la photo" : "Agrandir la photo"}</button>
      <button type="button" disabled={photos.length < 2} onClick={() => move(1)}>Photo suivante</button>
    </div>
  </dialog>;
}
