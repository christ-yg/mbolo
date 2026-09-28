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
  let otherDeviceRevoked = false;

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
      await json(route, {
        data: [
          {
            id: "current-device",
            device: "Chrome · Windows",
            ipFingerprint: "ab12cd34",
            createdAt: "2026-09-28T12:00:00Z",
            lastSeenAt: "2026-09-28T15:00:00Z",
            isCurrent: true,
          },
          ...(!otherDeviceRevoked
            ? [{
                id: "other-device",
                device: "Safari · iPhone",
                ipFingerprint: "ef56gh78",
                createdAt: "2026-09-27T12:00:00Z",
                lastSeenAt: "2026-09-28T11:00:00Z",
                isCurrent: false,
              }]
            : []),
        ],
      });
      return;
    }

    if (
      path.endsWith("/auth/security/sessions/other-device/revoke/") &&
      method === "POST"
    ) {
      expect(request.postDataJSON()).toEqual({ current_password: ACCOUNT_PASSWORD });
      expect(request.headers()["x-csrftoken"]).toBe("e2e-account-security-csrf");
      otherDeviceRevoked = true;
      await json(route, { data: { revoked: true } });
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

    if (path.endsWith("/auth/security/revoke-sessions/") && method === "POST") {
      expect(request.postDataJSON()).toEqual({ current_password: ACCOUNT_PASSWORD });
      expect(request.headers()["x-csrftoken"]).toBe("e2e-account-security-csrf");
      await json(route, { data: { revoked: true } });
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

    if (path.endsWith("/auth/security/login-alert-emails/") && method === "PATCH") {
      expect(request.postDataJSON()).toEqual({
        current_password: ACCOUNT_PASSWORD,
        enabled: false,
      });
      expect(request.headers()["x-csrftoken"]).toBe("e2e-account-security-csrf");
      await json(route, { data: { loginAlertEmailsEnabled: false } });
      return;
    }

    if (path.endsWith("/auth/security/deactivate/") && method === "POST") {
      expect(request.postDataJSON()).toEqual({
        current_password: ACCOUNT_PASSWORD,
        confirmation: "DESACTIVER",
      });
      expect(request.headers()["x-csrftoken"]).toBe("e2e-account-security-csrf");
      await json(route, { data: { deactivated: true } });
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

  test("le membre ferme toutes les autres sessions", async ({ page }) => {
    const form = page.getByRole("heading", { name: "Fermer les autres sessions" }).locator("..");

    await form.getByLabel("Mot de passe actuel").fill(ACCOUNT_PASSWORD);
    await form.getByRole("button", { name: "Déconnecter les autres appareils" }).click();

    await expect(page.getByText("Les autres appareils ont été déconnectés.")).toBeVisible();
    await expect(form.getByLabel("Mot de passe actuel")).toHaveValue("");
  });

  test("les e-mails d'alerte peuvent être coupés sans désactiver les notifications internes", async ({ page }) => {
    const form = page
      .getByRole("heading", { name: "Nouvelles connexions par e-mail" })
      .locator("..");

    await form.getByLabel("Mot de passe actuel").fill(ACCOUNT_PASSWORD);
    await form.getByRole("button", { name: "Désactiver les e-mails d’alerte" }).click();

    await expect(
      page.getByText(
        "Les alertes par e-mail sont désactivées. Les notifications internes restent actives.",
      ),
    ).toBeVisible();
    await expect(form.getByRole("button", { name: "Activer les e-mails d’alerte" })).toBeVisible();
  });

  test("un appareil inconnu peut être déconnecté individuellement", async ({ page }) => {
    const device = page.getByText("Safari · iPhone").locator("../..");

    await device.getByLabel("Mot de passe actuel").fill(ACCOUNT_PASSWORD);
    await device.getByRole("button", { name: "Déconnecter cet appareil" }).click();

    await expect(page.getByText("L’appareil sélectionné a été déconnecté.")).toBeVisible();
    await expect(page.getByText("Safari · iPhone")).toHaveCount(0);
    await expect(page.getByText("Chrome · Windows")).toBeVisible();
  });

  test("la désactivation exige le mot-clé exact avant l'appel sensible", async ({ page }) => {
    const form = page.locator(".security-danger-zone__form");

    await form.getByLabel("Mot de passe actuel").fill(ACCOUNT_PASSWORD);
    await form.getByLabel("Écris DESACTIVER").fill("desactiver");
    await form.getByRole("button", { name: "Désactiver mon compte" }).click();

    await expect(page.getByText("Écris exactement DESACTIVER pour confirmer.")).toBeVisible();
    await expect(page).toHaveURL("/account/security");
  });
});
