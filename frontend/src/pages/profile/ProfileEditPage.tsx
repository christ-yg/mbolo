import {
  useEffect,
  useMemo,
  useState,
} from "react";
import { Link } from "react-router-dom";

import {
  getMyProfile,
  ProfileUpdateError,
  updateMyProfile,
} from "../../api/profileService";
import { useAuth } from "../../hooks/useAuth";
import type {
  EditableProfile,
  ProfileCity,
  ProfileDatingIntent,
  ProfileFieldErrors,
  ProfileGender,
  UpdateProfilePayload,
} from "../../types/profileEdit";

const GENDERS: Array<{value: ProfileGender; label: string}> = [
  {value: "", label: "Sélectionner"},
  {value: "man", label: "Homme"},
  {value: "woman", label: "Femme"},
  {value: "non_binary", label: "Non binaire"},
  {value: "prefer_not_to_say", label: "Je préfère ne pas préciser"},
];

const CITIES: Array<{value: ProfileCity; label: string}> = [
  {value: "", label: "Sélectionner"},
  {value: "libreville", label: "Libreville"},
  {value: "port_gentil", label: "Port-Gentil"},
  {value: "franceville", label: "Franceville"},
  {value: "oyem", label: "Oyem"},
  {value: "moanda", label: "Moanda"},
  {value: "lambarene", label: "Lambaréné"},
  {value: "mouila", label: "Mouila"},
  {value: "tchibanga", label: "Tchibanga"},
  {value: "koulamoutou", label: "Koulamoutou"},
  {value: "makokou", label: "Makokou"},
  {value: "bitam", label: "Bitam"},
  {value: "other", label: "Autre ville"},
];

const INTENTS: Array<{value: ProfileDatingIntent; label: string}> = [
  {value: "", label: "Sélectionner"},
  {value: "serious_relationship", label: "Relation sérieuse"},
  {value: "friendship", label: "Amitié"},
  {value: "discussion", label: "Discussion"},
  {value: "marriage", label: "Mariage"},
  {value: "not_sure", label: "Je ne sais pas encore"},
];

const EMPTY_FORM: UpdateProfilePayload = {
  display_name: "",
  birth_date: null,
  gender: "",
  city: "",
  biography: "",
  dating_intent: "",
  is_discoverable: false,
};

function labelFor<T extends string>(
  options: Array<{value: T; label: string}>,
  value: T,
): string {
  return options.find((option) => option.value === value)?.label ?? "Non précisé";
}

function calculateAge(birthDate: string | null): number | null {
  if (!birthDate) {
    return null;
  }

  const parsed = new Date(`${birthDate}T00:00:00`);
  const today = new Date();

  if (Number.isNaN(parsed.getTime())) {
    return null;
  }

  let age = today.getFullYear() - parsed.getFullYear();
  const monthDifference = today.getMonth() - parsed.getMonth();

  if (
    monthDifference < 0 ||
    (monthDifference === 0 && today.getDate() < parsed.getDate())
  ) {
    age -= 1;
  }

  return age;
}

