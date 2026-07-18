/**
 * Page d'inscription sécurisée de Mbolo.
 *
 * Responsabilités :
 *
 * - collecter les informations d'inscription ;
 * - effectuer des validations ergonomiques côté navigateur ;
 * - transmettre les données au backend Django ;
 * - envoyer le jeton CSRF ;
 * - afficher les erreurs retournées par l'API ;
 * - empêcher plusieurs soumissions simultanées.
 *
 * Important :
 * la validation frontend améliore l'expérience utilisateur,
 * mais le backend Django reste l'autorité de sécurité finale.
 */

import {
  type ChangeEvent,
  type FormEvent,
  useMemo,
  useState,
} from "react";
import { Link, useNavigate } from "react-router-dom";

import { normalizeApiError } from "../../api/apiError";
import { registerUser } from "../../api/authService";

/**
 * Données locales contrôlées par le formulaire.
 */
interface RegisterFormValues {
  email: string;
  password: string;
  passwordConfirmation: string;
}

/**
 * Erreurs frontend ou backend associées aux champs.
 */
interface RegisterFormErrors {
  email?: string;
  password?: string;
  passwordConfirmation?: string;
  general?: string;
}

/**
 * Valeurs initiales centralisées.
 *
 * Nous évitons de recréer cette structure dans plusieurs endroits.
 */
const INITIAL_FORM_VALUES: RegisterFormValues = {
  email: "",
  password: "",
  passwordConfirmation: "",
};

/**
 * Expression volontairement simple pour détecter les erreurs
 * évidentes de format.
 *
 * Django effectuera ensuite la validation complète côté serveur.
 */
const BASIC_EMAIL_PATTERN = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

/**
 * Longueur minimale ergonomique du mot de passe.
 *
 * Les validateurs Django appliquent toujours les exigences
 * définitives du projet.
 */
const MINIMUM_PASSWORD_LENGTH = 12;

/**
 * Mesure la progression visuelle du mot de passe.
 *
 * Ce calcul ne remplace pas les validateurs de sécurité Django.
 */
function calculatePasswordStrength(password: string): number {
  let score = 0;

  if (password.length >= MINIMUM_PASSWORD_LENGTH) {
    score += 1;
  }

  if (/[a-z]/.test(password) && /[A-Z]/.test(password)) {
    score += 1;
  }

  if (/\d/.test(password)) {
    score += 1;
  }

  if (/[^a-zA-Z0-9]/.test(password)) {
    score += 1;
  }

  return score;
}

/**
 * Retourne un libellé compréhensible pour l'utilisateur.
 */
function getPasswordStrengthLabel(score: number): string {
  switch (score) {
    case 4:
      return "Très robuste";

    case 3:
      return "Robuste";

    case 2:
      return "Moyen";

    case 1:
      return "Faible";

    default:
      return "À renforcer";
  }
}

