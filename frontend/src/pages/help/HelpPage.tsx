import { Link } from "react-router-dom";

import "../launch/LaunchInfoPages.css";

const faq = [
  ["Qui peut utiliser Mbolo ?", "Mbolo est réservé aux personnes âgées d’au moins 18 ans."],
  ["Pourquoi vérifier mon adresse e-mail ?", "La vérification confirme que tu contrôles l’adresse associée au compte et renforce la fiabilité du parcours d’accès."],
  ["Quand puis-je envoyer un message ?", "La messagerie privée est liée aux connexions réciproques : un match actif permet d’ouvrir une conversation."],
  ["Que faire face à un profil suspect ?", "N’envoie pas d’argent sous pression. Utilise les fonctions de blocage et de signalement et conserve tes échanges dans Mbolo."],
  ["Puis-je gérer mes données ?", "Oui. Le Centre de confidentialité regroupe les actions disponibles sur tes données et ton compte."],
  ["Les fonctions Premium sont-elles déjà payantes ?", "La plateforme prépare les fonctions Premium, mais aucun paiement réel ne doit être considéré comme actif tant que les partenaires de paiement ne sont pas officiellement connectés."],
];

export function HelpPage() {
  return (
    <main className="launch-info-page">
      <section className="launch-info-hero launch-info-hero--centered">
        <div>
          <p className="launch-info-eyebrow">Centre d’aide</p>
          <h1>Les réponses essentielles pour utiliser Mbolo sereinement.</h1>
          <p className="launch-info-lead">
            Compte, matchs, messages, sécurité et confidentialité : retrouve ici
            les réponses aux questions les plus fréquentes.
          </p>
        </div>
      </section>

      <section className="launch-info-section launch-info-section--faq">
        <div className="launch-info-faq">
          {faq.map(([question, answer]) => (
            <details key={question}>
              <summary>{question}<span aria-hidden="true">+</span></summary>
              <p>{answer}</p>
            </details>
          ))}
        </div>

        <aside className="launch-info-help-panel">
          <p className="launch-info-eyebrow">Besoin de sécurité ?</p>
          <h2>Priorité à ta protection.</h2>
          <p>
            Pour un problème lié à un autre membre, utilise le blocage ou le
            signalement. Pour une sanction de compte, la page de contestation
            reste accessible publiquement.
          </p>
          <Link to="/safety">Ouvrir le Centre de sécurité →</Link>
          <Link to="/sanction-appeal">Contester une sanction →</Link>
          <Link to="/legal/community">Lire les règles de la communauté →</Link>
        </aside>
      </section>
    </main>
  );
}