export function ProfileEditPage() {
  const { user } = useAuth();
  const [profile, setProfile] = useState<EditableProfile | null>(null);
  const [form, setForm] = useState<UpdateProfilePayload>(EMPTY_FORM);
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [errorMessage, setErrorMessage] = useState("");
  const [successMessage, setSuccessMessage] = useState("");
  const [fieldErrors, setFieldErrors] = useState<ProfileFieldErrors>({});

  useEffect(() => {
    let isActive = true;

    async function loadProfile(): Promise<void> {
      try {
        const result = await getMyProfile();

        if (isActive) {
          setProfile(result);
          setForm({
            display_name: result.display_name,
            birth_date: result.birth_date,
            gender: result.gender,
            city: result.city,
            biography: result.biography,
            dating_intent: result.dating_intent,
            is_discoverable: result.is_discoverable,
          });
        }
      } catch (error: unknown) {
        if (isActive) {
          setErrorMessage(
            error instanceof Error ? error.message : "Chargement impossible.",
          );
        }
      } finally {
        if (isActive) {
          setIsLoading(false);
        }
      }
    }

    void loadProfile();

    return () => {
      isActive = false;
    };
  }, []);

  const previewAge = useMemo(
    () => calculateAge(form.birth_date),
    [form.birth_date],
  );

  const requiredProfileIsComplete = Boolean(
    form.display_name.trim() &&
    form.birth_date &&
    form.gender &&
    form.city &&
    form.dating_intent,
  );

  function updateField<K extends keyof UpdateProfilePayload>(
    field: K,
    value: UpdateProfilePayload[K],
  ): void {
    setForm((current) => ({...current, [field]: value}));
    setFieldErrors((current) => ({...current, [field]: undefined}));
    setSuccessMessage("");
  }

  function validateForm(): ProfileFieldErrors {
    const errors: ProfileFieldErrors = {};
    const normalizedName = form.display_name.trim().replace(/\s+/g, " ");

    if (normalizedName.length > 0 && normalizedName.length < 2) {
      errors.display_name = "Le nom public doit contenir au moins 2 caractères.";
    }

    if (normalizedName.length > 50) {
      errors.display_name = "Le nom public ne peut pas dépasser 50 caractères.";
    }

    if (form.biography.length > 500) {
      errors.biography = "La biographie ne peut pas dépasser 500 caractères.";
    }

    if (form.birth_date && (previewAge === null || previewAge < 18)) {
      errors.birth_date = "Tu dois avoir au moins 18 ans pour utiliser Mbolo.";
    }

    if (form.is_discoverable && !requiredProfileIsComplete) {
      errors.is_discoverable =
        "Complète le nom, la naissance, le genre, la ville et l’intention avant d’être visible.";
    }

    if (form.is_discoverable && !user?.isEmailVerified) {
      errors.is_discoverable =
        "Vérifie d’abord ton adresse e-mail avant d’apparaître dans Découvrir.";
    }

    return errors;
  }

  async function handleSubmit(
    event: React.FormEvent<HTMLFormElement>,
  ): Promise<void> {
    event.preventDefault();

    if (isSaving) {
      return;
    }

    const clientErrors = validateForm();

    if (Object.keys(clientErrors).length > 0) {
      setFieldErrors(clientErrors);
      setErrorMessage("");
      return;
    }

    setIsSaving(true);
    setErrorMessage("");
    setSuccessMessage("");
    setFieldErrors({});

    try {
      const saved = await updateMyProfile({
        ...form,
        display_name: form.display_name.trim().replace(/\s+/g, " "),
        biography: form.biography.trim(),
      });

      setProfile(saved);
      setForm({
        display_name: saved.display_name,
        birth_date: saved.birth_date,
        gender: saved.gender,
        city: saved.city,
        biography: saved.biography,
        dating_intent: saved.dating_intent,
        is_discoverable: saved.is_discoverable,
      });
      setSuccessMessage("Ton profil a été enregistré avec succès.");
    } catch (error: unknown) {
      if (error instanceof ProfileUpdateError) {
        setFieldErrors(error.fieldErrors);
      }

      setErrorMessage(
        error instanceof Error ? error.message : "Enregistrement impossible.",
      );
    } finally {
      setIsSaving(false);
    }
  }

  if (isLoading) {
    return <main className="profile-edit-state">Chargement de ton profil…</main>;
  }

  if (profile === null) {
    return (
      <main className="profile-edit-state">
        <h1>Profil indisponible</h1>
        <p>{errorMessage}</p>
        <Link to="/">Retour à l’accueil</Link>
      </main>
    );
  }

  return (
    <main className="profile-edit-page">
      <header className="profile-edit-page__header">
        <div>
          <p className="section-heading__eyebrow">Mon identité sur Mbolo</p>
          <h1>Modifier mon profil</h1>
          <p>
            Présente-toi avec authenticité. Seules les informations affichées
            dans l’aperçu pourront être visibles par les autres membres.
          </p>
        </div>

        <div className="profile-edit-page__status">
          <strong>{requiredProfileIsComplete ? "Complet" : "À compléter"}</strong>
          <span>{profile.is_discoverable ? "Visible dans Découvrir" : "Profil privé"}</span>
        </div>
      </header>

      <form className="profile-edit-layout" onSubmit={handleSubmit} noValidate>
        <section className="profile-edit-form" aria-label="Informations du profil">
          <div className="profile-edit-section-heading">
            <div>
              <p className="section-heading__eyebrow">Informations essentielles</p>
              <h2>Parle-nous de toi</h2>
            </div>
            <p>Les champs marqués d’un astérisque sont nécessaires pour être visible.</p>
          </div>

          <div className="profile-edit-grid">
            <label className="profile-edit-field profile-edit-field--wide">
              <span>Nom public *</span>
              <input
                type="text"
                value={form.display_name}
                onChange={(event) => updateField("display_name", event.target.value)}
                maxLength={50}
                autoComplete="nickname"
                aria-invalid={Boolean(fieldErrors.display_name)}
              />
              <small>{fieldErrors.display_name ?? `${form.display_name.length}/50 caractères`}</small>
            </label>

            <label className="profile-edit-field">
              <span>Date de naissance *</span>
              <input
                type="date"
                value={form.birth_date ?? ""}
                onChange={(event) => updateField("birth_date", event.target.value || null)}
                aria-invalid={Boolean(fieldErrors.birth_date)}
              />
              <small>{fieldErrors.birth_date ?? "Ton âge sera calculé automatiquement."}</small>
            </label>

            <label className="profile-edit-field">
              <span>Genre *</span>
              <select
                value={form.gender}
                onChange={(event) => updateField("gender", event.target.value as ProfileGender)}
                aria-invalid={Boolean(fieldErrors.gender)}
              >
                {GENDERS.map((option) => (
                  <option key={option.value || "empty"} value={option.value}>{option.label}</option>
                ))}
              </select>
              <small>{fieldErrors.gender ?? "Choisis l’option qui te correspond."}</small>
            </label>

            <label className="profile-edit-field">
              <span>Ville *</span>
              <select
                value={form.city}
                onChange={(event) => updateField("city", event.target.value as ProfileCity)}
                aria-invalid={Boolean(fieldErrors.city)}
              >
                {CITIES.map((option) => (
                  <option key={option.value || "empty"} value={option.value}>{option.label}</option>
                ))}
              </select>
              <small>{fieldErrors.city ?? "Ta ville aide à proposer des rencontres pertinentes."}</small>
            </label>

            <label className="profile-edit-field">
              <span>Intention relationnelle *</span>
              <select
                value={form.dating_intent}
                onChange={(event) => updateField("dating_intent", event.target.value as ProfileDatingIntent)}
                aria-invalid={Boolean(fieldErrors.dating_intent)}
              >
                {INTENTS.map((option) => (
                  <option key={option.value || "empty"} value={option.value}>{option.label}</option>
                ))}
              </select>
              <small>{fieldErrors.dating_intent ?? "Annonce clairement ce que tu recherches."}</small>
            </label>

            <label className="profile-edit-field profile-edit-field--wide">
              <span>Biographie</span>
              <textarea
                value={form.biography}
                onChange={(event) => updateField("biography", event.target.value)}
                maxLength={500}
                rows={7}
                placeholder="Tes passions, tes valeurs, ce qui te rend unique…"
                aria-invalid={Boolean(fieldErrors.biography)}
              />
              <small>{fieldErrors.biography ?? `${form.biography.length}/500 caractères`}</small>
            </label>
          </div>

          <label className="profile-edit-visibility">
            <input
              type="checkbox"
              checked={form.is_discoverable}
              onChange={(event) => updateField("is_discoverable", event.target.checked)}
            />
            <span>
              <strong>Afficher mon profil dans Découvrir</strong>
              <small>
                Tu dois avoir 18 ans, compléter les informations obligatoires
                et vérifier ton adresse e-mail.
              </small>
            </span>
          </label>

          {fieldErrors.is_discoverable ? (
            <p className="profile-edit-form__error">{fieldErrors.is_discoverable}</p>
          ) : null}

          {errorMessage ? <p className="profile-edit-form__error" role="alert">{errorMessage}</p> : null}
          {successMessage ? <p className="profile-edit-form__success" role="status">{successMessage}</p> : null}

          <div className="profile-edit-form__actions">
            <Link to="/discovery">Annuler</Link>
            <button type="submit" disabled={isSaving}>
              {isSaving ? "Enregistrement…" : "Enregistrer mon profil"}
            </button>
          </div>
        </section>

        <aside className="profile-edit-preview" aria-label="Aperçu du profil">
          <p className="section-heading__eyebrow">Aperçu en direct</p>
          <div className="profile-edit-preview__avatar" aria-hidden="true">
            {form.display_name.trim().charAt(0).toUpperCase() || "M"}
          </div>
          <h2>
            {form.display_name.trim() || "Ton nom"}
            {previewAge !== null ? `, ${previewAge}` : ""}
          </h2>
          <p className="profile-edit-preview__location">
            {labelFor(CITIES, form.city)} · {labelFor(INTENTS, form.dating_intent)}
          </p>
          <p className="profile-edit-preview__biography">
            {form.biography.trim() || "Ta biographie apparaîtra ici. Quelques mots sincères suffisent pour donner envie de te connaître."}
          </p>
          <div className="profile-edit-preview__facts">
            <span>{labelFor(GENDERS, form.gender)}</span>
            <span>
              {form.is_discoverable
                ? user?.isEmailVerified && requiredProfileIsComplete
                  ? "Visible après enregistrement"
                  : "Visibilité indisponible"
                : profile.is_discoverable
                  ? "Profil visible"
                  : "Profil privé"}
            </span>
          </div>
          <p className="profile-edit-preview__privacy">
            Ton e-mail, ton mot de passe et tes informations techniques ne sont jamais affichés ici.
          </p>
        </aside>
      </form>
    </main>
  );
}
