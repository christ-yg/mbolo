/**
 * Page temporaire de connexion.
 *
 * Le formulaire sécurisé sera construit dans la prochaine étape.
 */

import { Link } from "react-router-dom";

export function LoginPage() {
  return (
    <main className="placeholder-page">
      <section className="placeholder-card">
        <p className="section-heading__eyebrow">Authentification</p>

        <h1>Connexion à Mbolo</h1>

        <p>
          Le formulaire de connexion sécurisé arrive dans la prochaine
          étape.
        </p>

        <Link to="/">Retourner à l’accueil</Link>
      </section>
    </main>
  );
}
