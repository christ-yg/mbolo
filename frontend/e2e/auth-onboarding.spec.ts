import { expect, test, type Page, type Route } from "@playwright/test";

const NEW_MEMBER = {
  id: "99999999-9999-4999-8999-999999999999",
  email: "nouveau.membre@mbolo.invalid",
  is_email_verified: false,
  email_2fa_enabled: false,
};

const STRONG_PASSWORD = "Mbolo!Afrique2026";
const TWO_FACTOR_EMAIL = "securite@mbolo.invalid";
const TWO_FACTOR_CHALLENGE = "e2e-two-factor-challenge";
const EMAIL_VERIFICATION_TOKEN = "e2e-email-verification-token";

async function json(route: Route, body: unknown, status = 200): Promise<void> {
  await route.fulfill({
    status,
    contentType: "application/json",
    body: JSON.stringify(body),
  });
}

async function installAnonymousApi(page: Page): Promise<void> {
  let isAuthenticated = false;

  await page.route("**/api/**", async (route) => {
    const request = route.request();
    const path = new URL(request.url()).pathname;
    const method = request.method();

    if (path.includes("/api/v1/v1/")) {
      await json(route, { detail: "Préfixe API dupliqué détecté" }, 500);
      return;
    }

    if (path.endsWith("/auth/me/") && method === "GET") {
      if (isAuthenticated) {
        await json(route, { data: NEW_MEMBER });
        return;
      }

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

    if (path.endsWith("/auth/password-reset/request/") && method === "POST") {
      expect(request.postDataJSON()).toEqual({ email: NEW_MEMBER.email });
      expect(request.headers()["x-csrftoken"]).toBe("e2e-onboarding-csrf-token");
      await json(route, {
        data: {
          message: "Demande traitée.",
        },
      });
      return;
    }

    if (path.endsWith("/auth/login/") && method === "POST") {
      expect(request.postDataJSON()).toEqual({
        email: TWO_FACTOR_EMAIL,
        password: STRONG_PASSWORD,
      });
      expect(request.headers()["x-csrftoken"]).toBe("e2e-onboarding-csrf-token");
      await json(route, {
        data: {
          requiresTwoFactor: true,
          challengeToken: TWO_FACTOR_CHALLENGE,
          maskedEmail: "s*******@mbolo.invalid",
        },
      });
      return;
    }

    if (path.endsWith("/auth/login/2fa/confirm/") && method === "POST") {
      expect(request.postDataJSON()).toEqual({
        challenge_token: TWO_FACTOR_CHALLENGE,
        code: "123456",
      });
      expect(request.headers()["x-csrftoken"]).toBe("e2e-onboarding-csrf-token");
      isAuthenticated = true;
      await json(route, { data: NEW_MEMBER });
      return;
    }

    if (path.endsWith("/auth/email-verification/confirm/") && method === "POST") {
      expect(request.postDataJSON()).toEqual({ token: EMAIL_VERIFICATION_TOKEN });
      expect(request.headers()["x-csrftoken"]).toBe("e2e-onboarding-csrf-token");
      await json(route, {
        data: {
          email: NEW_MEMBER.email,
          isEmailVerified: true,
        },
      });
      return;
    }

    if (path.endsWith("/profiles/discovery/") && method === "GET") {
      await json(route, {
        count: 0,
        next: null,
        previous: null,
        results: [],
      });
      return;
    }

    if (path.endsWith("/interactions/rewind/") && method === "GET") {
      await json(route, {
        entitled: false,
        available: false,
        reason: "premium_required",
      });
      return;
    }

    if (path.endsWith("/super-like/") && method === "GET") {
      await json(route, {
        entitled: false,
        daily_limit: 0,
        remaining_today: 0,
      });
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

  test("la récupération du mot de passe protège l'existence des comptes", async ({ page }) => {
    await page.goto("/forgot-password");

    await page.getByLabel("Adresse e-mail").fill("  Nouveau.Membre@MBOLO.invalid  ");
    await page.getByRole("button", { name: "Envoyer le lien" }).click();

    await expect(
      page.getByText(
        "Si un compte éligible correspond à cette adresse, un lien vient d’être envoyé.",
      ),
    ).toBeVisible();
    await expect(page.getByText("Demande traitée.")).toHaveCount(0);
  });

  test("la connexion 2FA exige exactement six chiffres", async ({ page }) => {
    await page.goto("/login");

    await page.getByLabel("Adresse e-mail").fill(TWO_FACTOR_EMAIL);
    await page.getByLabel("Mot de passe", { exact: true }).fill(STRONG_PASSWORD);
    await page.getByRole("button", { name: "Se connecter" }).click();

    await expect(page.getByLabel("Code temporaire")).toBeVisible();
    await expect(page.getByText("s*******@mbolo.invalid", { exact: false })).toBeVisible();
    await page.getByLabel("Code temporaire").fill("12345");
    await page.getByRole("button", { name: "Confirmer la connexion" }).click();

    await expect(page.getByText("Saisis le code à six chiffres reçu par e-mail.")).toBeVisible();

    await page.getByLabel("Code temporaire").fill("123456");
    await page.getByRole("button", { name: "Confirmer la connexion" }).click();

    await expect(page).toHaveURL("/discovery");
    await expect(
      page.getByRole("heading", {
        name: "Tu as vu tous les profils disponibles pour le moment.",
      }),
    ).toBeVisible();
  });

  test("un lien incomplet est refusé sans appel de confirmation", async ({ page }) => {
    await page.goto("/verify-email");

    await expect(
      page.getByRole("heading", { name: "Vérification impossible" }),
    ).toBeVisible();
    await expect(
      page.getByText("Le lien de vérification est incomplet ou invalide."),
    ).toBeVisible();
  });

  test("un jeton valide confirme l'adresse e-mail", async ({ page }) => {
    await page.goto(`/verify-email?token=${EMAIL_VERIFICATION_TOKEN}`);

    await expect(
      page.getByRole("heading", { name: "Adresse confirmée" }),
    ).toBeVisible();
    await expect(
      page.getByText(`L’adresse ${NEW_MEMBER.email} est maintenant vérifiée.`),
    ).toBeVisible();
    await expect(
      page.getByRole("link", { name: /Continuer vers la connexion/ }),
    ).toHaveAttribute("href", "/login");
  });
});
