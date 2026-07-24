import { useEffect, useState } from "react";

import { normalizeApiError } from "../../api/apiError";
import {
  getPremiumOverview,
  updatePremiumPrivacy,
  activateProfileBoost,
} from "../../api/premiumService";
import type { PremiumOverview } from "../../types/premium";


export function PremiumPage() {
  const [overview, setOverview] = useState<PremiumOverview | null>(null);
  const [error, setError] = useState("");
  const [isUpdatingPrivacy, setIsUpdatingPrivacy] = useState(false);
  const [isActivatingBoost, setIsActivatingBoost] = useState(false);

  async function handleActivateBoost(): Promise<void> {
    if (!overview || isActivatingBoost) return;
    setIsActivatingBoost(true);
    setError("");
    try {
      const boost = await activateProfileBoost();
      setOverview((current) => current ? { ...current, boost } : current);
    } catch (caught: unknown) {
      setError(normalizeApiError(caught).message);
    } finally {
      setIsActivatingBoost(false);
    }
  }

  async function handleIncognitoChange(enabled: boolean): Promise<void> {
    if (!overview || isUpdatingPrivacy) return;

    setIsUpdatingPrivacy(true);
    setError("");

    try {
      const privacy = await updatePremiumPrivacy(enabled);
      setOverview((current) => (
        current ? { ...current, privacy } : current
      ));
    } catch (caught: unknown) {
      setError(normalizeApiError(caught).message);
    } finally {
      setIsUpdatingPrivacy(false);
    }
  }

  useEffect(() => {
    let active = true;
    void getPremiumOverview()
      .then((result) => {
        if (active) setOverview(result);
      })
      .catch((caught: unknown) => {
        if (active) setError(normalizeApiError(caught).message);
      });
    return () => {
      active = false;
    };
  }, []);

  return (
    <main className="premium-page">
      <section className="premium-page__hero">
        <p className="section-heading__eyebrow">Mbolo Premium</p>
        <h1>Plus de contrôle. Plus de possibilités.</h1>
        <p>
          Choisis une expérience adaptée à tes besoins. Les paiements seront
          proposés en francs CFA avec les moyens familiers au Gabon, tandis
          que les droits Premium resteront contrôlés exclusivement par le
          serveur Mbolo.
        </p>
        {overview ? (
          <div className="premium-current-plan">
            <span>Ton offre actuelle</span>
            <strong>{overview.subscription.plan_name}</strong>
            <small>
              {overview.subscription.is_premium
                ? "Abonnement actif"
                : "Compte gratuit"}
            </small>
          </div>
        ) : null}
      </section>

      {error ? (
        <div className="form-alert form-alert--error" role="alert">
          <span aria-hidden="true">!</span><p>{error}</p>
        </div>
      ) : null}

      {!overview && !error ? (
        <p className="premium-page__loading" role="status">
          Chargement sécurisé des offres…
        </p>
      ) : null}

      {overview ? (
        <section className="premium-plan-grid" aria-label="Offres Mbolo">
          {overview.plans.map((plan) => {
            const isCurrent =
              overview.subscription.plan === plan.code;
            return (
              <article
                className={`premium-plan-card premium-plan-card--${plan.code}`}
                key={plan.code}
              >
                <p className="section-heading__eyebrow">
                  {plan.code === "free" ? "Essentiel" : "Expérience Premium"}
                </p>
                <h2>{plan.name}</h2>
                <p>{plan.description}</p>
                <strong className="premium-plan-card__price">
                  {plan.price_label}
                </strong>
                <ul>
                  {plan.features.map((feature) => (
                    <li key={feature}>
                      <span aria-hidden="true">✓</span>
                      {feature}
                    </li>
                  ))}
                </ul>
                <button type="button" disabled>
                  {isCurrent
                    ? "Offre actuelle"
                    : plan.payment_available
                      ? "Choisir cette offre"
                      : "Bientôt disponible"}
                </button>
              </article>
            );
          })}
        </section>
      ) : null}

      {overview ? (
        <section className="premium-boost">
          <div>
            <p className="section-heading__eyebrow">Visibilité Premium</p>
            <h2>Boost de profil pendant {overview.boost.duration_minutes} minutes</h2>
            <p>
              Ton profil remonte temporairement dans Découvrir auprès des
              membres compatibles. Le Boost ne contourne jamais leurs filtres,
              les blocages, la vérification du compte ou la confidentialité.
            </p>
            <small>
              {overview.boost.allowance_per_7_days} activation(s) par période
              de 7 jours · {overview.boost.remaining} restante(s).
            </small>
          </div>
          <button
            type="button"
            className="premium-boost__button"
            disabled={
              isActivatingBoost ||
              overview.boost.active ||
              overview.boost.remaining <= 0
            }
            onClick={() => { void handleActivateBoost(); }}
          >
            {overview.boost.active
              ? `Boost actif jusqu’à ${new Date(overview.boost.active_until ?? "").toLocaleTimeString("fr-FR", { hour: "2-digit", minute: "2-digit" })}`
              : !overview.boost.entitled
                ? "Disponible avec Plus ou Prestige"
                : overview.boost.remaining <= 0
                  ? "Quota temporairement épuisé"
                  : isActivatingBoost
                    ? "Activation sécurisée…"
                    : "Activer mon Boost"}
          </button>
        </section>
      ) : null}

      {overview ? (
        <section className="premium-incognito">
          <div>
            <p className="section-heading__eyebrow">Confidentialité Prestige</p>
            <h2>Mode discret</h2>
            <p>
              Lorsque ce mode est actif, tes matchs ne voient ni ta présence
              en ligne ni ta dernière activité. Tu continues néanmoins à
              recevoir tes messages et notifications normalement.
            </p>
          </div>
          <label className="premium-incognito__control">
            <input
              type="checkbox"
              checked={overview.privacy.incognito_enabled}
              disabled={
                !overview.privacy.incognito_available ||
                isUpdatingPrivacy
              }
              onChange={(event) => {
                void handleIncognitoChange(event.target.checked);
              }}
            />
            <span>
              {overview.privacy.effective_incognito
                ? "Mode discret actif"
                : overview.privacy.incognito_available
                  ? "Activer le mode discret"
                  : "Réservé à Mbolo Prestige"}
            </span>
          </label>
          <small>
            La disponibilité est revérifiée par Django à chaque consultation.
            Une expiration de Prestige désactive automatiquement son effet.
          </small>
        </section>
      ) : null}

      {overview ? (
        <section className="premium-payment-section">
          <div className="premium-payment-section__intro">
            <p className="section-heading__eyebrow">Paiements au Gabon</p>
            <h2>Des moyens locaux, une validation rigoureuse.</h2>
            <p>
              Le paiement sera initié chez Mbolo puis confirmé par le serveur
              du prestataire. Une simple redirection du navigateur ne pourra
              jamais activer un abonnement.
            </p>
          </div>
          <div className="premium-payment-methods">
            {overview.payment_methods.map((method) => (
              <article key={method.code}>
                <span aria-hidden="true">
                  {method.code === "bank_card" ? "▣" : "●"}
                </span>
                <div>
                  <h3>{method.name}</h3>
                  <p>{method.description}</p>
                  <small>
                    {method.available
                      ? "Disponible"
                      : "Activation après validation du partenaire marchand"}
                  </small>
                </div>
              </article>
            ))}
          </div>
          <div className="premium-payment-notice" role="note">
            <strong>Pourquoi l’encaissement est encore verrouillé ?</strong>
            <p>{overview.payment_notice}</p>
          </div>
        </section>
      ) : null}

      <section className="premium-page__security">
        <h2>Ce que Mbolo protège pendant un paiement</h2>
        <p>
          Aucun PIN Airtel ou Moov Money, aucun OTP, aucun numéro complet de
          carte et aucun CVV ne seront enregistrés. Le montant sera calculé
          côté serveur et chaque confirmation sera vérifiée, journalisée et
          rendue idempotente afin d’éviter les doubles activations.
        </p>
      </section>
    </main>
  );
}
