import { expect, test, type Page, type Route } from "@playwright/test";

const NEW_MEMBER = {
  id: "99999999-9999-4999-8999-999999999999",
  email: "nouveau.membre@mbolo.invalid",
  is_email_verified: false,
  email_2fa_enabled: false,
};

const STRONG_PASSWORD = "Mbolo!Afrique2026";

async function json(route: Route, body: unknown, status = 200): Promise<void> {
  await route.fulfill({
    status,
    contentType: "application/json",
    body: JSON.stringify(body),
  });
}

async function installAnonymousApi(page: Page): Promise<void> {
  await page.route("**/api/**", async (route) => {
    const request = route.request();
    const path = new URL(request.url()).pathname;
    const method = request.method();

    if (path.includes("/api/v1/v1/")) {
      await json(route, { detail: "Préfixe API dupliqué détecté" }, 500);
      return;
    }

    if (path.endsWith("/auth/me/") && method === "GET") {
      await json(route, { detail: "Non authentifié." }, 401);
      return;
    }

    if (path.endsWith("/csrf/") && method === "GET") {
      await json(route, { csrfToken: "e2e-onboarding-csrf-token" });
      return;
    }

    if (path.endsWith("/auth/register/") && method === "POST") {
      const payload = request.postDataJSON() as Record<string, unknown>;

      expect(payload).toEqual({
        email: NEW_MEMBER.email,
        password: STRONG_PASSWORD,
        password_confirmation: STRONG_PASSWORD,
        accept_terms: true,
        confirm_adult: true,
      });
      expect(request.headers()["x-csrftoken"]).toBe("e2e-onboarding-csrf-token");

      await json(route, { data: NEW_MEMBER }, 201);
      return;
    }

    await json(route, { detail: `Endpoint E2E non simulé: ${method} ${path}` }, 501);
  });
}

test.describe("Arrivée d'un nouveau membre Mbolo", () => {
  test.beforeEach(async ({ page }) => {
    await installAnonymousApi(page);
  });

  test("le formulaire bloque une inscription incomplète", async ({ page }) => {
    await page.goto("/register");
    await page.getByRole("button", { name: "Créer mon compte" }).click();

    await expect(page.getByText("L’adresse e-mail est obligatoire.")).toBeVisible();
    await expect(page.getByText("Le mot de passe est obligatoire.")).toBeVisible();
    await expect(page.getByText("Confirme ton mot de passe.")).toBeVisible();
    await expect(
      page.getByText("Confirme ta majorité et accepte les documents légaux."),
    ).toBeVisible();
  });

  test("un adulte crée son compte puis retrouve son e-mail sur la connexion", async ({ page }) => {
    await page.goto("/register");

    await page.getByLabel("Adresse e-mail").fill("  Nouveau.Membre@MBOLO.invalid  ");
    await page.getByLabel("Mot de passe", { exact: true }).fill(STRONG_PASSWORD);
    await page.getByLabel("Confirmation du mot de passe").fill(STRONG_PASSWORD);
    await page.getByRole("checkbox").check();
    await page.getByRole("button", { name: "Créer mon compte" }).click();

    await expect(page).toHaveURL("/login");
    await expect(
      page.getByText("Ton compte a été créé. Vérifie ton adresse e-mail avant de te connecter."),
    ).toBeVisible();
    await expect(page.getByLabel("Adresse e-mail")).toHaveValue(NEW_MEMBER.email);
  });
});
