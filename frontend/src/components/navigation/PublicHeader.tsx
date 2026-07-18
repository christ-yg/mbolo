/**
 * Barre de navigation publique de Mbolo.
 *
 * Elle sera affichée sur :
 *
 * - la page d'accueil ;
 * - la page de connexion ;
 * - la page d'inscription ;
 * - les pages publiques futures.
 */

import { NavLink } from "react-router-dom";

import { BrandLogo } from "../common/BrandLogo";
import { LinkButton } from "../common/LinkButton";
import type { NavigationItem } from "../../types/navigation";

/**
 * Les liens sont définis hors du composant afin de ne pas recréer
 * le tableau à chaque rendu React.
 */
const navigationItems: NavigationItem[] = [
  {
    label: "Accueil",
    href: "/",
  },
  {
    label: "Découvrir",
    href: "/discovery",
  },
  {
    label: "Sécurité",
    href: "/safety",
  },
];

export function PublicHeader() {
  return (
    <header className="public-header">
      <div className="public-header__container">
        <BrandLogo />

        <nav
          className="public-header__navigation"
          aria-label="Navigation principale"
        >
          {navigationItems.map((item) => (
            <NavLink
              key={item.href}
              className={({ isActive }) =>
                [
                  "public-header__link",
                  isActive
                    ? "public-header__link--active"
                    : "",
                ]
                  .filter(Boolean)
                  .join(" ")
              }
              to={item.href}
            >
              {item.label}
            </NavLink>
          ))}
        </nav>

        <div className="public-header__actions">
          <LinkButton to="/login" variant="ghost">
            Se connecter
          </LinkButton>

          <LinkButton to="/register" variant="primary">
            Créer un compte
          </LinkButton>
        </div>
      </div>
    </header>
  );
}
