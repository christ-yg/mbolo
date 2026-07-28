/**
 * Page affichée lorsqu'aucune route ne correspond à l'URL.
 */

import { Link } from "react-router-dom";

import "./NotFoundPage.css";

export function NotFoundPage() {
  return (
    <main className="placeholder-page">
      <section className="placeholder-card">
        <p className="placeholder-card__code">404</p>

        <h1>Cette page n’existe pas.</h1>

        <p>
          L’adresse demandée est incorrecte ou la page a été déplacée.
        </p>

        <Link to="/">Retourner à l’accueil</Link>
      </section>
    </main>
  );
}
