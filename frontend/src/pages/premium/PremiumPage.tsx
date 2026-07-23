import { useEffect, useState } from "react";

import { normalizeApiError } from "../../api/apiError";
import { getPremiumOverview } from "../../api/premiumService";
import type { PremiumOverview } from "../../types/premium";


export function PremiumPage() {
  const [overview, setOverview] = useState<PremiumOverview | null>(null);
  const [error, setError] = useState("");

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
