/**
 * Logo textuel de Mbolo.
 *
 * Le logo est conservé dans un composant indépendant afin de pouvoir
 * le réutiliser dans :
 *
 * - l'en-tête ;
 * - le pied de page ;
 * - les pages d'authentification ;
 * - les e-mails ou écrans d'accueil futurs.
 */

import { Link } from "react-router-dom";

interface BrandLogoProps {
  /**
   * Variante visuelle utilisée selon le fond.
   */
  variant?: "dark" | "light";
}

export function BrandLogo({
  variant = "dark",
}: BrandLogoProps) {
  return (
    <Link
      className={`brand-logo brand-logo--${variant}`}
      to="/"
      aria-label="Retour à l'accueil Mbolo"
    >
      <span className="brand-logo__symbol" aria-hidden="true">
        M
      </span>

      <span className="brand-logo__text">Mbolo</span>
    </Link>
  );
}
