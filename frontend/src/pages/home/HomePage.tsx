import { LinkButton } from "../../components/common/LinkButton";

import "./HomePage.css";


const trustIndicators = [
  {
    value: "18+",
    label: "Communauté exclusivement adulte",
  },
  {
    value: "6",
    label: "Photos protégées par profil",
  },
  {
    value: "24/7",
    label: "Protection et signalements",
  },
];


const experienceCards = [
  {
    number: "01",
    eyebrow: "Authenticité",
    title: "Des profils qui inspirent confiance",
    description:
      "Adresse e-mail vérifiée, photos contrôlées et outils de vérification pour réduire les faux profils.",
  },
  {
    number: "02",
    eyebrow: "Confidentialité",
    title: "Tu gardes le contrôle sur ta visibilité",
    description:
      "Choisis qui peut te découvrir, protège tes informations et maîtrise les interactions autour de ton profil.",
  },
  {
    number: "03",
    eyebrow: "Respect",
    title: "Des échanges pensés pour durer",
    description:
      "Blocage, signalement, limitation anti-abus et modération contribuent à une communauté plus saine.",
  },
];


const safetyPoints = [
  "Sessions sécurisées et protection CSRF",
  "Limitation anti-force brute avec Redis",
  "Réencodage sécurisé des photos",
  "Journalisation et alertes de connexion",
];


export function HomePage() {
  return (
    <main className="home-premium-page">
      <section className="home-premium-hero">
        <div className="home-premium-hero__background" />

        <div className="home-premium-hero__container">
          <div className="home-premium-hero__content">
            <div className="home-premium-hero__eyebrow">
              <span aria-hidden="true" />
              Rencontre africaine, moderne et sécurisée
            </div>

            <h1>
              La rencontre sincère commence par la confiance.
            </h1>

            <p className="home-premium-hero__description">
              Mbolo rapproche les personnes qui souhaitent construire une
              relation authentique dans une expérience élégante, respectueuse
              et pensée avec la sécurité au cœur du produit.
            </p>

            <div className="home-premium-hero__actions">
              <LinkButton
                to="/register"
                variant="primary"
                className="home-premium-hero__primary-action"
              >
                Créer mon profil
                <span aria-hidden="true">→</span>
              </LinkButton>

              <LinkButton
                to="/safety"
                variant="secondary"
              >
                Découvrir notre sécurité
              </LinkButton>
            </div>

            <div className="home-premium-hero__proof">
              <span>Inscription gratuite</span>
              <span>Réservé aux adultes</span>
              <span>Données protégées</span>
            </div>
          </div>

          <div
            className="home-premium-visual"
            aria-label="Aperçu d’un profil Mbolo"
          >
            <div className="home-premium-visual__halo" />

            <div className="home-premium-profile">
              <div className="home-premium-profile__top">
                <span>Profil recommandé</span>
                <span
                  className="home-premium-profile__verified"
                  aria-label="Profil vérifié"
                >
                  ✓
                </span>
              </div>

              <div className="home-premium-profile__portrait">
                <div className="home-premium-profile__portrait-glow" />

                <div
                  className="home-premium-profile__initials"
                  aria-hidden="true"
                >
                  AM
                </div>

                <div className="home-premium-profile__identity">
                  <p>Libreville, Gabon</p>

                  <h2>
                    Arielle
                    <span>29</span>
                  </h2>

                  <small>
                    Passionnée de voyages, de culture et de projets ambitieux.
                  </small>
                </div>
              </div>

              <div className="home-premium-profile__footer">
                <button
                  type="button"
                  aria-label="Passer ce profil"
                >
                  ×
                </button>

                <button
                  type="button"
                  aria-label="Aimer ce profil"
                >
                  ♥
                </button>
              </div>
            </div>

            <div className="home-premium-floating-card home-premium-floating-card--security">
              <span aria-hidden="true">✓</span>
              <div>
                <strong>Protection active</strong>
                <small>Confidentialité par conception</small>
              </div>
            </div>

            <div className="home-premium-floating-card home-premium-floating-card--match">
              <div className="home-premium-floating-card__avatars">
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

        <div className="home-premium-trust-strip">
          <div className="home-premium-trust-strip__container">
            {trustIndicators.map((indicator) => (
              <article key={indicator.label}>
                <strong>{indicator.value}</strong>
                <span>{indicator.label}</span>
              </article>
            ))}
          </div>
        </div>
      </section>

      <section className="home-premium-experience">
        <div className="home-premium-section-heading">
          <div>
            <p className="section-heading__eyebrow">
              L’expérience Mbolo
            </p>

            <h2>
              Une plateforme pensée pour créer de vraies connexions.
            </h2>
          </div>

          <p>
            Chaque détail est conçu pour rendre la rencontre plus fluide,
            plus rassurante et plus respectueuse.
          </p>
        </div>

        <div className="home-premium-experience__grid">
          {experienceCards.map((feature) => (
            <article key={feature.number}>
              <div className="home-premium-experience__meta">
                <span>{feature.number}</span>
                <small>{feature.eyebrow}</small>
              </div>

              <h3>{feature.title}</h3>

              <p>{feature.description}</p>

              <span
                className="home-premium-experience__arrow"
                aria-hidden="true"
              >
                ↗
              </span>
            </article>
          ))}
        </div>
      </section>

      <section className="home-premium-safety">
        <div className="home-premium-safety__visual">
          <div className="home-premium-safety__shield">
            <span>M</span>
          </div>

          <div className="home-premium-safety__orbit home-premium-safety__orbit--one" />
          <div className="home-premium-safety__orbit home-premium-safety__orbit--two" />

          <div className="home-premium-safety__badge">
            <span aria-hidden="true">✓</span>
            Sécurité intégrée
          </div>
        </div>

        <div className="home-premium-safety__content">
          <p className="section-heading__eyebrow">
            Sécurité par conception
          </p>

          <h2>
            La confiance ne doit jamais être ajoutée à la fin.
          </h2>

          <p>
            Mbolo est développé avec une approche de défense en profondeur
            inspirée des pratiques utilisées dans les organisations matures.
          </p>

          <ul>
            {safetyPoints.map((point) => (
              <li key={point}>
                <span aria-hidden="true">✓</span>
                {point}
              </li>
            ))}
          </ul>

          <LinkButton to="/safety" variant="secondary">
            Consulter notre approche
          </LinkButton>
        </div>
      </section>

      <section className="home-premium-final-cta">
        <div>
          <p>Une nouvelle rencontre peut commencer aujourd’hui.</p>

          <h2>
            Rejoins une communauté qui valorise l’authenticité, le respect
            et l’ambition.
          </h2>
        </div>

        <LinkButton
          to="/register"
          variant="primary"
        >
          Commencer maintenant
          <span aria-hidden="true">→</span>
        </LinkButton>
      </section>
    </main>
  );
}
