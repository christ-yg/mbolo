import { type FormEvent, useState } from "react";
import { Link } from "react-router-dom";

import { normalizeApiError } from "../../api/apiError";
import { submitSanctionAppeal } from "../../api/sanctionAppealService";

import "./AuthPagesPremium.css";

export function SanctionAppealPage() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (isSubmitting) return;

    if (message.trim().length < 30) {
      setError("Explique ta demande en au moins 30 caractères.");
      return;
    }

    setIsSubmitting(true);
    setError("");
    setSuccess("");
    try {
      const result = await submitSanctionAppeal({
        email: email.trim().toLowerCase(),
        password,
        message: message.trim(),
      });
      setSuccess(result.message);
      setPassword("");
      setMessage("");
    } catch (caughtError: unknown) {
      setError(normalizeApiError(caughtError).message);
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <main className="appeal-page">
      <section className="appeal-page__intro">
        <p className="section-heading__eyebrow">Révision équitable</p>
        <h1>Contester une sanction</h1>
        <p>
          Ce formulaire est réservé au membre sanctionné. Tes identifiants
          servent uniquement à confirmer ton identité et ne sont jamais
          enregistrés dans la contestation.
        </p>
      </section>

      <section className="appeal-card">
        <div>
          <h2>Explique calmement la situation</h2>
          <p>
            Donne les faits utiles. L’identité du modérateur, celle de la
            personne ayant signalé et les notes internes restent protégées.
          </p>
        </div>

        {error ? <div className="form-alert form-alert--error" role="alert">{error}</div> : null}
        {success ? <div className="form-alert form-alert--success" role="status">{success}</div> : null}

        <form className="auth-form" onSubmit={handleSubmit}>
          <div className="form-field">
            <label htmlFor="appeal-email">Adresse e-mail</label>
            <input
              id="appeal-email"
              type="email"
              required
              maxLength={254}
              autoComplete="email"
              value={email}
              disabled={isSubmitting}
              onChange={(event) => setEmail(event.target.value)}
            />
          </div>
          <div className="form-field">
            <label htmlFor="appeal-password">Mot de passe actuel</label>
            <input
              id="appeal-password"
              type="password"
              required
              maxLength={128}
              autoComplete="current-password"
              value={password}
              disabled={isSubmitting}
              onChange={(event) => setPassword(event.target.value)}
            />
          </div>
          <div className="form-field">
            <label htmlFor="appeal-message">Ta contestation</label>
            <textarea
              id="appeal-message"
              required
              minLength={30}
              maxLength={2000}
              rows={8}
              value={message}
              disabled={isSubmitting}
              onChange={(event) => setMessage(event.target.value)}
            />
            <small>{message.length}/2000 caractères</small>
          </div>
          <button className="auth-form__submit" type="submit" disabled={isSubmitting}>
            {isSubmitting ? "Transmission sécurisée…" : "Envoyer ma contestation"}
          </button>
          <p className="auth-form__security-note">
            Une seule contestation est autorisée par sanction.
          </p>
        </form>

        <Link className="appeal-card__back" to="/login">← Retour à la connexion</Link>
      </section>
    </main>
  );
}
