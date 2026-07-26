import { Link } from "react-router-dom";

import { useAuth } from "../../hooks/useAuth";

import "./MySpacePage.css";

interface SpaceLink {
  title: string;
  description: string;
  to: string;
  eyebrow: string;
  symbol: string;
  emphasis?: boolean;
}

const PERSONALIZATION_LINKS: SpaceLink[] = [
  {
    title: "Modifier mon profil",
    description: "Mets à jour ton identité publique, ta ville, ta recherche et tes centres d’intérêt.",
    to: "/profile/edit",
    eyebrow: "Identité",
    symbol: "P",
    emphasis: true,
  },
  {
    title: "Gérer mes photos",
    description: "Ajoute, supprime ou définis ta photo principale parmi les images approuvées.",
    to: "/profile/photos",
    eyebrow: "Image",
    symbol: "▣",
  },
  {
    title: "Vérifier mon profil",
    description: "Consulte le statut de ta vérification et renforce la confiance autour de ton compte.",
    to: "/profile/verification",
    eyebrow: "Confiance",
    symbol: "✓",
  },
  {
    title: "Préférences de découverte",
    description: "Ajuste les critères utilisés côté serveur pour sélectionner les profils compatibles.",
    to: "/discovery-preferences",
    eyebrow: "Découverte",
    symbol: "◇",
  },
];

const ACCOUNT_LINKS: SpaceLink[] = [
  {
    title: "Mon abonnement",
    description: "Compare les offres Mbolo et consulte les avantages associés à ton niveau actuel.",
    to: "/premium",
    eyebrow: "Premium",
    symbol: "+",
  },
  {
    title: "Qui m’a liké",
    description: "Retrouve les marques d’intérêt reçues selon les droits accordés à ton offre.",
    to: "/likes-received",
    eyebrow: "Intérêt reçu",
    symbol: "♡",
  },
  {
    title: "Confidentialité",
    description: "Contrôle tes données, tes consentements et les opérations liées à ton compte.",
    to: "/account/privacy",
    eyebrow: "Données",
    symbol: "◌",
  },
  {
    title: "Sécurité du compte",
    description: "Surveille les connexions, les appareils et les protections de ton accès Mbolo.",
    to: "/account/security",
    eyebrow: "Protection",
    symbol: "◆",
  },
  {
    title: "Profils bloqués",
    description: "Consulte et administre la liste privée des personnes que tu as bloquées.",
    to: "/blocked-users",
    eyebrow: "Contrôle",
    symbol: "⊘",
  },
  {
    title: "Mes signalements",
    description: "Suis les dossiers transmis à la modération sans exposer les notes internes.",
    to: "/reports",
    eyebrow: "Communauté",
    symbol: "!",
  },
];

function SpaceCard({ item }: { item: SpaceLink }) {
  return (
    <Link
      className={`my-space-card${item.emphasis ? " my-space-card--featured" : ""}`}
      to={item.to}
    >
      <span className="my-space-card__icon" aria-hidden="true">
        {item.symbol}
      </span>
      <span className="my-space-card__content">
        <span className="my-space-card__eyebrow">{item.eyebrow}</span>
        <strong>{item.title}</strong>
        <span>{item.description}</span>
      </span>
      <span className="my-space-card__arrow" aria-hidden="true">→</span>
    </Link>
  );
}

export function MySpacePage() {
  const { user } = useAuth();
  const email = user?.email ?? "Compte Mbolo";
  const emailVerified = Boolean(user?.isEmailVerified);
  const twoFactorEnabled = Boolean(user?.emailTwoFactorEnabled);

  return (
    <main className="my-space-page">
      <section className="my-space-hero">
        <div className="my-space-hero__copy">
          <p className="my-space-kicker">Pilotage de mon compte</p>
          <h1>Mon espace</h1>
          <p className="my-space-hero__lead">
            Retrouve au même endroit ton profil, tes préférences, ta confidentialité,
            ta sécurité et les outils qui te permettent de garder le contrôle.
          </p>
          <div className="my-space-hero__actions">
            <Link className="my-space-button my-space-button--primary" to="/profile/edit">
              Modifier mon profil <span aria-hidden="true">→</span>
            </Link>
            <Link className="my-space-button" to="/discovery">
              Aller dans Découvrir
            </Link>
          </div>
        </div>

        <aside className="my-space-summary" aria-label="Résumé du compte">
          <div className="my-space-summary__avatar" aria-hidden="true">
            {email.charAt(0).toUpperCase()}
          </div>
          <p className="my-space-summary__label">Compte connecté</p>
          <strong className="my-space-summary__email">{email}</strong>
          <div className="my-space-summary__status-list">
            <span className={emailVerified ? "is-positive" : "is-warning"}>
              {emailVerified ? "✓ Adresse e-mail vérifiée" : "○ Adresse e-mail à vérifier"}
            </span>
            <span className={twoFactorEnabled ? "is-positive" : "is-warning"}>
              {twoFactorEnabled ? "✓ Double authentification active" : "○ Double authentification inactive"}
            </span>
          </div>
          <Link to="/account/security">Renforcer ma sécurité →</Link>
        </aside>
      </section>

      <section className="my-space-section">
        <div className="my-space-section__heading">
          <div>
            <p className="my-space-kicker">Mon identité sur Mbolo</p>
            <h2>Personnaliser mon expérience</h2>
          </div>
          <p>
            Les informations publiques et les critères de découverte restent séparés
            de tes données techniques et de connexion.
          </p>
        </div>
        <div className="my-space-grid my-space-grid--personalization">
          {PERSONALIZATION_LINKS.map((item) => (
            <SpaceCard key={item.to} item={item} />
          ))}
        </div>
      </section>

      <section className="my-space-section my-space-section--account">
        <div className="my-space-section__heading">
          <div>
            <p className="my-space-kicker">Compte et contrôle</p>
            <h2>Gérer mes accès et mes données</h2>
          </div>
          <p>
            Chaque action sensible est protégée par l’authentification et validée
            côté serveur avant d’être appliquée.
          </p>
        </div>
        <div className="my-space-grid">
          {ACCOUNT_LINKS.map((item) => (
            <SpaceCard key={item.to} item={item} />
          ))}
        </div>
      </section>

      <section className="my-space-security-note">
        <div className="my-space-security-note__mark" aria-hidden="true">M</div>
        <div>
          <p className="my-space-kicker">Confidentialité par conception</p>
          <h2>Ce qui est privé reste privé.</h2>
          <p>
            Ton adresse e-mail, ton mot de passe, tes empreintes de session et les
            notes internes de modération ne sont jamais affichés aux autres membres.
          </p>
        </div>
        <Link to="/safety">Consulter le centre de sécurité →</Link>
      </section>
    </main>
  );
}
