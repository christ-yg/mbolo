import { Link } from "react-router-dom";

import "../launch/LaunchInfoPages.css";

const steps = [
  ["01", "Créer un compte", "Inscris-toi avec une adresse e-mail valide et confirme ton accès."],
  ["02", "Construire ton profil", "Ajoute des informations sincères, tes préférences et des photos qui te représentent."],
  ["03", "Découvrir", "Explore les profils proposés selon les préférences de découverte disponibles."],
  ["04", "Créer un match", "Lorsque l’intérêt devient réciproque, Mbolo crée un match entre les deux membres."],
  ["05", "Échanger", "La messagerie privée permet alors de commencer une conversation dans le respect."],
  ["06", "Garder le contrôle", "À tout moment, tu peux gérer ta visibilité, bloquer, signaler ou ajuster tes paramètres."],
];

export function HowItWorksPage() {
  return (
    <main className="launch-info-page">
      <section className="launch-info-hero launch-info-hero--centered">
        <div>
          <p className="launch-info-eyebrow">Le parcours Mbolo</p>
          <h1>De la découverte à la conversation, sans compliquer la rencontre.</h1>
          <p className="launch-info-lead">
            Le parcours est conçu pour rester simple : présenter qui tu es,
            découvrir avec intention et échanger lorsque l’intérêt est mutuel.
          </p>
        </div>
      </section>

      <section className="launch-info-section">
        <div className="launch-info-timeline">
          {steps.map(([number, title, description]) => (
            <article key={number}>
              <div className="launch-info-timeline__number">{number}</div>
              <div>
                <h2>{title}</h2>
                <p>{description}</p>
              </div>
            </article>
          ))}
        </div>
      </section>

      <section className="launch-info-callout">
        <div>
          <p className="launch-info-eyebrow">La sécurité reste accessible</p>
          <h2>Un doute pendant ton parcours ?</h2>
          <p>Consulte le Centre de sécurité ou le Centre d’aide avant de continuer.</p>
        </div>
        <div className="launch-info-actions">
          <Link className="launch-info-button launch-info-button--primary" to="/safety">Centre de sécurité</Link>
          <Link className="launch-info-button" to="/help">Centre d’aide</Link>
        </div>
      </section>
    </main>
  );
}
