import {
  type ChangeEvent,
  type FormEvent,
  useEffect,
  useMemo,
  useState,
} from "react";
import { Link } from "react-router-dom";

import { normalizeApiError } from "../../api/apiError";
import {
  getProfileVerification,
  submitProfileVerification,
} from "../../api/profileVerificationService";
import type { ProfileVerificationState } from "../../types/profileVerification";

const MAX_FILE_BYTES = 8 * 1024 * 1024;

function formatDate(value: string | null): string {
  if (!value) {
    return "—";
  }
  return new Intl.DateTimeFormat("fr-FR", {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(new Date(value));
}

export function ProfileVerificationPage() {
  const [state, setState] = useState<ProfileVerificationState | null>(null);
  const [selfie, setSelfie] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState("");
  const [isLoading, setIsLoading] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  useEffect(() => {
    let active = true;
    void getProfileVerification()
      .then((result) => {
        if (active) {
          setState(result);
        }
      })
      .catch((caught: unknown) => {
        if (active) {
          setError(normalizeApiError(caught).message);
        }
      })
      .finally(() => {
        if (active) {
          setIsLoading(false);
        }
      });
    return () => {
      active = false;
    };
  }, []);

  useEffect(() => {
    return () => {
      if (previewUrl) {
        URL.revokeObjectURL(previewUrl);
      }
    };
  }, [previewUrl]);

  const statusClass = useMemo(
    () => `verification-status verification-status--${state?.status ?? "not_submitted"}`,
    [state?.status],
  );

  function selectSelfie(event: ChangeEvent<HTMLInputElement>) {
    const selected = event.target.files?.[0] ?? null;
    setError("");
    setMessage("");
    if (!selected) {
      setSelfie(null);
      setPreviewUrl("");
      return;
    }
    if (!["image/jpeg", "image/png", "image/webp"].includes(selected.type)) {
      setError("Choisis une image JPEG, PNG ou WebP.");
      event.target.value = "";
      return;
    }
    if (selected.size > MAX_FILE_BYTES) {
      setError("Le selfie ne peut pas dépasser 8 Mio.");
      event.target.value = "";
      return;
    }
    setSelfie(selected);
    setPreviewUrl(URL.createObjectURL(selected));
  }

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!selfie || isSubmitting || !state?.can_submit) {
      return;
    }
    setIsSubmitting(true);
    setError("");
    setMessage("");
    try {
      const result = await submitProfileVerification(selfie);
      setState(result);
      setSelfie(null);
      setPreviewUrl("");
      setMessage("Ta demande a été transmise de manière sécurisée.");
    } catch (caught: unknown) {
      setError(normalizeApiError(caught).message);
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <main className="profile-verification-page">
      <section className="profile-verification-hero">
        <p className="section-heading__eyebrow">Confiance sur Mbolo</p>
        <h1>Vérifier mon profil</h1>
        <p>
          Le badge est accordé après comparaison humaine entre un selfie récent
          et ta photo principale. La validation de l’e-mail ne donne plus ce badge.
        </p>
      </section>

      {error ? <div className="form-alert form-alert--error" role="alert"><span>!</span><p>{error}</p></div> : null}
      {message ? <div className="form-alert form-alert--success" role="status"><span>✓</span><p>{message}</p></div> : null}

      {isLoading ? (
        <p className="verification-loading">Chargement du statut…</p>
      ) : state ? (
        <div className="profile-verification-grid">
          <section className="verification-card">
            <p className="section-heading__eyebrow">Statut actuel</p>
            <div className={statusClass}>
              <span aria-hidden="true">
                {state.status === "approved" ? "✓" : state.status === "rejected" ? "!" : "⌛"}
              </span>
              <div>
                <h2>{state.status_label}</h2>
                <p>
                  {state.status === "approved"
                    ? "Ton badge Profil vérifié est visible sur Mbolo."
                    : state.status === "pending"
                      ? "Un administrateur doit encore examiner ta demande."
                      : state.status === "rejected"
                        ? "Tu peux corriger le problème et envoyer un nouveau selfie."
                        : "Tu n’as pas encore envoyé de demande."}
                </p>
              </div>
            </div>
            {state.rejection_reason ? (
              <div className="verification-rejection">
                <strong>Pourquoi recommencer ?</strong>
                <p>{state.rejection_reason}</p>
              </div>
            ) : null}
            <dl className="verification-dates">
              <div><dt>Envoyée</dt><dd>{formatDate(state.submitted_at)}</dd></div>
              <div><dt>Examinée</dt><dd>{formatDate(state.reviewed_at)}</dd></div>
            </dl>
          </section>

          <form className="verification-card" onSubmit={submit}>
            <p className="section-heading__eyebrow">Justificatif privé</p>
            <h2>Prends un selfie récent</h2>
            <ul className="verification-guidelines">
              <li>Visage entièrement visible et bien éclairé.</li>
              <li>Une seule personne, sans lunettes sombres ni filtre.</li>
              <li>Le visage doit correspondre à ta photo principale.</li>
              <li>N’envoie pas de passeport ni de carte d’identité à cette étape.</li>
            </ul>

            {state.can_submit ? (
              <>
                <label className="verification-upload">
                  Sélectionner mon selfie
                  <input
                    type="file"
                    accept="image/jpeg,image/png,image/webp"
                    onChange={selectSelfie}
                  />
                </label>
                {previewUrl ? (
                  <img className="verification-preview" src={previewUrl} alt="Aperçu local du selfie sélectionné" />
                ) : null}
                <button type="submit" disabled={!selfie || isSubmitting}>
                  {isSubmitting ? "Envoi sécurisé…" : "Envoyer ma demande"}
                </button>
              </>
            ) : (
              <p className="verification-locked">
                {state.is_verified
                  ? "Aucun nouvel envoi n’est nécessaire."
                  : "Tu pourras agir après la décision de l’équipe Mbolo."}
              </p>
            )}
          </form>
        </div>
      ) : null}

      <nav className="verification-links" aria-label="Liens de vérification">
        <Link to="/profile/edit">← Retour à mon profil</Link>
        <Link to="/profile/photos">Gérer ma photo principale →</Link>
      </nav>
    </main>
  );
}

