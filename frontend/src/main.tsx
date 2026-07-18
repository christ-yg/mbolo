/**
 * Point d'entrée du frontend Mbolo.
 *
 * StrictMode active des contrôles supplémentaires pendant
 * le développement React.
 */

import { StrictMode } from "react";
import { createRoot } from "react-dom/client";

import App from "./App";
import "./styles/global.css";

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
