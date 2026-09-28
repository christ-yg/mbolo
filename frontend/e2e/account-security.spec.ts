import { expect, test, type Page, type Route } from "@playwright/test";

const ACCOUNT_PASSWORD = "Mbolo!Compte2026";
const NEW_PASSWORD = "Mbolo!Nouveau2026";

async function json(route: Route, body: unknown, status = 200): Promise<void> {
  await route.fulfill({
    status,
    contentType: "application/json",
    body: JSON.stringify(body),
  });
}

async function installSecurityApi(page: Page): Promise<void> {
  let twoFactorEnabled = false;

  await page.route("**/api/**", async (route) => {
    const request = route.request();
    const path = new URL(request.url()).pathname;
    const method = request.method();

    if (path.endsWith("/auth/me/") && method === "GET") {
      await json(route, {
        id: "11111111-1111-4111-8111-111111111111",
        email: "securite-compte@mbolo.invalid",
        isEmailVerified: true,
        emailTwoFactorEnabled: twoFactorEnabled,
      });
      return;
    }

    if (path.endsWith("/csrf/") && method === "GET") {
      await json(route, { csrfToken: "e2e-account-security-csrf" });
      return;
    }

    if (path.endsWith("/auth/security/login-activity/") && method === "GET") {
      await json(route, { data: [] });
      return;
    }

    if (path.endsWith("/auth/security/events/") && method === "GET") {
      await json(route, { data: [] });
      return;
    }

    if (path.endsWith("/auth/security/sessions/") && method === "GET") {
      await json(route, { data: [] });
      return;
    }

    if (path.endsWith("/auth/security/login-alert-emails/") && method === "GET") {
      await json(route, { data: { loginAlertEmailsEnabled: true } });
      return;
    }

    if (path.endsWith("/auth/security/change-password/") && method === "POST") {
      expect(request.postDataJSON()).toEqual({
        current_password: ACCOUNT_PASSWORD,
        new_password: NEW_PASSWORD,
        new_password_confirmation: NEW_PASSWORD,
      });
      expect(request.headers()["x-csrftoken"]).toBe("e2e-account-security-csrf");
      await json(route, { data: { changed: true } });
      return;
    }

    if (path.endsWith("/auth/security/email-2fa/") && method === "PATCH") {
      expect(request.postDataJSON()).toEqual({
        current_password: ACCOUNT_PASSWORD,
        enabled: true,
      });
      expect(request.headers()["x-csrftoken"]).toBe("e2e-account-security-csrf");
      twoFactorEnabled = true;
      await json(route, { data: { emailTwoFactorEnabled: true } });
      return;
    }

    await json(route, { detail: `Endpoint E2E non simulé: ${method} ${path}` }, 501);
  });
}

test.describe("Centre de sécurité du compte Mbolo", () => {
  test.beforeEach(async ({ page }) => {
    await installSecurityApi(page);
    await page.goto("/account/security");
    await expect(page.getByRole("heading", { name: "Sécurité de mon compte" })).toBeVisible();
  });

  test("le membre remplace son mot de passe et ferme les autres sessions", async ({ page }) => {
    const form = page.getByRole("heading", { name: "Changer mon mot de passe" }).locator("..");

    await form.getByLabel("Mot de passe actuel").fill(ACCOUNT_PASSWORD);
    await form.getByLabel("Nouveau mot de passe").fill(NEW_PASSWORD);
    await form.getByLabel("Confirmation").fill(NEW_PASSWORD);
    await form.getByRole("button", { name: "Changer le mot de passe" }).click();

    await expect(
      page.getByText("Mot de passe modifié. Toutes les autres sessions ont été fermées."),
    ).toBeVisible();
    await expect(form.getByLabel("Mot de passe actuel")).toHaveValue("");
  });

  test("le membre active la double authentification par e-mail", async ({ page }) => {
    const form = page
      .getByRole("heading", { name: "Double authentification par e-mail" })
      .locator("..");

    await expect(page.getByText("Standard", { exact: true })).toBeVisible();
    await form.getByLabel("Mot de passe actuel").fill(ACCOUNT_PASSWORD);
    await form.getByRole("button", { name: "Activer la double authentification" }).click();

    await expect(
      page.getByText(
        "Double authentification activée. Un code sera demandé à la prochaine connexion.",
      ),
    ).toBeVisible();
    await expect(page.getByText("Élevé", { exact: true })).toBeVisible();
    await expect(
      form.getByRole("button", { name: "Désactiver la double authentification" }),
    ).toBeVisible();
  });
});
