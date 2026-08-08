import { Link, useParams } from "react-router-dom";

import "./LegalPage.css";

type LegalDocument = {
  eyebrow: string;
  title: string;
  introduction: string;
  sections: Array<{ title: string; paragraphs: string[] }>;
};

const DOCUMENTS: Record<string, LegalDocument> = {
  notice: {
    eyebrow: "Identification et publication",
    title: "Mentions légales",
    introduction: "Cette page identifie les responsabilités liées à l’édition et à l’exploitation de Mbolo.",
    sections: [
      { title: "Éditeur", paragraphs: ["Mbolo est un projet numérique en phase de préproduction. L’identité juridique, la forme sociale, l’adresse du siège et les références d’immatriculation devront être ajoutées ici avant l’ouverture commerciale."] },
      { title: "Direction de la publication", paragraphs: ["Le nom et les coordonnées professionnelles du directeur de la publication seront renseignés avant la mise en production publique."] },
      { title: "Hébergement", paragraphs: ["Le nom de l’hébergeur, son adresse et ses coordonnées seront publiés dès que l’infrastructure de production aura été sélectionnée et contractualisée."] },
      { title: "Contact", paragraphs: ["Les demandes doivent être orientées depuis la page Contact. Aucun mot de passe, document d’identité ou renseignement bancaire ne doit être transmis dans une demande libre."] },
    ],
  },
  terms: {
    eyebrow: "Cadre d’utilisation",
    title: "Conditions générales d’utilisation",
    introduction: "Ces règles protègent les membres de Mbolo et définissent les conditions d’accès à la plateforme.",
    sections: [
      { title: "Accès réservé aux adultes", paragraphs: ["Mbolo est strictement réservé aux personnes âgées d’au moins 18 ans. Toute fausse déclaration peut entraîner la suspension ou la suppression du compte."] },
      { title: "Compte personnel", paragraphs: ["Chaque membre est responsable de son compte, de son mot de passe et de l’exactitude des informations publiées. L’usurpation d’identité et le partage de compte sont interdits."] },
      { title: "Comportement attendu", paragraphs: ["Le harcèlement, les menaces, les contenus haineux, les escroqueries, la prostitution, l’exploitation sexuelle et toute activité illégale sont interdits."] },
      { title: "Modération", paragraphs: ["Mbolo peut examiner les contenus signalés, masquer une photo, limiter une fonctionnalité ou sanctionner un compte afin de protéger la communauté. Une contestation reste possible depuis la page dédiée."] },
      { title: "Abonnements", paragraphs: ["Les prix, avantages et durées sont affichés avant paiement. Les moyens prévus pour le Gabon sont Airtel Money, Moov Money et les cartes bancaires, après activation des partenaires de paiement."] },
    ],
  },
  privacy: {
    eyebrow: "Protection des données",
    title: "Politique de confidentialité",
    introduction: "Mbolo applique la minimisation des données, la confidentialité par défaut et des contrôles d’accès adaptés.",
    sections: [
      { title: "Données collectées", paragraphs: ["Nous traitons les informations de compte, le profil public, les préférences, les photos, les interactions, les messages et les données techniques nécessaires à la sécurité."] },
      { title: "Finalités", paragraphs: ["Ces données servent à fournir les rencontres, sécuriser les comptes, prévenir les abus, gérer les abonnements et répondre aux obligations légales."] },
      { title: "Visibilité", paragraphs: ["L’adresse e-mail, le mot de passe, les selfies de vérification, les notes internes et les informations techniques ne sont jamais affichés aux autres membres."] },
      { title: "Conservation et droits", paragraphs: ["Le membre peut consulter ses données, demander leur export, désactiver son compte ou demander sa suppression depuis le Centre de confidentialité. Certaines traces de sécurité peuvent être conservées pendant la durée légalement nécessaire."] },
    ],
  },
  cookies: {
    eyebrow: "Navigation",
    title: "Politique relative aux cookies",
    introduction: "La version actuelle de Mbolo utilise uniquement les éléments indispensables au fonctionnement et à la sécurité.",
    sections: [
      { title: "Cookies nécessaires", paragraphs: ["Le cookie de session permet de rester connecté. Le cookie CSRF protège les actions sensibles contre les requêtes frauduleuses. Ils ne servent pas à vendre un profil publicitaire."] },
      { title: "Préférences futures", paragraphs: ["Si des outils de mesure d’audience ou de marketing sont ajoutés, ils seront désactivés par défaut jusqu’au recueil d’un consentement distinct."] },
    ],
  },
  community: {
    eyebrow: "Confiance et respect",
    title: "Règles de la communauté",
    introduction: "Mbolo doit rester un espace de rencontres authentiques, respectueuses et sûres.",
    sections: [
      { title: "Authenticité", paragraphs: ["Utilise tes propres photos et des informations sincères. Ne te fais pas passer pour une autre personne."] },
      { title: "Respect", paragraphs: ["Respecte le consentement, les limites et le refus. Aucun harcèlement, chantage, contenu discriminatoire ou sexuellement explicite non sollicité n’est accepté."] },
      { title: "Sécurité", paragraphs: ["Ne transmets jamais d’argent sous pression. Utilise le blocage et le signalement en cas de doute. Pour une première rencontre, privilégie un lieu public et informe une personne de confiance."] },
    ],
  },
};

export function LegalPage() {
  const { document = "terms" } = useParams();
  const content = DOCUMENTS[document] ?? DOCUMENTS.terms;

  return (
    <main className="legal-page">
      <header className="legal-page__hero">
        <p className="section-heading__eyebrow">{content.eyebrow}</p>
        <h1>{content.title}</h1>
        <p>{content.introduction}</p>
        <small>Version applicable : 8 août 2026</small>
      </header>

      <div className="legal-page__layout">
        <nav className="legal-page__nav" aria-label="Documents légaux">
          <Link to="/legal/notice">Mentions légales</Link>
          <Link to="/legal/terms">Conditions d’utilisation</Link>
          <Link to="/legal/privacy">Confidentialité</Link>
          <Link to="/legal/cookies">Cookies</Link>
          <Link to="/legal/community">Règles de la communauté</Link>
        </nav>

        <article className="legal-page__content">
          {content.sections.map((section) => (
            <section key={section.title}>
              <h2>{section.title}</h2>
              {section.paragraphs.map((paragraph) => <p key={paragraph}>{paragraph}</p>)}
            </section>
          ))}
          <div className="form-alert">
            Ces textes constituent le socle fonctionnel actuel. Ils devront être validés par un juriste gabonais avant l’ouverture commerciale définitive.
          </div>
        </article>
      </div>
    </main>
  );
}
