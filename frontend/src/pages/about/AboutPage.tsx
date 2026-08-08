import { Link } from "react-router-dom";

import "../launch/LaunchInfoPages.css";

const pillars = [
  ["01", "Authenticité", "Favoriser des profils sincères et des échanges qui commencent sur une intention claire."],
  ["02", "Respect", "Donner à chacun des outils simples pour poser ses limites, bloquer et signaler."],
  ["03", "Sécurité", "Concevoir chaque fonctionnalité avec la protection des comptes et des données en tête."],
];

export function AboutPage() {
  return (
    <main className="launch-info-page">
      <section className="launch-info-hero">
        <div>
          <p className="launch-info-eyebrow">Notre vision</p>
          <h1>Une rencontre africaine moderne, ambitieuse et digne de confiance.</h1>
          <p className="launch-info-lead">
            Mbolo est né avec une idée simple : créer une expérience de rencontre
            élégante, adaptée au contexte gabonais et construite autour de la
            réciprocité plutôt que du bruit.
          </p>
          <div className="launch-info-actions">
            <Link className="launch-info-button launch-info-button--primary" to="/register">Créer mon profil</Link>
            <Link className="launch-info-button" to="/how-it-works">Comment ça marche</Link>
          </div>
        </div>
        <aside className="launch-info-quote">
          <span aria-hidden="true">M</span>
          <p>« Mbolo » évoque la rencontre, le lien et le fait de se retrouver.</p>
        </aside>
      </section>

      <section className="launch-info-section">
        <header>
          <p className="launch-info-eyebrow">Nos principes</p>
          <h2>La qualité d’une communauté se construit dès le produit.</h2>
        </header>
        <div className="launch-info-grid">
          {pillars.map(([number, title, description]) => (
            <article className="launch-info-card" key={number}>
              <span>{number}</span>
              <h3>{title}</h3>
              <p>{description}</p>
            </article>
          ))}
        </div>
      </section>

      <section className="launch-info-band">
        <div>
          <p className="launch-info-eyebrow">Pensé pour durer</p>
          <h2>Le web aujourd’hui. Le mobile ensuite.</h2>
        </div>
        <p>
          La plateforme web constitue le socle fonctionnel de Mbolo. Les mêmes
          règles de compte, de sécurité, de profils et de messagerie serviront
          ensuite à l’application mobile.
        </p>
      </section>
    </main>
  );
}