export function RegisterPage() {
  const navigate = useNavigate();

  /**
   * Valeurs saisies dans les trois champs.
   */
  const [formValues, setFormValues] =
    useState<RegisterFormValues>(INITIAL_FORM_VALUES);

  /**
   * Erreurs actuellement affichées.
   */
  const [formErrors, setFormErrors] =
    useState<RegisterFormErrors>({});

  /**
   * Empêche une nouvelle soumission pendant l'appel réseau.
   */
  const [isSubmitting, setIsSubmitting] = useState(false);

  /**
   * Permet d'afficher ou masquer le mot de passe.
   */
  const [isPasswordVisible, setIsPasswordVisible] =
    useState(false);

  /**
   * Calcul mémorisé de la robustesse.
   *
   * Le calcul n'est refait que lorsque le mot de passe change.
   */
  const passwordStrength = useMemo(
    () => calculatePasswordStrength(formValues.password),
    [formValues.password],
  );

  /**
   * Met à jour un champ contrôlé.
   *
   * L'erreur du champ concerné est supprimée dès que
   * l'utilisateur reprend sa saisie.
   */
  function handleInputChange(
    event: ChangeEvent<HTMLInputElement>,
  ): void {
    const { name, value } = event.target;

    setFormValues((currentValues) => ({
      ...currentValues,
      [name]: value,
    }));

    setFormErrors((currentErrors) => ({
      ...currentErrors,
      [name]: undefined,
      general: undefined,
    }));
  }

  /**
   * Effectue les contrôles ergonomiques avant l'appel à Django.
   *
   * Le backend refera impérativement toutes les validations.
   */
  function validateForm(): RegisterFormErrors {
    const errors: RegisterFormErrors = {};

    const normalizedEmail = formValues.email
      .trim()
      .toLowerCase();

    if (!normalizedEmail) {
      errors.email = "L’adresse e-mail est obligatoire.";
    } else if (!BASIC_EMAIL_PATTERN.test(normalizedEmail)) {
      errors.email = "Saisis une adresse e-mail valide.";
    }

    if (!formValues.password) {
      errors.password = "Le mot de passe est obligatoire.";
    } else if (
      formValues.password.length < MINIMUM_PASSWORD_LENGTH
    ) {
      errors.password =
        `Utilise au moins ${MINIMUM_PASSWORD_LENGTH} caractères.`;
    }

    if (!formValues.passwordConfirmation) {
      errors.passwordConfirmation =
        "Confirme ton mot de passe.";
    } else if (
      formValues.password !==
      formValues.passwordConfirmation
    ) {
      errors.passwordConfirmation =
        "Les deux mots de passe ne correspondent pas.";
    }

    return errors;
  }

  /**
   * Envoie le formulaire d'inscription.
   */
  async function handleSubmit(
    event: FormEvent<HTMLFormElement>,
  ): Promise<void> {
    event.preventDefault();

    /**
     * Protection complémentaire contre les doubles clics.
     */
    if (isSubmitting) {
      return;
    }

    const validationErrors = validateForm();

    if (Object.keys(validationErrors).length > 0) {
      setFormErrors(validationErrors);
      return;
    }

    setIsSubmitting(true);
    setFormErrors({});

    try {
      await registerUser({
        email: formValues.email.trim().toLowerCase(),
        password: formValues.password,

        /**
         * Le backend Django attend actuellement ce nom exact.
         */
        password_confirmation:
          formValues.passwordConfirmation,
      });

      /**
       * Le compte est créé, mais l'adresse doit encore être
       * vérifiée avant l'utilisation complète du service.
       *
       * Nous transmettons l'e-mail uniquement dans l'état
       * de navigation, pas dans l'URL.
       */
      navigate("/login", {
        replace: true,
        state: {
          accountCreated: true,
          email: formValues.email.trim().toLowerCase(),
        },
      });
    } catch (error: unknown) {
      const normalizedError = normalizeApiError(error);

      /**
       * Adaptation des noms de champs Django vers ceux
       * utilisés dans le composant React.
       */
      const backendFieldErrors =
        normalizedError.fieldErrors;

      setFormErrors({
        email:
          backendFieldErrors.email?.[0],

        password:
          backendFieldErrors.password?.[0],

        passwordConfirmation:
          backendFieldErrors.password_confirmation?.[0],

        general: normalizedError.message,
      });
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <main className="auth-page">
      <section className="auth-page__panel">
        <div className="auth-page__intro">
          <p className="section-heading__eyebrow">
            Nouvelle inscription
          </p>

          <h1>Crée ton espace Mbolo.</h1>

          <p>
            Rejoins une communauté adulte fondée sur
            l’authenticité, le respect et la sécurité.
          </p>

          <div className="auth-page__trust-list">
            <div>
              <span aria-hidden="true">✓</span>

              <p>
                <strong>Adresse vérifiée</strong>
                <small>
                  Chaque nouveau compte confirme son e-mail.
                </small>
              </p>
            </div>

            <div>
              <span aria-hidden="true">✓</span>

              <p>
                <strong>Protection anti-abus</strong>
                <small>
                  Les tentatives automatisées sont limitées.
                </small>
              </p>
            </div>

            <div>
              <span aria-hidden="true">✓</span>

              <p>
                <strong>Données minimisées</strong>
                <small>
                  Nous collectons uniquement le nécessaire.
                </small>
              </p>
            </div>
          </div>
        </div>

        <div className="auth-card">
          <div className="auth-card__heading">
            <p>Commence ton expérience</p>

            <h2>Créer un compte</h2>

            <span>
              Tu possèdes déjà un compte ?{" "}
              <Link to="/login">Se connecter</Link>
            </span>
          </div>

          {formErrors.general ? (
            <div
              className="form-alert form-alert--error"
              role="alert"
            >
              <span aria-hidden="true">!</span>

              <p>{formErrors.general}</p>
            </div>
          ) : null}

          <form
            className="auth-form"
            noValidate
            onSubmit={handleSubmit}
          >
            <div className="form-field">
              <label htmlFor="register-email">
                Adresse e-mail
              </label>

              <input
                id="register-email"
                name="email"
                type="email"
                autoComplete="email"
                inputMode="email"
                maxLength={254}
                placeholder="exemple@email.com"
                value={formValues.email}
                aria-invalid={Boolean(formErrors.email)}
                aria-describedby={
                  formErrors.email
                    ? "register-email-error"
                    : undefined
                }
                disabled={isSubmitting}
                onChange={handleInputChange}
              />

              {formErrors.email ? (
                <p
                  id="register-email-error"
                  className="form-field__error"
                  role="alert"
                >
                  {formErrors.email}
                </p>
              ) : null}
            </div>

            <div className="form-field">
              <label htmlFor="register-password">
                Mot de passe
              </label>

              <div className="password-input">
                <input
                  id="register-password"
                  name="password"
                  type={
                    isPasswordVisible
                      ? "text"
                      : "password"
                  }
                  autoComplete="new-password"
                  maxLength={128}
                  placeholder="12 caractères minimum"
                  value={formValues.password}
                  aria-invalid={Boolean(
                    formErrors.password,
                  )}
                  aria-describedby="register-password-help"
                  disabled={isSubmitting}
                  onChange={handleInputChange}
                />

                <button
                  type="button"
                  className="password-input__toggle"
                  aria-label={
                    isPasswordVisible
                      ? "Masquer le mot de passe"
                      : "Afficher le mot de passe"
                  }
                  aria-pressed={isPasswordVisible}
                  disabled={isSubmitting}
                  onClick={() =>
                    setIsPasswordVisible(
                      (currentValue) => !currentValue,
                    )
                  }
                >
                  {isPasswordVisible ? "Masquer" : "Afficher"}
                </button>
              </div>

              <div
                id="register-password-help"
                className="password-strength"
              >
                <div
                  className="password-strength__bars"
                  aria-hidden="true"
                >
                  {[1, 2, 3, 4].map((level) => (
                    <span
                      key={level}
                      className={
                        level <= passwordStrength
                          ? "password-strength__bar password-strength__bar--active"
                          : "password-strength__bar"
                      }
                    />
                  ))}
                </div>

                <small>
                  Robustesse :{" "}
                  {getPasswordStrengthLabel(
                    passwordStrength,
                  )}
                </small>
              </div>

              {formErrors.password ? (
                <p
                  className="form-field__error"
                  role="alert"
                >
                  {formErrors.password}
                </p>
              ) : null}
            </div>

            <div className="form-field">
              <label htmlFor="register-password-confirmation">
                Confirmation du mot de passe
              </label>

              <input
                id="register-password-confirmation"
                name="passwordConfirmation"
                type={
                  isPasswordVisible
                    ? "text"
                    : "password"
                }
                autoComplete="new-password"
                maxLength={128}
                placeholder="Saisis à nouveau le mot de passe"
                value={formValues.passwordConfirmation}
                aria-invalid={Boolean(
                  formErrors.passwordConfirmation,
                )}
                aria-describedby={
                  formErrors.passwordConfirmation
                    ? "register-password-confirmation-error"
                    : undefined
                }
                disabled={isSubmitting}
                onChange={handleInputChange}
              />

              {formErrors.passwordConfirmation ? (
                <p
                  id="register-password-confirmation-error"
                  className="form-field__error"
                  role="alert"
                >
                  {formErrors.passwordConfirmation}
                </p>
              ) : null}
            </div>

            <label className="legal-confirmation">
              <input
                name="legalConfirmation"
                type="checkbox"
                required
                disabled={isSubmitting}
              />

              <span>
                Je confirme avoir au moins 18 ans et accepter
                les futures conditions d’utilisation ainsi que
                la politique de confidentialité.
              </span>
            </label>

            <button
              className="auth-form__submit"
              type="submit"
              disabled={isSubmitting}
            >
              {isSubmitting
                ? "Création sécurisée…"
                : "Créer mon compte"}

              {!isSubmitting ? (
                <span aria-hidden="true">→</span>
              ) : null}
            </button>

            <p className="auth-form__security-note">
              Tes informations sont transmises à Django avec
              une protection CSRF et une connexion locale
              contrôlée.
            </p>
          </form>
        </div>
      </section>
    </main>
  );
}
