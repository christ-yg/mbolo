import { expect, test } from "@playwright/test";

/**
 * Parcours publics de Mbolo.
 * Ces scénarios ne nécessitent aucun compte utilisateur.
 */
test.describe("Mbolo — parcours public", () => {
  test(
    "la page d'accueil répond correctement",
    async ({ page }) => {
      const response = await page.goto("/");

      expect(response).not.toBeNull();
      expect(response?.ok()).toBeTruthy();

      /**
       * On confirme qu'il ne s'agit pas seulement d'une réponse HTTP vide :
       * l'application React Mbolo doit effectivement être rendue.
       */
      await expect(page.locator("body")).toContainText(
        "Mbolo",
      );
    },
  );

  test(
    "la page de connexion est accessible",
    async ({ page }) => {
      await page.goto("/login");

      await expect(
        page.locator('input[name="email"]'),
      ).toBeVisible();

      await expect(
        page.locator('input[name="password"]'),
      ).toBeVisible();
    },
  );

  /**
   * Contrôle de sécurité : une route privée ne doit jamais rester accessible
   * à un navigateur qui ne possède pas de session Django authentifiée.
   */
  test(
    "un visiteur anonyme ne peut pas accéder à la découverte",
    async ({ page }) => {
      await page.goto("/discovery");

      await expect(page).toHaveURL(
        /\/login(?:$|[?#])/,
      );
    },
  );
});
