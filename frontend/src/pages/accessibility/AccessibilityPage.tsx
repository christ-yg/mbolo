import "../launch/LaunchInfoPages.css";

const commitments = [
  ["01", "Navigation claire", "Des titres hiérarchisés, des liens explicites et un ordre de lecture cohérent facilitent la navigation au clavier et avec les technologies d’assistance."],
  ["02", "Lisibilité", "Les interfaces visent des contrastes suffisants, une taille de texte adaptable et une utilisation possible sur mobile sans zoom imposé."],
  ["03", "Mouvement maîtrisé", "Les préférences de réduction des animations du système sont respectées lorsque des transitions sont présentes."],
] as const;

export function AccessibilityPage() {
  return (
    <main className="launch-info-page">
      <section className="launch-info-hero launch-info-hero--centered">
        <div>
          <p className="launch-info-eyebrow">Accessibilité numérique</p>
          <h1>Mbolo doit rester utilisable par le plus grand nombre.</h1>
          <p className="launch-info-lead">
            L’accessibilité est intégrée progressivement à la conception, aux
            composants et aux tests. Cette page décrit les engagements actuels
            sans prétendre à une certification qui n’a pas encore été auditée.
          </p>
        </div>
      </section>

      <section className="launch-info-section">
        <header>
          <p className="launch-info-eyebrow">Engagements actuels</p>
          <h2>Une expérience compréhensible, robuste et adaptable.</h2>
        </header>
        <div className="launch-info-grid">
          {commitments.map(([number, title, description]) => (
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
          <p className="launch-info-eyebrow">Amélioration continue</p>
          <h2>Signaler une difficulté d’utilisation.</h2>
        </div>
        <p>
          Si un contenu ou une action reste inaccessible, utilise la page
          Contact et indique la page concernée, le navigateur et la difficulté
          rencontrée, sans joindre de donnée sensible.
        </p>
      </section>
    </main>
  );
}
