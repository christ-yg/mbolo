/**
 * Point d'entrée du frontend Mbolo.
 *
 * Ordre des styles :
 * 1. styles historiques ;
 * 2. fondation premium ;
 * 3. typographie compacte ;
 * 4. page Découvrir ;
 * 5. page Mes matchs.
 */

import { StrictMode } from "react";
import { createRoot } from "react-dom/client";

import App from "./App";
import "./styles/global.css";
import "./styles/premium-foundation.css";
import "./styles/compact-typography.css";
import "./styles/discovery-premium.css";
import "./styles/matches-premium.css";


const rootElement = document.getElementById("root");


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
