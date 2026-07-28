import { type FormEvent, useState } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";

import { normalizeApiError } from "../../api/apiError";
import { confirmPasswordReset } from "../../api/authService";

import "./AuthPagesPremium.css";

export function ResetPasswordPage() {
  const [params] = useSearchParams();
  const navigate = useNavigate();
  const [password, setPassword] = useState("");
  const [confirmation, setConfirmation] = useState("");
  const [error, setError] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const uid = params.get("uid") ?? "";
  const token = params.get("token") ?? "";

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (isSubmitting) return;
    if (!uid || !token) {
      setError("Ce lien de réinitialisation est incomplet.");
      return;
    }
    if (password.length < 12) {
      setError("Utilise au moins 12 caractères.");
      return;
    }
    if (password !== confirmation) {
      setError("Les deux mots de passe ne correspondent pas.");
      return;
    }
    setIsSubmitting(true);
    setError("");
    try {
      await confirmPasswordReset({
        uid,
        token,
        password,
        password_confirmation: confirmation,
      });
      navigate("/login", {
        replace: true,
        state: { passwordReset: true },
      });
    } catch (caught: unknown) {
      setError(normalizeApiError(caught).message);
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <main className="auth-page auth-page--single">
      <section className="auth-card auth-card--reset">
        <div className="auth-card__heading">
          <p>Nouveau secret</p>
          <h1>Choisis ton nouveau mot de passe</h1>
          <span>Le lien est temporaire et ne fonctionne qu’une fois.</span>
        </div>
        {error ? (
          <div className="form-alert form-alert--error" role="alert">
            <span aria-hidden="true">!</span><p>{error}</p>
          </div>
        ) : null}
        <form className="auth-form" onSubmit={handleSubmit} noValidate>
          <div className="form-field">
            <label htmlFor="new-password">Nouveau mot de passe</label>
            <input
              id="new-password"
              type="password"
              autoComplete="new-password"
              value={password}
              maxLength={128}
              onChange={(event) => setPassword(event.target.value)}
            />
          </div>
          <div className="form-field">
            <label htmlFor="new-password-confirmation">Confirmation</label>
            <input
              id="new-password-confirmation"
              type="password"
              autoComplete="new-password"
              value={confirmation}
              maxLength={128}
              onChange={(event) => setConfirmation(event.target.value)}
            />
          </div>
          <button className="auth-form__submit" disabled={isSubmitting}>
            {isSubmitting ? "Modification…" : "Modifier mon mot de passe"}
            {!isSubmitting ? <span aria-hidden="true">→</span> : null}
          </button>
          <p className="auth-form__security-note">
            <Link to="/login">← Retour à la connexion</Link>
          </p>
        </form>
      </section>
    </main>
  );
}
