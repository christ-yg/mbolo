import { expect, test, type Page, type Route } from "@playwright/test";

const ACCOUNT_PASSWORD = "Mbolo!Confidentialite2026";
const DELETE_CONFIRMATION = "SUPPRIMER DEFINITIVEMENT";

async function json(route: Route, body: unknown, status = 200): Promise<void> {
  await route.fulfill({
    status,
    contentType: "application/json",
    body: JSON.stringify(body),
  });
}

async function installPrivacyApi(page: Page): Promise<void> {
  await page.route("**/api/**", async (route) => {
    const request = route.request();
    const path = new URL(request.url()).pathname;
    const method = request.method();

    if (path.endsWith("/auth/me/") && method === "GET") {
      await json(route, {
        id: "11111111-1111-4111-8111-111111111111",
        email: "confidentialite@mbolo.invalid",
        isEmailVerified: true,
        emailTwoFactorEnabled: true,
      });
      return;
    }

    if (path.endsWith("/csrf/") && method === "GET") {
      await json(route, { csrfToken: "e2e-privacy-csrf" });
      return;
    }

    if (path.endsWith("/auth/privacy/export/") && method === "GET") {
      await json(route, {
        account: { email: "confidentialite@mbolo.invalid" },
        profile: { displayName: "Membre Test" },
        secrets: null,
      });
      return;
    }

    if (path.endsWith("/auth/privacy/delete/") && method === "POST") {
      expect(request.postDataJSON()).toEqual({
        current_password: ACCOUNT_PASSWORD,
        confirmation: DELETE_CONFIRMATION,
      });
      expect(request.headers()["x-csrftoken"]).toBe("e2e-privacy-csrf");
      await json(route, { data: { deleted: true } });
      return;
    }

    await json(route, { detail: `Endpoint E2E non simulé: ${method} ${path}` }, 501);
  });
}

test.describe("Centre de confidentialité Mbolo", () => {
  test.beforeEach(async ({ page }) => {
    await installPrivacyApi(page);
    await page.goto("/account/privacy");
    await expect(
      page.getByRole("heading", { name: "Garder le contrôle reste essentiel." }),
    ).toBeVisible();
  });

  test("le membre exporte une copie JSON de ses données", async ({ page }) => {
    await page.getByRole("button", { name: /Exporter mes données/ }).click();

    await expect(
      page.getByText("Ton export JSON a été préparé et téléchargé de manière sécurisée."),
    ).toBeVisible();
  });

  test("la suppression reste verrouillée sans phrase exacte", async ({ page }) => {
    const form = page.locator(".privacy-center-danger__form");

    await form.getByLabel("Mot de passe actuel").fill(ACCOUNT_PASSWORD);
    await form.getByLabel("Phrase de confirmation").fill("SUPPRIMER");

    await expect(
      form.getByRole("button", { name: /Continuer vers la confirmation/ }),
    ).toBeDisabled();
    await expect(page.getByRole("dialog")).toHaveCount(0);
  });

  test("la double confirmation transmet uniquement les valeurs attendues", async ({ page }) => {
    const form = page.locator(".privacy-center-danger__form");

    await form.getByLabel("Mot de passe actuel").fill(ACCOUNT_PASSWORD);
    await form.getByLabel("Phrase de confirmation").fill(DELETE_CONFIRMATION);
    await form.getByRole("button", { name: /Continuer vers la confirmation/ }).click();

    await expect(
      page.getByRole("heading", { name: "Supprimer définitivement ce compte ?" }),
    ).toBeVisible();
    await page.getByRole("button", { name: "Oui, supprimer définitivement" }).click();

    await expect(page).toHaveURL("/");
  });
});
