/**
 * Première page d'accueil publique de Mbolo.
 *
 * Cette version constitue notre première base visuelle professionnelle.
 * Elle sera enrichie progressivement avec :
 *
 * - des illustrations ;
 * - des animations légères ;
 * - des témoignages ;
 * - une section détaillée sur la sécurité ;
 * - une présentation plus complète des fonctionnalités.
 */

import { LinkButton } from "../../components/common/LinkButton";

const trustIndicators = [
  {
    value: "18+",
    label: "Communauté exclusivement adulte",
  },
  {
    value: "6",
    label: "Photos sécurisées par profil",
  },
  {
    value: "24/7",
    label: "Protection et signalements",
  },
];

const featureCards = [
  {
    number: "01",
    title: "Des profils authentiques",
    description:
      "Des profils structurés, des adresses e-mail vérifiées et des photos traitées par une chaîne de sécurité dédiée.",
  },
  {
    number: "02",
    title: "Une découverte privée",
    description:
      "Choisis qui peut te découvrir grâce à des préférences confidentielles et des contrôles d'accès stricts.",
  },
  {
    number: "03",
    title: "Des échanges plus sûrs",
    description:
      "Blocages bidirectionnels, signalements, limitation anti-abus et journalisation sécurisée protègent la communauté.",
  },
];

export function HomePage() {
  return (
    <main>
      <section className="hero-section">
        <div className="hero-section__glow hero-section__glow--one" />
        <div className="hero-section__glow hero-section__glow--two" />

        <div className="hero-section__container">
          <div className="hero-section__content">
            <div className="hero-section__eyebrow">
              <span className="hero-section__eyebrow-dot" />

              Rencontre africaine, moderne et sécurisée
            </div>

            <h1 className="hero-section__title">
              Une rencontre
              <span> sincère </span>
              commence par un espace de confiance.
            </h1>

            <p className="hero-section__description">
              Mbolo rapproche les personnes qui souhaitent créer une
              relation authentique, dans une expérience élégante,
              respectueuse et conçue avec la sécurité au cœur du produit.
            </p>

            <div className="hero-section__actions">
              <LinkButton
                to="/register"
                variant="primary"
                className="hero-section__primary-action"
              >
                Commencer l’expérience
                <span aria-hidden="true">→</span>
              </LinkButton>

              <LinkButton to="/safety" variant="secondary">
                Découvrir notre sécurité
              </LinkButton>
            </div>

            <p className="hero-section__privacy-note">
              Inscription gratuite · Réservé aux adultes · Données
              protégées
            </p>
          </div>

          <div
            className="hero-visual"
            aria-label="Aperçu de profils Mbolo"
          >
            <div className="hero-visual__frame">
              <div className="hero-visual__topbar">
                <span className="hero-visual__status">
                  Profil recommandé
                </span>

                <span
                  className="hero-visual__verified"
                  aria-label="Profil vérifié"
                >
                  ✓
                </span>
              </div>

              <div className="hero-visual__portrait">
                <div className="hero-visual__portrait-overlay" />

                <div className="hero-visual__initials" aria-hidden="true">
                  AM
                </div>

                <div className="hero-visual__profile-data">
                  <p className="hero-visual__location">
                    Libreville, Gabon
                  </p>

                  <h2>
                    Arielle
                    <span>29</span>
                  </h2>

                  <p>
                    Passionnée de voyages, de culture et de projets
                    ambitieux.
                  </p>
                </div>
              </div>

              <div className="hero-visual__footer">
                <button
                  className="hero-visual__control hero-visual__control--secondary"
                  type="button"
                  aria-label="Passer ce profil"
                >
                  ×
                </button>

                <button
                  className="hero-visual__control hero-visual__control--primary"
                  type="button"
                  aria-label="Aimer ce profil"
                >
                  ♥
                </button>
              </div>
            </div>

            <div className="hero-visual__floating-card hero-visual__floating-card--security">
              <span aria-hidden="true">◆</span>

              <div>
                <strong>Protection active</strong>
                <small>Confidentialité par conception</small>
              </div>
            </div>

            <div className="hero-visual__floating-card hero-visual__floating-card--match">
              <div className="hero-visual__avatars">
                <span>AM</span>
                <span>CY</span>
              </div>

              <div>
                <strong>Nouveau match</strong>
                <small>Une connexion réciproque</small>
              </div>
            </div>
          </div>
        </div>

        <div className="trust-strip">
          <div className="trust-strip__container">
            {trustIndicators.map((indicator) => (
              <article
                className="trust-strip__item"
                key={indicator.label}
              >
                <strong>{indicator.value}</strong>
                <span>{indicator.label}</span>
              </article>
            ))}
          </div>
        </div>
      </section>

      <section className="features-section">
        <div className="features-section__container">
          <div className="section-heading">
            <p className="section-heading__eyebrow">
              L’expérience Mbolo
            </p>

            <h2>
              Plus qu’une application.
              <span> Un environnement de confiance.</span>
            </h2>

            <p>
              Chaque fonctionnalité est conçue pour favoriser des
              rencontres sérieuses tout en réduisant les abus, les
              expositions inutiles et les risques pour les utilisateurs.
            </p>
          </div>

          <div className="features-grid">
            {featureCards.map((feature) => (
              <article className="feature-card" key={feature.number}>
                <span className="feature-card__number">
                  {feature.number}
                </span>

                <h3>{feature.title}</h3>

                <p>{feature.description}</p>

                <span
                  className="feature-card__decorative-arrow"
                  aria-hidden="true"
                >
                  ↗
                </span>
              </article>
            ))}
          </div>
        </div>
      </section>

      <section className="security-section">
        <div className="security-section__container">
          <div className="security-section__visual">
            <div className="security-section__shield">
              <span aria-hidden="true">M</span>
            </div>

            <div className="security-section__orbit security-section__orbit--one" />
            <div className="security-section__orbit security-section__orbit--two" />
          </div>

          <div className="security-section__content">
            <p className="section-heading__eyebrow">
              Sécurité par conception
            </p>

            <h2>
              La confiance n’est pas une option ajoutée à la fin.
            </h2>

            <p>
              Mbolo est développé avec une approche de défense en
              profondeur inspirée des standards utilisés par les
              organisations matures.
            </p>

            <ul className="security-list">
              <li>
                <span aria-hidden="true">✓</span>
                Protection CSRF et sessions sécurisées
              </li>

              <li>
                <span aria-hidden="true">✓</span>
                Limitation anti-force brute avec Redis
              </li>

              <li>
                <span aria-hidden="true">✓</span>
                Traitement et réencodage sécurisé des photos
              </li>

              <li>
                <span aria-hidden="true">✓</span>
                Blocage, signalement et isolation des données
              </li>
            </ul>

            <LinkButton to="/safety" variant="secondary">
              Consulter notre approche
            </LinkButton>
          </div>
        </div>
      </section>

      <section className="final-cta">
        <div className="final-cta__container">
          <p>Une nouvelle rencontre peut commencer aujourd’hui.</p>

          <h2>
            Rejoins une communauté qui valorise l’authenticité,
            le respect et l’ambition.
          </h2>

          <LinkButton to="/register" variant="primary">
            Créer mon profil
            <span aria-hidden="true">→</span>
          </LinkButton>
        </div>
      </section>
    </main>
  );
}
