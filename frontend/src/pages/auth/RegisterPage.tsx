/**
 * Page temporaire d'inscription.
 */

import { Link } from "react-router-dom";

export function RegisterPage() {
  return (
    <main className="placeholder-page">
      <section className="placeholder-card">
        <p className="section-heading__eyebrow">
          Nouvelle inscription
        </p>

        <h1>Créer un compte Mbolo</h1>

        <p>
          Le formulaire d’inscription relié à Django sera ajouté dans
          la prochaine étape.
        </p>

        <Link to="/">Retourner à l’accueil</Link>
      </section>
    </main>
  );
}
