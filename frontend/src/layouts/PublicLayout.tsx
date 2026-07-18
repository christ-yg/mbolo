/**
 * Structure commune des pages publiques.
 *
 * Outlet représente la page correspondant à la route courante.
 */

import { Outlet } from "react-router-dom";

import { PublicHeader } from "../components/navigation/PublicHeader";

export function PublicLayout() {
  return (
    <div className="public-layout">
      <PublicHeader />

      <Outlet />
    </div>
  );
}
