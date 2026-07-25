import { LinkButton } from "../../components/common/LinkButton";
import { useAuth } from "../../hooks/useAuth";

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
    label: "Outils de sécurité disponibles",
  },
];

const experienceCards = [
  {
    number: "01",
    eyebrow: "Authenticité",
    title: "Des profils qui inspirent davantage confiance",
    description:
      "Adresse e-mail vérifiée, photos contrôlées et parcours de vérification pour réduire les faux profils et les usurpations.",
  },
  {
    number: "02",
    eyebrow: "Confidentialité",
    title: "Une visibilité que tu maîtrises réellement",
    description:
      "Tu choisis quand apparaître dans Découvrir, tu peux bloquer, signaler et gérer les données associées à ton compte.",
  },
  {
    number: "03",
    eyebrow: "Respect",
    title: "Des échanges réservés aux connexions réciproques",
    description:
      "La messagerie privée devient accessible après un match actif afin de limiter les sollicitations indésirables.",
  },
];

const journeySteps = [
  {
    number: "01",
    title: "Crée ton profil",
    description:
      "Présente-toi avec quelques informations utiles et des photos authentiques.",
  },
  {
    number: "02",
    title: "Découvre avec intention",
    description:
      "Explore des profils compatibles selon tes préférences et ta recherche.",
  },
  {
    number: "03",
    title: "Échange après un match",
    description:
      "Une conversation privée s’ouvre uniquement lorsque l’intérêt est réciproque.",
  },
];

const safetyPoints = [
  "Sessions sécurisées et protection CSRF",
  "Limitation anti-abus appuyée par Redis",
  "Contrôle et réencodage des photos envoyées",
  "Journalisation des connexions sensibles",
];

