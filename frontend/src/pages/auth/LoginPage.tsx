/**
 * Page de connexion sécurisée de Mbolo.
 *
 * Le formulaire utilise désormais le contexte global AuthProvider.
 *
 * Après une connexion réussie :
 *
 * - la session est créée dans Django ;
 * - l'utilisateur est enregistré dans le contexte React ;
 * - la page demandée initialement est restaurée ;
 * - sinon l'utilisateur est dirigé vers /discovery.
 */

import {
  type ChangeEvent,
  type FormEvent,
  useState,
} from "react";
import {
  Link,
  useLocation,
  useNavigate,
} from "react-router-dom";

import { normalizeApiError } from "../../api/apiError";
import { useAuth } from "../../hooks/useAuth";

import "./AuthPagesPremium.css";

/**
 * Valeurs du formulaire.
 */
interface LoginFormValues {
  email: string;
  password: string;
}

/**
 * Erreurs associées au formulaire.
 */
interface LoginFormErrors {
  email?: string;
  password?: string;
  general?: string;
}

/**
 * Données pouvant être transmises par :
 *
 * - la page d'inscription ;
 * - une route protégée.
 */
interface LoginLocationState {
  accountCreated?: boolean;
  email?: string;
  from?: string;
  passwordReset?: boolean;
}

const INITIAL_FORM_VALUES: LoginFormValues = {
  email: "",
  password: "",
};

const BASIC_EMAIL_PATTERN =
  /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

