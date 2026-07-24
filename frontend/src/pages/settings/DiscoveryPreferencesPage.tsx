
import {
  useEffect,
  useMemo,
  useState,
} from "react";
import {
  Link,
  useNavigate,
} from "react-router-dom";

import {
  getDiscoveryPreferences,
  updateDiscoveryPreferences,
} from "../../api/discoveryPreferencesService";

import type {
  DiscoveryPreferences,
  PreferenceCity,
  PreferenceDatingIntent,
  PreferenceGender,
} from "../../types/discoveryPreferences";

const GENDER_OPTIONS: Array<{
  value: PreferenceGender;
  label: string;
}> = [
  {value: "man", label: "Hommes"},
  {value: "woman", label: "Femmes"},
  {value: "non_binary", label: "Personnes non binaires"},
  {
    value: "prefer_not_to_say",
    label: "Genre non précisé",
  },
];

const CITY_OPTIONS: Array<{
  value: PreferenceCity;
  label: string;
}> = [
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

const INTENT_OPTIONS: Array<{
  value: PreferenceDatingIntent;
  label: string;
}> = [
  {
    value: "serious_relationship",
    label: "Relation sérieuse",
  },
  {value: "friendship", label: "Amitié"},
  {value: "discussion", label: "Discussion"},
  {value: "marriage", label: "Mariage"},
  {value: "not_sure", label: "Je ne sais pas encore"},
];

function toggleValue<T extends string>(
  values: T[],
  value: T,
): T[] {
  return values.includes(value)
    ? values.filter((item) => item !== value)
    : [...values, value];
}

export function DiscoveryPreferencesPage() {
  const navigate = useNavigate();

  const [preferences, setPreferences] =
    useState<DiscoveryPreferences | null>(null);

  const [isLoading, setIsLoading] =
    useState(true);

  const [isSaving, setIsSaving] =
    useState(false);

  const [errorMessage, setErrorMessage] =
    useState("");

  const [successMessage, setSuccessMessage] =
    useState("");

  useEffect(() => {
    let isActive = true;

    async function load(): Promise<void> {
      try {
        const result =
          await getDiscoveryPreferences();

        if (isActive) {
          setPreferences(result);
        }
      } catch (error: unknown) {
        if (isActive) {
          setErrorMessage(
            error instanceof Error
              ? error.message
              : "Chargement impossible.",
          );
        }
      } finally {
        if (isActive) {
          setIsLoading(false);
        }
      }
    }

    void load();

    return () => {
      isActive = false;
    };
  }, []);

  const selectedCriteriaCount = useMemo(() => {
    if (preferences === null) {
      return 0;
    }

    return (
      preferences.preferred_genders.length +
      (
        preferences.advanced_filters_effective
          ? preferences.preferred_cities.length +
            preferences.preferred_dating_intents.length +
            Number(preferences.maximum_distance_km < 500) +
            Number(preferences.only_verified_profiles) +
            Number(preferences.only_profiles_with_photos)
          : 0
      )
    );
  }, [preferences]);

  async function handleSubmit(
    event: React.FormEvent<HTMLFormElement>,
  ): Promise<void> {
    event.preventDefault();

    if (preferences === null || isSaving) {
      return;
    }

    if (
      preferences.minimum_age >
      preferences.maximum_age
    ) {
      setErrorMessage(
        "L’âge minimum ne peut pas dépasser l’âge maximum.",
      );
      return;
    }

    setIsSaving(true);
    setErrorMessage("");
    setSuccessMessage("");

    try {
      const saved =
        await updateDiscoveryPreferences({
          minimum_age: preferences.minimum_age,
          maximum_age: preferences.maximum_age,
          preferred_genders:
            preferences.preferred_genders,
          ...(
            preferences.advanced_filters_available
              ? {
                  preferred_cities:
                    preferences.preferred_cities,
                  preferred_dating_intents:
                    preferences.preferred_dating_intents,
                  maximum_distance_km:
                    preferences.maximum_distance_km,
                  only_verified_profiles:
                    preferences.only_verified_profiles,
                  only_profiles_with_photos:
                    preferences.only_profiles_with_photos,
                }
              : {}
          ),
        });

      setPreferences(saved);
      setSuccessMessage(
        "Tes préférences ont été enregistrées.",
      );
    } catch (error: unknown) {
      setErrorMessage(
        error instanceof Error
          ? error.message
          : "Enregistrement impossible.",
      );
    } finally {
      setIsSaving(false);
    }
  }

  if (isLoading) {
    return (
      <main className="discovery-preferences-page">
        <section className="discovery-preferences-state">
          Chargement de tes préférences…
        </section>
      </main>
    );
  }

  if (preferences === null) {
    return (
      <main className="discovery-preferences-page">
        <section className="discovery-preferences-state">
          <h1>Préférences indisponibles</h1>
          <p>{errorMessage}</p>
          <Link to="/discovery">Retour à Découvrir</Link>
        </section>
      </main>
    );
  }

  return (
    <main className="discovery-preferences-page">
      <section className="discovery-preferences-page__header">
        <div>
          <p className="section-heading__eyebrow">
            Sélection personnalisée
          </p>

          <h1>Mes préférences</h1>

          <p>
            Ces critères restent privés et sont appliqués
            automatiquement par le moteur de découverte.
          </p>
        </div>

        <div className="discovery-preferences-page__summary">
          <strong>{selectedCriteriaCount}</strong>
          <span>critère(s) actif(s)</span>
        </div>
      </section>

      <form
        className="discovery-preferences-form"
        onSubmit={(event) => {
          void handleSubmit(event);
        }}
      >
        {errorMessage ? (
          <div
            className="discovery-preferences-form__error"
            role="alert"
          >
            {errorMessage}
          </div>
        ) : null}

        {successMessage ? (
          <div
            className="discovery-preferences-form__success"
            role="status"
          >
            {successMessage}
          </div>
        ) : null}

        <section className="discovery-preferences-section">
          <div>
            <p className="section-heading__eyebrow">
              Tranche d’âge
            </p>
            <h2>Quel âge recherches-tu ?</h2>
          </div>

          <div className="discovery-preferences-age-grid">
            <label>
              Âge minimum
              <input
                type="number"
                min={18}
                max={99}
                value={preferences.minimum_age}
                onChange={(event) => {
                  setPreferences({
                    ...preferences,
                    minimum_age: Number(
                      event.target.value,
                    ),
                  });
                }}
              />
            </label>

            <label>
              Âge maximum
              <input
                type="number"
                min={18}
                max={99}
                value={preferences.maximum_age}
                onChange={(event) => {
                  setPreferences({
                    ...preferences,
                    maximum_age: Number(
                      event.target.value,
                    ),
                  });
                }}
              />
            </label>
          </div>
        </section>

        <section className="discovery-preferences-section">
          <div>
            <p className="section-heading__eyebrow">
              Genre
            </p>
            <h2>Profils recherchés</h2>
            <p>
              Aucun choix signifie que tous les genres
              peuvent être proposés.
            </p>
          </div>

          <div className="discovery-preferences-options">
            {GENDER_OPTIONS.map((option) => (
              <label key={option.value}>
                <input
                  type="checkbox"
                  checked={
                    preferences.preferred_genders.includes(
                      option.value,
                    )
                  }
                  onChange={() => {
                    setPreferences({
                      ...preferences,
                      preferred_genders: toggleValue(
                        preferences.preferred_genders,
                        option.value,
                      ),
                    });
                  }}
                />
                <span>{option.label}</span>
              </label>
            ))}
          </div>
        </section>

        <section
          className={`discovery-preferences-section discovery-preferences-section--advanced${
            preferences.advanced_filters_available
              ? ""
              : " discovery-preferences-section--locked"
          }`}
        >
          <div>
            <p className="section-heading__eyebrow">
              Filtres avancés · Mbolo Plus
            </p>
            <h2>Villes recherchées</h2>
            <p>
              Tu peux sélectionner plusieurs villes.
            </p>
            {!preferences.advanced_filters_available ? (
              <div className="premium-filter-lock" role="note">
                <strong>Disponible avec Mbolo Plus ou Prestige</strong>
                <span>
                  Tes anciens choix sont conservés, mais ils ne filtrent
                  plus Découvrir tant que ton abonnement n’est pas actif.
                </span>
                <Link to="/premium">Découvrir les offres Premium</Link>
              </div>
            ) : null}
          </div>

          <div className="discovery-preferences-options">
            {CITY_OPTIONS.map((option) => (
              <label key={option.value}>
                <input
                  type="checkbox"
                  disabled={!preferences.advanced_filters_available}
                  checked={
                    preferences.preferred_cities.includes(
                      option.value,
                    )
                  }
                  onChange={() => {
                    setPreferences({
                      ...preferences,
                      preferred_cities: toggleValue(
                        preferences.preferred_cities,
                        option.value,
                      ),
                    });
                  }}
                />
                <span>{option.label}</span>
              </label>
            ))}
          </div>
        </section>

        <section className="discovery-preferences-section discovery-preferences-section--advanced">
          <div>
            <p className="section-heading__eyebrow">
              Proximité · Mbolo Plus
            </p>
            <h2>Distance maximale approximative</h2>
            <p>
              Mbolo compare uniquement les centres des villes déclarées.
              Ta position GPS exacte n’est ni demandée ni affichée.
            </p>
          </div>

          <label className="discovery-distance-control">
            <strong>
              Jusqu’à {preferences.maximum_distance_km} km
            </strong>
            <input
              type="range"
              min={10}
              max={500}
              step={10}
              disabled={!preferences.advanced_filters_available}
              value={preferences.maximum_distance_km}
              onChange={(event) => {
                setPreferences({
                  ...preferences,
                  maximum_distance_km: Number(event.target.value),
                });
              }}
            />
            <small>
              Distance indicative à vol d’oiseau, pas un trajet routier.
            </small>
          </label>
        </section>

        <section className="discovery-preferences-section discovery-preferences-section--advanced">
          <div>
            <p className="section-heading__eyebrow">
              Intention
            </p>
            <h2>Type de rencontre</h2>
          </div>

          <div className="discovery-preferences-options">
            {INTENT_OPTIONS.map((option) => (
              <label key={option.value}>
                <input
                  type="checkbox"
                  disabled={!preferences.advanced_filters_available}
                  checked={
                    preferences.preferred_dating_intents.includes(
                      option.value,
                    )
                  }
                  onChange={() => {
                    setPreferences({
                      ...preferences,
                      preferred_dating_intents: toggleValue(
                        preferences.preferred_dating_intents,
                        option.value,
                      ),
                    });
                  }}
                />
                <span>{option.label}</span>
              </label>
            ))}
          </div>
        </section>

        <section className="discovery-preferences-section discovery-preferences-section--advanced">
          <div>
            <p className="section-heading__eyebrow">
              Qualité des profils
            </p>
            <h2>Filtres supplémentaires</h2>
          </div>

          <div className="discovery-preferences-switches">
            <label>
              <input
                type="checkbox"
                disabled={!preferences.advanced_filters_available}
                checked={
                  preferences.only_verified_profiles
                }
                onChange={(event) => {
                  setPreferences({
                    ...preferences,
                    only_verified_profiles:
                      event.target.checked,
                  });
                }}
              />
              <span>
                <strong>Profils vérifiés uniquement</strong>
                <small>
                  Afficher seulement les profils dont le selfie a été
                  approuvé par l’équipe Mbolo.
                </small>
              </span>
            </label>

            <label>
              <input
                type="checkbox"
                disabled={!preferences.advanced_filters_available}
                checked={
                  preferences.only_profiles_with_photos
                }
                onChange={(event) => {
                  setPreferences({
                    ...preferences,
                    only_profiles_with_photos:
                      event.target.checked,
                  });
                }}
              />
              <span>
                <strong>Profils avec photo uniquement</strong>
                <small>
                  Exclure les profils qui n’ont encore publié
                  aucune photo.
                </small>
              </span>
            </label>
          </div>
        </section>

        <div className="discovery-preferences-form__actions">
          <button
            type="button"
            onClick={() => navigate("/discovery")}
          >
            Annuler
          </button>

          <button
            type="submit"
            disabled={isSaving}
          >
            {isSaving
              ? "Enregistrement…"
              : "Enregistrer les préférences"}
          </button>
        </div>
      </form>
    </main>
  );
}
