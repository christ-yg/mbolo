/**
 * Page Premium de Mbolo.
 *
 * Cette version conserve la logique métier existante :
 * - récupération de l'offre active ;
 * - activation sécurisée d'un Boost ;
 * - activation du mode discret selon les droits serveur ;
 * - affichage des moyens de paiement ;
 * - affichage des offres réellement retournées par l'API.
 *
 * La refonte corrige surtout :
 * - les contrastes insuffisants ;
 * - les titres trop sombres sur fond bordeaux ;
 * - les espaces verticaux trop importants ;
 * - la hiérarchie visuelle des offres ;
 * - le rendu mobile ;
 * - la lisibilité des avantages et des états verrouillés.
 */

import { useEffect, useMemo, useState } from "react";

import { normalizeApiError } from "../../api/apiError";
import {
  activateProfileBoost,
  getPremiumOverview,
  updatePremiumPrivacy,
} from "../../api/premiumService";
import type { PremiumOverview } from "../../types/premium";

import "./PremiumPage.css";


function formatBoostTime(value: string | null): string {
  if (!value) {
    return "";
  }

  const date = new Date(value);

  if (Number.isNaN(date.getTime())) {
    return "";
  }

  return date.toLocaleTimeString(
    "fr-FR",
    {
      hour: "2-digit",
      minute: "2-digit",
    },
  );
}