export function HomePage() {
  const { isAuthenticated, isInitializing } = useAuth();

  const primaryAction = isAuthenticated
    ? { to: "/discovery", label: "Découvrir des profils" }
    : { to: "/register", label: "Créer mon profil" };

  const secondaryAction = isAuthenticated
    ? { to: "/profile/edit", label: "Modifier mon profil" }
    : { to: "/safety", label: "Découvrir notre sécurité" };

  const finalAction = isAuthenticated
    ? { to: "/discovery", label: "Continuer à découvrir" }
    : { to: "/register", label: "Commencer maintenant" };

  return (
    <main className="home-premium-page">
      <section className="home-premium-hero">
        <div className="home-premium-hero__background" aria-hidden="true" />

        <div className="home-premium-shell home-premium-hero__container">
          <div className="home-premium-hero__content">
            <p className="home-premium-eyebrow">
              <span aria-hidden="true" />
              Rencontre africaine, moderne et sécurisée
            </p>

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
                to={primaryAction.to}
                variant="primary"
                className="home-premium-hero__primary-action"
                aria-disabled={isInitializing}
              >
                {isInitializing ? "Vérification du compte…" : primaryAction.label}
                <span aria-hidden="true">→</span>
              </LinkButton>

              <LinkButton
                to={secondaryAction.to}
                variant="secondary"
                aria-disabled={isInitializing}
              >
                {secondaryAction.label}
              </LinkButton>
            </div>

            <div className="home-premium-hero__proof" aria-label="Engagements Mbolo">
              <span>Inscription gratuite</span>
              <span>Réservé aux adultes</span>
              <span>Données protégées</span>
            </div>
          </div>

          <div className="home-premium-visual" aria-label="Aperçu d’un profil Mbolo">
            <div className="home-premium-visual__halo" aria-hidden="true" />

            <article className="home-premium-profile">
              <div className="home-premium-profile__top">
                <span>Profil recommandé</span>
                <span className="home-premium-profile__verified" aria-label="Profil vérifié">
                  ✓
                </span>
              </div>

              <div className="home-premium-profile__portrait">
                <div className="home-premium-profile__portrait-glow" aria-hidden="true" />
                <div className="home-premium-profile__initials" aria-hidden="true">
                  AM
                </div>

                <div className="home-premium-profile__identity">
                  <p>Libreville, Gabon</p>
                  <h2>
                    Arielle <span>29</span>
                  </h2>
                  <small>
                    Passionnée de voyages, de culture et de projets ambitieux.
                  </small>
                </div>
              </div>

              <div className="home-premium-profile__footer" aria-hidden="true">
                <span>×</span>
                <span>♥</span>
              </div>
            </article>

            <div className="home-premium-floating-card home-premium-floating-card--security">
              <span aria-hidden="true">✓</span>
              <div>
                <strong>Protection active</strong>
                <small>Confidentialité par conception</small>
              </div>
            </div>

            <div className="home-premium-floating-card home-premium-floating-card--match">
              <div className="home-premium-floating-card__avatars" aria-hidden="true">
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
          <div className="home-premium-shell home-premium-trust-strip__container">
            {trustIndicators.map((indicator) => (
              <article key={indicator.label}>
                <strong>{indicator.value}</strong>
                <span>{indicator.label}</span>
              </article>
            ))}
          </div>
        </div>
      </section>

      <section className="home-premium-shell home-premium-experience">
        <header className="home-premium-section-heading">
          <div>
            <p className="home-premium-section-eyebrow">L’expérience Mbolo</p>
            <h2>Une plateforme pensée pour créer de vraies connexions.</h2>
          </div>
          <p>
            Chaque détail est conçu pour rendre la rencontre plus fluide,
            plus rassurante et plus respectueuse.
          </p>
        </header>

        <div className="home-premium-experience__grid">
          {experienceCards.map((feature) => (
            <article key={feature.number}>
              <div className="home-premium-experience__meta">
                <span>{feature.number}</span>
                <small>{feature.eyebrow}</small>
              </div>
              <h3>{feature.title}</h3>
              <p>{feature.description}</p>
              <span className="home-premium-experience__arrow" aria-hidden="true">↗</span>
            </article>
          ))}
        </div>
      </section>

      <section className="home-premium-shell home-premium-journey">
        <div className="home-premium-journey__intro">
          <p className="home-premium-section-eyebrow">Simple et intentionnel</p>
          <h2>Trois étapes pour commencer une vraie conversation.</h2>
          <p>
            Mbolo réduit le bruit et place la réciprocité au centre de
            l’expérience.
          </p>
        </div>

        <div className="home-premium-journey__steps">
          {journeySteps.map((step) => (
            <article key={step.number}>
              <span>{step.number}</span>
              <div>
                <h3>{step.title}</h3>
                <p>{step.description}</p>
              </div>
            </article>
          ))}
        </div>
      </section>

      <section className="home-premium-shell home-premium-safety">
        <div className="home-premium-safety__visual" aria-hidden="true">
          <div className="home-premium-safety__shield"><span>M</span></div>
          <div className="home-premium-safety__orbit home-premium-safety__orbit--one" />
          <div className="home-premium-safety__orbit home-premium-safety__orbit--two" />
          <div className="home-premium-safety__badge">
            <span>✓</span>
            Sécurité intégrée
          </div>
        </div>

        <div className="home-premium-safety__content">
          <p className="home-premium-section-eyebrow">Sécurité par conception</p>
          <h2>La confiance ne doit jamais être ajoutée à la fin.</h2>
          <p>
            Mbolo est développé avec une approche de défense en profondeur,
            de minimisation des données et de contrôle côté serveur.
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

      <section className="home-premium-shell home-premium-final-cta">
        <div>
          <p>Une nouvelle rencontre peut commencer aujourd’hui.</p>
          <h2>
            Rejoins une communauté qui valorise l’authenticité, le respect et
            l’ambition.
          </h2>
        </div>

        <LinkButton
          to={finalAction.to}
          variant="primary"
          aria-disabled={isInitializing}
        >
          {isInitializing ? "Vérification du compte…" : finalAction.label}
          <span aria-hidden="true">→</span>
        </LinkButton>
      </section>
    </main>
  );
}
