import { Link } from "react-router-dom";

import "../launch/LaunchInfoPages.css";

const deletionSteps = [
  {
    number: "01",
    title: "Accède à ton compte",
    description:
      "Connecte-toi avec le compte MBOLO concerné. Cette vérification empêche une autre personne de supprimer ton compte à ta place.",
  },
  {
    number: "02",
    title: "Ouvre le Centre de confidentialité",
    description:
      "Dans Mon espace, ouvre Sécurité et confidentialité, puis choisis Supprimer définitivement mon compte.",
  },
  {
    number: "03",
    title: "Confirme la suppression",
    description:
      "Saisis ton mot de passe et confirme. Le compte, le profil, les photos et les données associées sont alors supprimés.",
  },
] as const;

export function AccountDeletionPage() {
  return (
    <main className="launch-info-page">
      <section className="launch-info-hero launch-info-hero--centered">
        <div>
          <p className="launch-info-eyebrow">Contrôle de tes données</p>
          <h1>Supprimer définitivement un compte MBOLO.</h1>
          <p className="launch-info-lead">
            Cette page publique explique comment lancer une suppression depuis
            le Web ou l’application. Une simple désactivation ne remplace pas
            la suppression définitive.
          </p>
          <div className="launch-info-actions">
            <Link className="button button--primary" to="/login">
              Se connecter pour supprimer mon compte
            </Link>
            <Link className="button button--secondary" to="/forgot-password">
              Je n’ai plus accès à mon mot de passe
            </Link>
          </div>
        </div>
      </section>

      <section className="launch-info-section">
        <div className="launch-info-grid">
          {deletionSteps.map((step) => (
            <article className="launch-info-card" key={step.number}>
              <span>{step.number}</span>
              <h2>{step.title}</h2>
              <p>{step.description}</p>
            </article>
          ))}
        </div>
      </section>

      <section className="launch-info-callout">
        <div>
          <p className="launch-info-eyebrow">Ce qui est supprimé</p>
          <h2>Le compte et les données personnelles associées.</h2>
        </div>
        <p>
          La suppression couvre notamment le profil, les préférences, les
          photos, les sessions et les informations d’authentification. Certaines
          traces strictement nécessaires à la prévention de la fraude, à la
          sécurité ou à une obligation légale peuvent être conservées pendant
          la durée requise, conformément à la politique de confidentialité.
        </p>
      </section>

      <section className="launch-info-section">
        <article className="launch-info-card">
          <span>?</span>
          <h2>Besoin d’aide avant la suppression ?</h2>
          <p>
            Consulte le Centre d’aide ou la page Contact. Ne communique jamais
            ton mot de passe, ton code 2FA ou ton code PIN Mobile Money.
          </p>
          <Link to="/contact">Contacter l’assistance →</Link>
        </article>
      </section>
    </main>
  );
}