export function PremiumPage() {
  const [overview, setOverview] =
    useState<PremiumOverview | null>(null);
  const [error, setError] =
    useState("");
  const [isLoading, setIsLoading] =
    useState(true);
  const [isUpdatingPrivacy, setIsUpdatingPrivacy] =
    useState(false);
  const [isActivatingBoost, setIsActivatingBoost] =
    useState(false);


  useEffect(() => {
    let active = true;

    void getPremiumOverview()
      .then((result) => {
        if (active) {
          setOverview(result);
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


  const currentPlan = useMemo(
    () =>
      overview?.plans.find(
        (plan) =>
          plan.code === overview.subscription.plan,
      ) ?? null,
    [overview],
  );


  async function handleActivateBoost(): Promise<void> {
    if (!overview || isActivatingBoost) {
      return;
    }

    setIsActivatingBoost(true);
    setError("");

    try {
      const boost = await activateProfileBoost();

      setOverview((current) =>
        current
          ? {
              ...current,
              boost,
            }
          : current,
      );
    } catch (caught: unknown) {
      setError(normalizeApiError(caught).message);
    } finally {
      setIsActivatingBoost(false);
    }
  }


  async function handleIncognitoChange(
    enabled: boolean,
  ): Promise<void> {
    if (!overview || isUpdatingPrivacy) {
      return;
    }

    setIsUpdatingPrivacy(true);
    setError("");

    try {
      const privacy = await updatePremiumPrivacy(enabled);

      setOverview((current) =>
        current
          ? {
              ...current,
              privacy,
            }
          : current,
      );
    } catch (caught: unknown) {
      setError(normalizeApiError(caught).message);
    } finally {
      setIsUpdatingPrivacy(false);
    }
  }


  return (
    <main className="premium-redesign-page">
      <section
        className="premium-redesign-hero"
        aria-labelledby="premium-title"
      >
        <div className="premium-redesign-hero__content">
          <p className="premium-redesign-eyebrow">
            Mbolo Premium
          </p>

          <h1 id="premium-title">
            Plus de contrôle.
            <span> Plus de possibilités.</span>
          </h1>

          <p className="premium-redesign-hero__description">
            Choisis une expérience adaptée à tes besoins.
            Les paiements seront proposés en francs CFA avec
            des moyens familiers au Gabon, tandis que chaque
            droit Premium restera contrôlé côté serveur.
          </p>

          <div className="premium-redesign-hero__assurances">
            <span>✓ Paiement confirmé côté serveur</span>
            <span>✓ Aucun PIN ni CVV stocké</span>
            <span>✓ Activation impossible par simple redirection</span>
          </div>
        </div>

        <aside className="premium-redesign-current-plan">
          <p>Ton offre actuelle</p>

          <strong>
            {overview?.subscription.plan_name
              ?? "Chargement…"}
          </strong>

          <span>
            {overview?.subscription.is_premium
              ? "Abonnement Premium actif"
              : "Compte gratuit"}
          </span>

          {currentPlan ? (
            <small>{currentPlan.description}</small>
          ) : null}
        </aside>
      </section>

      {error ? (
        <div
          className="premium-redesign-alert"
          role="alert"
        >
          <span aria-hidden="true">!</span>
          <p>{error}</p>
        </div>
      ) : null}

      {isLoading ? (
        <section
          className="premium-redesign-loading"
          aria-busy="true"
        >
          <span
            className="premium-redesign-loader"
            aria-hidden="true"
          />

          <p className="premium-redesign-eyebrow">
            Vérification sécurisée
          </p>

          <h2>Chargement des offres</h2>

          <p>
            Mbolo récupère ton abonnement et les avantages
            réellement disponibles pour ton compte.
          </p>
        </section>
      ) : null}

      {overview ? (
        <>
          <section
            className="premium-redesign-plans"
            aria-labelledby="premium-plans-title"
          >
            <div className="premium-redesign-section-heading">
              <div>
                <p className="premium-redesign-eyebrow">
                  Choisir mon expérience
                </p>

                <h2 id="premium-plans-title">
                  Une offre pour chaque étape
                </h2>
              </div>

              <p>
                Les tarifs restent masqués tant que leur
                validation commerciale n’est pas terminée.
              </p>
            </div>

            <div className="premium-redesign-plan-grid">
              {overview.plans.map((plan) => {
                const isCurrent =
                  overview.subscription.plan === plan.code;

                const isPrestige =
                  plan.code === "prestige";

                const isPlus =
                  plan.code === "plus";

                return (
                  <article
                    key={plan.code}
                    className={[
                      "premium-redesign-plan-card",
                      `premium-redesign-plan-card--${plan.code}`,
                      isCurrent
                        ? "premium-redesign-plan-card--current"
                        : "",
                    ].join(" ")}
                  >
                    <div className="premium-redesign-plan-card__top">
                      <div>
                        <p className="premium-redesign-plan-card__label">
                          {plan.code === "free"
                            ? "Essentiel"
                            : isPrestige
                              ? "Expérience exclusive"
                              : "Expérience Premium"}
                        </p>

                        <h3>{plan.name}</h3>
                      </div>

                      {isCurrent ? (
                        <span className="premium-redesign-plan-card__badge">
                          Offre actuelle
                        </span>
                      ) : isPlus ? (
                        <span className="premium-redesign-plan-card__badge premium-redesign-plan-card__badge--recommended">
                          Recommandée
                        </span>
                      ) : null}
                    </div>

                    <p className="premium-redesign-plan-card__description">
                      {plan.description}
                    </p>

                    <strong className="premium-redesign-plan-card__price">
                      {plan.price_label}
                    </strong>

                    <ul>
                      {plan.features.map((feature) => (
                        <li key={feature}>
                          <span aria-hidden="true">✓</span>
                          <p>{feature}</p>
                        </li>
                      ))}
                    </ul>

                    <button
                      type="button"
                      disabled
                    >
                      {isCurrent
                        ? "Offre actuelle"
                        : plan.payment_available
                          ? "Choisir cette offre"
                          : "Bientôt disponible"}
                    </button>
                  </article>
                );
              })}
            </div>
          </section>

          <section className="premium-redesign-tools">
            <article className="premium-redesign-tool-card">
              <div className="premium-redesign-tool-card__icon">
                ↗
              </div>

              <div className="premium-redesign-tool-card__content">
                <p className="premium-redesign-eyebrow">
                  Visibilité Premium
                </p>

                <h2>
                  Boost de profil pendant{" "}
                  {overview.boost.duration_minutes} minutes
                </h2>

                <p>
                  Ton profil remonte temporairement dans
                  Découvrir auprès des membres compatibles.
                  Le Boost ne contourne jamais les filtres,
                  blocages ou règles de confidentialité.
                </p>

                <div className="premium-redesign-tool-card__meta">
                  <span>
                    {overview.boost.allowance_per_7_days}
                    {" "}activation(s) / 7 jours
                  </span>

                  <span>
                    {overview.boost.remaining}
                    {" "}restante(s)
                  </span>
                </div>
              </div>

              <button
                type="button"
                disabled={
                  isActivatingBoost
                  || overview.boost.active
                  || overview.boost.remaining <= 0
                }
                onClick={() => {
                  void handleActivateBoost();
                }}
              >
                {overview.boost.active
                  ? `Actif jusqu’à ${formatBoostTime(
                      overview.boost.active_until,
                    )}`
                  : !overview.boost.entitled
                    ? "Disponible avec Plus ou Prestige"
                    : overview.boost.remaining <= 0
                      ? "Quota temporairement épuisé"
                      : isActivatingBoost
                        ? "Activation sécurisée…"
                        : "Activer mon Boost"}
              </button>
            </article>

            <article className="premium-redesign-tool-card premium-redesign-tool-card--prestige">
              <div className="premium-redesign-tool-card__icon">
                ◇
              </div>

              <div className="premium-redesign-tool-card__content">
                <p className="premium-redesign-eyebrow">
                  Confidentialité Prestige
                </p>

                <h2>Mode discret</h2>

                <p>
                  Tes matchs ne voient ni ta présence en ligne
                  ni ta dernière activité. Les messages et
                  notifications restent disponibles normalement.
                </p>

                <small>
                  Le serveur revérifie automatiquement ton droit
                  Prestige à chaque consultation.
                </small>
              </div>

              <label className="premium-redesign-switch">
                <input
                  type="checkbox"
                  checked={
                    overview.privacy.incognito_enabled
                  }
                  disabled={
                    !overview.privacy.incognito_available
                    || isUpdatingPrivacy
                  }
                  onChange={(event) => {
                    void handleIncognitoChange(
                      event.target.checked,
                    );
                  }}
                />

                <span
                  className="premium-redesign-switch__track"
                  aria-hidden="true"
                >
                  <span />
                </span>

                <strong>
                  {overview.privacy.effective_incognito
                    ? "Mode discret actif"
                    : overview.privacy.incognito_available
                      ? "Activer le mode discret"
                      : "Réservé à Mbolo Prestige"}
                </strong>
              </label>
            </article>
          </section>

          <section
            className="premium-redesign-payments"
            aria-labelledby="premium-payment-title"
          >
            <div className="premium-redesign-section-heading">
              <div>
                <p className="premium-redesign-eyebrow">
                  Paiements au Gabon
                </p>

                <h2 id="premium-payment-title">
                  Des moyens locaux.
                  <span> Une validation rigoureuse.</span>
                </h2>
              </div>

              <p>
                Le paiement sera initié chez Mbolo puis confirmé
                directement par le serveur du prestataire.
              </p>
            </div>

            <div className="premium-redesign-payment-grid">
              {overview.payment_methods.map((method) => (
                <article key={method.code}>
                  <span
                    className="premium-redesign-payment-grid__icon"
                    aria-hidden="true"
                  >
                    {method.code === "bank_card"
                      ? "▣"
                      : "●"}
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

            <aside
              className="premium-redesign-payment-notice"
              role="note"
            >
              <span aria-hidden="true">i</span>

              <div>
                <strong>
                  Pourquoi l’encaissement est encore verrouillé ?
                </strong>

                <p>{overview.payment_notice}</p>
              </div>
            </aside>
          </section>

          <section className="premium-redesign-security">
            <div>
              <p className="premium-redesign-eyebrow">
                Protection du paiement
              </p>

              <h2>
                Ce que Mbolo ne conservera jamais
              </h2>
            </div>

            <div className="premium-redesign-security__items">
              <span>PIN Airtel ou Moov Money</span>
              <span>Code OTP</span>
              <span>Numéro complet de carte</span>
              <span>Code CVV</span>
            </div>

            <p>
              Le montant est calculé côté serveur. Chaque
              confirmation est vérifiée, journalisée et rendue
              idempotente afin d’éviter toute double activation.
            </p>
          </section>
        </>
      ) : null}
    </main>
  );
}
