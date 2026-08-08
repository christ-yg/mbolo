import { Link } from "react-router-dom";

import "../launch/LaunchInfoPages.css";

const supportPaths = [
  {
    number: "01",
    title: "Compte et connexion",
    description: "Utilise le Centre d’aide pour les questions d’inscription, de vérification d’e-mail et de récupération de compte.",
    to: "/help",
    action: "Consulter le Centre d’aide",
  },
  {
    number: "02",
    title: "Sécurité et comportement",
    description: "Pour un profil suspect, bloque et signale directement depuis Mbolo afin de conserver les éléments utiles à la modération.",
    to: "/safety",
    action: "Ouvrir le Centre de sécurité",
  },
  {
    number: "03",
    title: "Sanction de compte",
    description: "La contestation publique permet de transmettre une demande même lorsque l’accès au compte est limité.",
    to: "/sanction-appeal",
    action: "Contester une sanction",
  },
] as const;

export function ContactPage() {
  return (
    <main className="launch-info-page">
      <section className="launch-info-hero launch-info-hero--centered">
        <div>
          <p className="launch-info-eyebrow">Contact et assistance</p>
          <h1>Trouver rapidement le bon canal d’assistance.</h1>
          <p className="launch-info-lead">
            Mbolo sépare l’aide générale, les demandes de sécurité et les
            contestations afin de protéger les informations personnelles et
            d’orienter chaque demande vers le parcours approprié.
          </p>
        </div>
      </section>

      <section className="launch-info-section">
        <div className="launch-info-grid">
          {supportPaths.map((item) => (
            <article className="launch-info-card" key={item.number}>
              <span>{item.number}</span>
              <h2>{item.title}</h2>
              <p>{item.description}</p>
              <Link to={item.to}>{item.action} →</Link>
            </article>
          ))}
        </div>
      </section>

      <section className="launch-info-callout">
        <div>
          <p className="launch-info-eyebrow">Urgence réelle</p>
          <h2>La plateforme ne remplace pas les services d’urgence.</h2>
        </div>
        <p>
          En cas de danger immédiat, contacte les autorités ou les services
          d’urgence de ton pays. Ne publie jamais de mot de passe, de document
          d’identité ou de donnée bancaire dans une demande d’assistance.
        </p>
      </section>
    </main>
  );
}
