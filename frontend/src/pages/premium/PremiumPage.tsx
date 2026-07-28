import { useEffect, useMemo, useState } from "react";

import { normalizeApiError } from "../../api/apiError";
import {
  activateProfileBoost,
  cancelPremiumPayment,
  confirmPremiumPaymentTest,
  createPremiumCheckout,
  getPremiumOverview,
  getPremiumPaymentHistory,
  updatePremiumPrivacy,
} from "../../api/premiumService";
import type {
  PremiumOverview,
  PremiumPaymentMethod,
  PremiumPaymentTransaction,
} from "../../types/premium";

import "./PremiumPage.css";


function formatBoostTime(value: string | null): string {
  if (!value) return "";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "";
  return date.toLocaleTimeString("fr-FR", {
    hour: "2-digit",
    minute: "2-digit",
  });
}


function formatMoney(value: number): string {
  return new Intl.NumberFormat("fr-FR").format(value);
}


function formatDate(value: string): string {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleString("fr-FR", {
    dateStyle: "medium",
    timeStyle: "short",
  });
}


export function PremiumPage() {
  const [overview, setOverview] = useState<PremiumOverview | null>(null);
  const [error, setError] = useState("");
  const [isLoading, setIsLoading] = useState(true);
  const [isUpdatingPrivacy, setIsUpdatingPrivacy] = useState(false);
  const [isActivatingBoost, setIsActivatingBoost] = useState(false);
  const [selectedPlan, setSelectedPlan] = useState<"plus" | "prestige" | null>(null);
  const [selectedMethod, setSelectedMethod] =
    useState<PremiumPaymentMethod["code"]>("airtel_money");
  const [transaction, setTransaction] =
    useState<PremiumPaymentTransaction | null>(null);
  const [history, setHistory] = useState<PremiumPaymentTransaction[]>([]);
  const [isPaymentBusy, setIsPaymentBusy] = useState(false);
  const [paymentMessage, setPaymentMessage] = useState("");

  async function loadOverview(): Promise<void> {
    const result = await getPremiumOverview();
    setOverview(result);
  }

  async function loadHistory(): Promise<void> {
    const result = await getPremiumPaymentHistory();
    setHistory(result.transactions);
  }

  useEffect(() => {
    let active = true;

    Promise.all([getPremiumOverview(), getPremiumPaymentHistory()])
      .then(([premiumResult, historyResult]) => {
        if (!active) return;
        setOverview(premiumResult);
        setHistory(historyResult.transactions);
      })
      .catch((caught: unknown) => {
        if (active) setError(normalizeApiError(caught).message);
      })
      .finally(() => {
        if (active) setIsLoading(false);
      });

    return () => {
      active = false;
    };
  }, []);

  const currentPlan = useMemo(
    () =>
      overview?.plans.find(
        (plan) => plan.code === overview.subscription.plan,
      ) ?? null,
    [overview],
  );

  const checkoutPlan = useMemo(
    () =>
      overview?.plans.find((plan) => plan.code === selectedPlan) ?? null,
    [overview, selectedPlan],
  );

  async function handleActivateBoost(): Promise<void> {
    if (!overview || isActivatingBoost) return;
    setIsActivatingBoost(true);
    setError("");

    try {
      const boost = await activateProfileBoost();
      setOverview((current) =>
        current ? { ...current, boost } : current,
      );
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
      setOverview((current) =>
        current ? { ...current, privacy } : current,
      );
    } catch (caught: unknown) {
      setError(normalizeApiError(caught).message);
    } finally {
      setIsUpdatingPrivacy(false);
    }
  }

  async function handleCreateCheckout(): Promise<void> {
    if (!selectedPlan || isPaymentBusy) return;
    setIsPaymentBusy(true);
    setError("");
    setPaymentMessage("");

    try {
      const result = await createPremiumCheckout(
        selectedPlan,
        selectedMethod,
      );
      setTransaction(result);
      setPaymentMessage(
        "Transaction créée côté serveur. Aucun argent réel n'a été débité.",
      );
      await loadHistory();
    } catch (caught: unknown) {
      setError(normalizeApiError(caught).message);
    } finally {
      setIsPaymentBusy(false);
    }
  }

  async function handleConfirmTestPayment(): Promise<void> {
    if (!transaction || isPaymentBusy) return;
    setIsPaymentBusy(true);
    setError("");

    try {
      const result = await confirmPremiumPaymentTest(transaction.id);
      setTransaction(result.transaction);
      setPaymentMessage(
        `Paiement test confirmé. ${result.subscription.plan_name} est maintenant actif.`,
      );
      await Promise.all([loadOverview(), loadHistory()]);
    } catch (caught: unknown) {
      setError(normalizeApiError(caught).message);
    } finally {
      setIsPaymentBusy(false);
    }
  }

  async function handleCancelPayment(): Promise<void> {
    if (!transaction || isPaymentBusy) return;
    setIsPaymentBusy(true);
    setError("");

    try {
      const result = await cancelPremiumPayment(transaction.id);
      setTransaction(result);
      setPaymentMessage("Transaction annulée sans activation d'abonnement.");
      await loadHistory();
    } catch (caught: unknown) {
      setError(normalizeApiError(caught).message);
    } finally {
      setIsPaymentBusy(false);
    }
  }

  return (
    <main className="premium-redesign-page">
      <section className="premium-redesign-hero" aria-labelledby="premium-title">
        <div className="premium-redesign-hero__content">
          <p className="premium-redesign-eyebrow">Mbolo Premium</p>
          <h1 id="premium-title">
            Plus de contrôle.
            <span> Plus de possibilités.</span>
          </h1>
          <p className="premium-redesign-hero__description">
            Choisis une expérience adaptée à tes besoins. Les montants,
            droits et activations sont toujours vérifiés côté serveur.
          </p>
          <div className="premium-redesign-hero__assurances">
            <span>✓ Montant calculé côté serveur</span>
            <span>✓ Aucun PIN ni CVV stocké</span>
            <span>✓ Confirmation idempotente</span>
          </div>
        </div>

        <aside className="premium-redesign-current-plan">
          <p>Ton offre actuelle</p>
          <strong>{overview?.subscription.plan_name ?? "Chargement…"}</strong>
          <span>
            {overview?.subscription.is_premium
              ? "Abonnement Premium actif"
              : "Compte gratuit"}
          </span>
          {currentPlan ? <small>{currentPlan.description}</small> : null}
        </aside>
      </section>

      {error ? (
        <div className="premium-redesign-alert" role="alert">
          <span aria-hidden="true">!</span>
          <p>{error}</p>
        </div>
      ) : null}

      {isLoading ? (
        <section className="premium-redesign-loading" aria-busy="true">
          <span className="premium-redesign-loader" aria-hidden="true" />
          <p className="premium-redesign-eyebrow">Vérification sécurisée</p>
          <h2>Chargement des offres</h2>
        </section>
      ) : null}

      {overview ? (
        <>
          <section className="premium-redesign-plans">
            <div className="premium-redesign-section-heading">
              <div>
                <p className="premium-redesign-eyebrow">Choisir mon expérience</p>
                <h2>Une offre pour chaque étape</h2>
              </div>
              <p>
                Le paiement test permet de vérifier le parcours complet
                sans débiter d'argent réel.
              </p>
            </div>

            <div className="premium-redesign-plan-grid">
              {overview.plans.map((plan) => {
                const isCurrent = overview.subscription.plan === plan.code;
                return (
                  <article
                    key={plan.code}
                    className={[
                      "premium-redesign-plan-card",
                      `premium-redesign-plan-card--${plan.code}`,
                      isCurrent ? "premium-redesign-plan-card--current" : "",
                    ].join(" ")}
                  >
                    <div className="premium-redesign-plan-card__top">
                      <div>
                        <p className="premium-redesign-plan-card__label">
                          {plan.code === "free"
                            ? "Essentiel"
                            : plan.code === "prestige"
                              ? "Expérience exclusive"
                              : "Expérience Premium"}
                        </p>
                        <h3>{plan.name}</h3>
                      </div>
                      {isCurrent ? (
                        <span className="premium-redesign-plan-card__badge">
                          Offre actuelle
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
                      disabled={isCurrent || plan.code === "free"}
                      onClick={() => {
                        if (plan.code === "plus" || plan.code === "prestige") {
                          setSelectedPlan(plan.code);
                          setTransaction(null);
                          setPaymentMessage("");
                        }
                      }}
                    >
                      {isCurrent
                        ? "Offre actuelle"
                        : plan.code === "free"
                          ? "Offre gratuite"
                          : "Choisir cette offre"}
                    </button>
                  </article>
                );
              })}
            </div>
          </section>

          <section className="premium-redesign-tools">
            <article className="premium-redesign-tool-card">
              <div className="premium-redesign-tool-card__icon">↗</div>
              <div className="premium-redesign-tool-card__content">
                <p className="premium-redesign-eyebrow">Visibilité Premium</p>
                <h2>
                  Boost de profil pendant {overview.boost.duration_minutes} minutes
                </h2>
                <p>
                  Le Boost ne contourne jamais les filtres, blocages ou
                  règles de confidentialité.
                </p>
              </div>
              <button
                type="button"
                disabled={
                  isActivatingBoost
                  || overview.boost.active
                  || overview.boost.remaining <= 0
                }
                onClick={() => void handleActivateBoost()}
              >
                {overview.boost.active
                  ? `Actif jusqu’à ${formatBoostTime(overview.boost.active_until)}`
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
              <div className="premium-redesign-tool-card__icon">◇</div>
              <div className="premium-redesign-tool-card__content">
                <p className="premium-redesign-eyebrow">
                  Confidentialité Prestige
                </p>
                <h2>Mode discret</h2>
                <p>
                  Le serveur revérifie automatiquement ton droit Prestige.
                </p>
              </div>
              <label className="premium-redesign-switch">
                <input
                  type="checkbox"
                  checked={overview.privacy.incognito_enabled}
                  disabled={
                    !overview.privacy.incognito_available
                    || isUpdatingPrivacy
                  }
                  onChange={(event) =>
                    void handleIncognitoChange(event.target.checked)
                  }
                />
                <span className="premium-redesign-switch__track" aria-hidden="true">
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

          <section className="premium-payment-history">
            <div className="premium-redesign-section-heading">
              <div>
                <p className="premium-redesign-eyebrow">Historique</p>
                <h2>Mes transactions Premium</h2>
              </div>
              <p>
                Les transactions restent rattachées à ton compte et ne
                contiennent aucun secret bancaire.
              </p>
            </div>

            {history.length === 0 ? (
              <div className="premium-payment-history__empty">
                Aucune transaction Premium pour le moment.
              </div>
            ) : (
              <div className="premium-payment-history__list">
                {history.map((item) => (
                  <article key={item.id}>
                    <div>
                      <strong>{item.plan_name}</strong>
                      <span>{item.method_name}</span>
                    </div>
                    <div>
                      <strong>{formatMoney(item.amount_xaf)} FCFA</strong>
                      <span>{formatDate(item.created_at)}</span>
                    </div>
                    <span className={`premium-payment-status premium-payment-status--${item.status}`}>
                      {item.status}
                    </span>
                  </article>
                ))}
              </div>
            )}
          </section>
        </>
      ) : null}

      {selectedPlan && checkoutPlan && overview ? (
        <div className="premium-checkout-backdrop" role="presentation">
          <section
            className="premium-checkout-dialog"
            role="dialog"
            aria-modal="true"
            aria-labelledby="premium-checkout-title"
          >
            <button
              type="button"
              className="premium-checkout-dialog__close"
              onClick={() => {
                if (!isPaymentBusy) {
                  setSelectedPlan(null);
                  setTransaction(null);
                  setPaymentMessage("");
                }
              }}
              aria-label="Fermer"
            >
              ×
            </button>

            <p className="premium-redesign-eyebrow">Paiement test sécurisé</p>
            <h2 id="premium-checkout-title">{checkoutPlan.name}</h2>
            <p className="premium-checkout-dialog__amount">
              {formatMoney(checkoutPlan.amount_xaf)} FCFA
              <span> / 30 jours</span>
            </p>

            {!transaction ? (
              <>
                <fieldset>
                  <legend>Choisir un moyen de paiement</legend>
                  {overview.payment_methods.map((method) => (
                    <label key={method.code}>
                      <input
                        type="radio"
                        name="premium-payment-method"
                        value={method.code}
                        checked={selectedMethod === method.code}
                        onChange={() => setSelectedMethod(method.code)}
                      />
                      <span>
                        <strong>{method.name}</strong>
                        <small>{method.description}</small>
                      </span>
                    </label>
                  ))}
                </fieldset>

                <div className="premium-checkout-dialog__notice">
                  Aucun débit réel. Aucun PIN, OTP, PAN ou CVV ne sera demandé.
                </div>

                <button
                  type="button"
                  className="premium-checkout-dialog__primary"
                  disabled={isPaymentBusy}
                  onClick={() => void handleCreateCheckout()}
                >
                  {isPaymentBusy
                    ? "Création sécurisée…"
                    : "Créer la transaction test"}
                </button>
              </>
            ) : (
              <div className="premium-checkout-result">
                <span className={`premium-payment-status premium-payment-status--${transaction.status}`}>
                  {transaction.status}
                </span>
                <strong>
                  Transaction {transaction.id.slice(0, 8).toUpperCase()}
                </strong>
                <p>{paymentMessage}</p>

                {transaction.status === "pending"
                && transaction.can_confirm_in_test_mode ? (
                  <div className="premium-checkout-result__actions">
                    <button
                      type="button"
                      className="premium-checkout-dialog__primary"
                      disabled={isPaymentBusy}
                      onClick={() => void handleConfirmTestPayment()}
                    >
                      {isPaymentBusy
                        ? "Confirmation serveur…"
                        : "Simuler la confirmation du prestataire"}
                    </button>
                    <button
                      type="button"
                      disabled={isPaymentBusy}
                      onClick={() => void handleCancelPayment()}
                    >
                      Annuler la transaction
                    </button>
                  </div>
                ) : null}

                {transaction.status === "succeeded" ? (
                  <button
                    type="button"
                    className="premium-checkout-dialog__primary"
                    onClick={() => {
                      setSelectedPlan(null);
                      setTransaction(null);
                    }}
                  >
                    Terminer
                  </button>
                ) : null}
              </div>
            )}
          </section>
        </div>
      ) : null}
    </main>
  );
}