export function LoginPage() {
  const navigate = useNavigate();
  const location = useLocation();

  /**
   * Fonction login fournie par AuthProvider.
   */
  const { login, confirmTwoFactor } = useAuth();

  const locationState =
    location.state as LoginLocationState | null;

  const [formValues, setFormValues] =
    useState<LoginFormValues>({
      ...INITIAL_FORM_VALUES,

      /**
       * Préremplissage uniquement de l'adresse e-mail
       * après une inscription.
       */
      email:
        typeof locationState?.email === "string"
          ? locationState.email
          : "",
    });

  const [formErrors, setFormErrors] =
    useState<LoginFormErrors>({});

  const [isSubmitting, setIsSubmitting] =
    useState(false);

  const [isPasswordVisible, setIsPasswordVisible] =
    useState(false);
  const [challengeToken, setChallengeToken] = useState("");
  const [maskedEmail, setMaskedEmail] = useState("");
  const [twoFactorCode, setTwoFactorCode] = useState("");

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

  function validateForm(): LoginFormErrors {
    const errors: LoginFormErrors = {};

    const normalizedEmail =
      formValues.email.trim().toLowerCase();

    if (!normalizedEmail) {
      errors.email =
        "L’adresse e-mail est obligatoire.";
    } else if (
      !BASIC_EMAIL_PATTERN.test(normalizedEmail)
    ) {
      errors.email =
        "Saisis une adresse e-mail valide.";
    }

    if (!formValues.password) {
      errors.password =
        "Le mot de passe est obligatoire.";
    }

    return errors;
  }

  async function handleSubmit(
    event: FormEvent<HTMLFormElement>,
  ): Promise<void> {
    event.preventDefault();

    if (isSubmitting) {
      return;
    }

    const validationErrors = validateForm();

    if (
      Object.keys(validationErrors).length > 0
    ) {
      setFormErrors(validationErrors);

      return;
    }

    setIsSubmitting(true);
    setFormErrors({});

    try {
      const result = await login({
        email:
          formValues.email.trim().toLowerCase(),
        password: formValues.password,
      });
      if (result.requiresTwoFactor) {
        setChallengeToken(result.challengeToken);
        setMaskedEmail(result.maskedEmail);
        return;
      }

      /**
       * Si l'utilisateur avait demandé une route privée,
       * nous le renvoyons vers cette route.
       *
       * Sinon, destination par défaut : /discovery.
       */
      const destination =
        typeof locationState?.from === "string" &&
        locationState.from.startsWith("/")
          ? locationState.from
          : "/discovery";

      navigate(destination, {
        replace: true,
      });
    } catch (error: unknown) {
      const normalizedError =
        normalizeApiError(error);

      setFormErrors({
        general: normalizedError.message,
      });
    } finally {
      setIsSubmitting(false);
    }
  }

  async function handleTwoFactorSubmit(
    event: FormEvent<HTMLFormElement>,
  ): Promise<void> {
    event.preventDefault();
    if (!/^\d{6}$/.test(twoFactorCode)) {
      setFormErrors({ general: "Saisis le code à six chiffres reçu par e-mail." });
      return;
    }
    setIsSubmitting(true);
    setFormErrors({});
    try {
      await confirmTwoFactor({
        challenge_token: challengeToken,
        code: twoFactorCode,
      });
      const destination =
        typeof locationState?.from === "string" &&
        locationState.from.startsWith("/")
          ? locationState.from
          : "/discovery";
      navigate(destination, { replace: true });
    } catch (error: unknown) {
      setFormErrors({ general: normalizeApiError(error).message });
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <main className="auth-page">
      <section className="auth-page__panel">
        <div className="auth-page__intro">
          <p className="section-heading__eyebrow">
            Bon retour sur Mbolo
          </p>

          <h1>
            Retrouve les connexions qui comptent.
          </h1>

          <p>
            Connecte-toi à ton espace sécurisé pour
            découvrir tes profils recommandés, tes matchs
            et tes échanges.
          </p>

          <div className="auth-page__trust-list">
            <div>
              <span aria-hidden="true">✓</span>

              <p>
                <strong>Session sécurisée</strong>

                <small>
                  L’authentification utilise les sessions
                  Django.
                </small>
              </p>
            </div>

            <div>
              <span aria-hidden="true">✓</span>

              <p>
                <strong>
                  Protection anti-force brute
                </strong>

                <small>
                  Les tentatives répétées sont limitées
                  avec Redis.
                </small>
              </p>
            </div>

            <div>
              <span aria-hidden="true">✓</span>

              <p>
                <strong>Messages génériques</strong>

                <small>
                  Nous ne révélons pas si un compte précis
                  existe.
                </small>
              </p>
            </div>
          </div>
        </div>

        <div className="auth-card">
          <div className="auth-card__heading">
            <p>Accès à ton espace</p>

            <h2>Se connecter</h2>

            <span>
              Tu n’as pas encore de compte ?{" "}
              <Link to="/register">
                Créer un compte
              </Link>
            </span>
          </div>

          {locationState?.accountCreated ? (
            <div
              className="form-alert form-alert--success"
              role="status"
            >
              <span aria-hidden="true">✓</span>

              <p>
                Ton compte a été créé. Vérifie ton
                adresse e-mail avant de te connecter.
              </p>
            </div>
          ) : null}

          {locationState?.passwordReset ? (
            <div
              className="form-alert form-alert--success"
              role="status"
            >
              <span aria-hidden="true">✓</span>
              <p>Ton mot de passe a été modifié. Connecte-toi avec le nouveau.</p>
            </div>
          ) : null}

          {formErrors.general ? (
            <div
              className="form-alert form-alert--error"
              role="alert"
            >
              <span aria-hidden="true">!</span>

              <p>{formErrors.general}</p>
            </div>
          ) : null}

          {challengeToken ? (
          <form
            className="auth-form"
            noValidate
            onSubmit={handleTwoFactorSubmit}
          >
            <div className="form-field">
              <label htmlFor="login-two-factor-code">
                Code temporaire
              </label>
              <p>
                Saisis le code envoyé à {maskedEmail}. Il expire dans 10 minutes.
              </p>
              <input
                id="login-two-factor-code"
                type="text"
                inputMode="numeric"
                autoComplete="one-time-code"
                maxLength={6}
                value={twoFactorCode}
                disabled={isSubmitting}
                onChange={(event) =>
                  setTwoFactorCode(
                    event.target.value.replace(/\D/g, "").slice(0, 6),
                  )
                }
              />
            </div>
            <button
              className="auth-form__submit"
              type="submit"
              disabled={isSubmitting}
            >
              {isSubmitting ? "Vérification…" : "Confirmer la connexion"}
            </button>
            <button
              type="button"
              disabled={isSubmitting}
              onClick={() => {
                setChallengeToken("");
                setTwoFactorCode("");
                setFormErrors({});
              }}
            >
              Revenir à la connexion
            </button>
          </form>
          ) : (
          <form
            className="auth-form"
            noValidate
            onSubmit={handleSubmit}
          >
            <div className="form-field">
              <label htmlFor="login-email">
                Adresse e-mail
              </label>

              <input
                id="login-email"
                name="email"
                type="email"
                autoComplete="email"
                inputMode="email"
                maxLength={254}
                placeholder="exemple@email.com"
                value={formValues.email}
                aria-invalid={Boolean(
                  formErrors.email,
                )}
                aria-describedby={
                  formErrors.email
                    ? "login-email-error"
                    : undefined
                }
                disabled={isSubmitting}
                onChange={handleInputChange}
              />

              {formErrors.email ? (
                <p
                  id="login-email-error"
                  className="form-field__error"
                  role="alert"
                >
                  {formErrors.email}
                </p>
              ) : null}
            </div>

            <div className="form-field">
              <div className="form-field__label-row">
                <label htmlFor="login-password">
                  Mot de passe
                </label>

                <Link
                  className="form-field__forgot-link"
                  to="/forgot-password"
                >
                  Mot de passe oublié ?
                </Link>
              </div>

              <div className="password-input">
                <input
                  id="login-password"
                  name="password"
                  type={
                    isPasswordVisible
                      ? "text"
                      : "password"
                  }
                  autoComplete="current-password"
                  maxLength={128}
                  placeholder="Ton mot de passe"
                  value={formValues.password}
                  aria-invalid={Boolean(
                    formErrors.password,
                  )}
                  aria-describedby={
                    formErrors.password
                      ? "login-password-error"
                      : undefined
                  }
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
                      (currentValue) =>
                        !currentValue,
                    )
                  }
                >
                  {isPasswordVisible
                    ? "Masquer"
                    : "Afficher"}
                </button>
              </div>

              {formErrors.password ? (
                <p
                  id="login-password-error"
                  className="form-field__error"
                  role="alert"
                >
                  {formErrors.password}
                </p>
              ) : null}
            </div>

            <button
              className="auth-form__submit"
              type="submit"
              disabled={isSubmitting}
            >
              {isSubmitting
                ? "Connexion sécurisée…"
                : "Se connecter"}

              {!isSubmitting ? (
                <span aria-hidden="true">→</span>
              ) : null}
            </button>

            <p className="auth-form__security-note">
              La session est conservée dans un cookie
              Django. Aucun mot de passe n’est enregistré
              dans le navigateur.
            </p>

            <p className="auth-form__security-note">
              Ton compte fait l’objet d’une sanction ?{" "}
              <Link to="/sanction-appeal">
                Demander une révision
              </Link>
            </p>
          </form>
          )}
        </div>
      </section>
    </main>
  );
}
