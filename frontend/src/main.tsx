/**
 * Point d'entrée du frontend Mbolo.
 *
 * L'ordre des feuilles de styles est volontaire :
 *
 * 1. global.css conserve les styles fonctionnels historiques ;
 * 2. premium-foundation.css applique le nouveau design system commun.
 *
 * La fondation premium est chargée en dernier afin d'harmoniser progressivement
 * les pages existantes sans casser leur comportement métier.
 */

import { StrictMode } from "react";
import { createRoot } from "react-dom/client";

import App from "./App";
import "./styles/global.css";
import "./styles/premium-foundation.css";


/**
 * Recherche de l'élément racine déclaré dans index.html.
 */
const rootElement = document.getElementById("root");


/**
 * Une erreur explicite est préférable à une page blanche silencieuse.
 */
if (rootElement === null) {
  throw new Error(
    "Impossible de démarrer Mbolo : l'élément HTML #root est absent.",
  );
}


createRoot(rootElement).render(
  <StrictMode>
    <App />
  </StrictMode>,
);
