/**
 * Bouton de navigation réutilisable.
 *
 * Il utilise React Router au lieu d'une balise <a> classique afin
 * d'éviter le rechargement complet de l'application.
 */

import type { ReactNode } from "react";
import { Link } from "react-router-dom";

interface LinkButtonProps {
  /**
   * Destination du bouton.
   */
  to: string;

  /**
   * Contenu visible du bouton.
   */
  children: ReactNode;

  /**
   * Variante visuelle.
   */
  variant?: "primary" | "secondary" | "ghost";

  /**
   * Classe CSS additionnelle facultative.
   */
  className?: string;
}

export function LinkButton({
  to,
  children,
  variant = "primary",
  className = "",
}: LinkButtonProps) {
  const classes = [
    "link-button",
    `link-button--${variant}`,
    className,
  ]
    .filter(Boolean)
    .join(" ");

  return (
    <Link className={classes} to={to}>
      {children}
    </Link>
  );
}
