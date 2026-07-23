import { type FormEvent, useState } from "react";
import { Link } from "react-router-dom";

import { normalizeApiError } from "../../api/apiError";
import { requestPasswordReset } from "../../api/authService";

export function ForgotPasswordPage() {
  const [email, setEmail] = useState("");
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (isSubmitting) return;
    const normalizedEmail = email.trim().toLowerCase();
    if (!normalizedEmail) {
      setError("Saisis ton adresse e-mail.");
      return;
    }
    setIsSubmitting(true);
    setError("");
    try {
      await requestPasswordReset({ email: normalizedEmail });
      setMessage(
        "Si un compte éligible correspond à cette adresse, un lien vient d’être envoyé.",
      );
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
          <p>Récupération sécurisée</p>
          <h1>Mot de passe oublié</h1>
          <span>
            Reçois un lien temporaire sans révéler si ton compte existe.
          </span>
        </div>
        {message ? (
          <div className="form-alert form-alert--success" role="status">
            <span aria-hidden="true">✓</span><p>{message}</p>
          </div>
        ) : null}
        {error ? (
          <div className="form-alert form-alert--error" role="alert">
            <span aria-hidden="true">!</span><p>{error}</p>
          </div>
        ) : null}
        <form className="auth-form" onSubmit={handleSubmit} noValidate>
          <div className="form-field">
            <label htmlFor="reset-email">Adresse e-mail</label>
            <input
              id="reset-email"
              type="email"
              autoComplete="email"
              value={email}
              disabled={isSubmitting}
              onChange={(event) => {
                setEmail(event.target.value);
                setError("");
              }}
            />
          </div>
          <button className="auth-form__submit" disabled={isSubmitting}>
            {isSubmitting ? "Envoi sécurisé…" : "Envoyer le lien"}
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
