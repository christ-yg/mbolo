import { expect, test, type Page, type Route } from "@playwright/test";

const PROFILE_ID = "22222222-2222-4222-8222-222222222222";

const PROFILE = {
  id: PROFILE_ID,
  display_name: "Arielle Test",
  age: 29,
  gender: "woman",
  gender_label: "Femme",
  city: "libreville",
  city_label: "Libreville",
  biography: "Profil fictif utilisé pour vérifier la sécurité Mbolo.",
  dating_intent: "serious_relationship",
  dating_intent_label: "Relation sérieuse",
  is_verified: true,
  photos: [],
  relationship: "match",
  current_decision: "like",
};

async function json(route: Route, body: unknown, status = 200): Promise<void> {
  await route.fulfill({
    status,
    contentType: "application/json",
    body: JSON.stringify(body),
  });
}

async function installProfileApi(page: Page): Promise<void> {
  await page.route("**/api/**", async (route) => {
    const request = route.request();
    const path = new URL(request.url()).pathname;

    if (path.endsWith("/auth/me/") && request.method() === "GET") {
      await json(route, {
        id: "11111111-1111-4111-8111-111111111111",
        email: "securite-profil@mbolo.invalid",
        isEmailVerified: true,
        emailTwoFactorEnabled: true,
      });
      return;
    }

    if (
      path.endsWith(`/profiles/public/${PROFILE_ID}/`) &&
      request.method() === "GET"
    ) {
      await json(route, PROFILE);
      return;
    }

    await route.fallback();
  });
}

async function openSafetyAction(page: Page, action: string): Promise<void> {
  await page.getByRole("button", { name: "Actions de sécurité" }).click();
  await page.getByRole("button", { name: action }).click();
}

test.describe("Actions de sécurité depuis un profil Mbolo", () => {
  test.beforeEach(async ({ page }) => {
    await installProfileApi(page);
  });

  test("un signalement transmet le motif et les faits puis confirme la confidentialité", async ({ page }) => {
    await page.route(`**/api/v1/safety/profiles/${PROFILE_ID}/report/`, async (route) => {
      expect(route.request().method()).toBe("POST");
      expect(route.request().postDataJSON()).toEqual({
        reason: "scam",
        description: "Demande insistante de transfert d’argent.",
      });
      await json(route, {
        created: true,
        message: "Signalement transmis confidentiellement à la modération.",
      }, 201);
    });

    await page.goto(`/profiles/${PROFILE_ID}`);
    await openSafetyAction(page, "Signaler ce profil");
    await page.getByLabel("Motif").selectOption("scam");
    await page.getByLabel("Informations complémentaires").fill(
      "  Demande insistante de transfert d’argent.  ",
    );
    await page.getByRole("button", { name: "Envoyer le signalement" }).click();

    await expect(page.getByRole("dialog")).toHaveCount(0);
    await expect(
      page.getByText("Signalement transmis confidentiellement à la modération."),
    ).toBeVisible();
  });

  test("un signalement refusé reste modifiable et affiche la raison du serveur", async ({ page }) => {
    await page.route(`**/api/v1/safety/profiles/${PROFILE_ID}/report/`, async (route) => {
      await json(route, { detail: "Ce profil a déjà été signalé récemment." }, 409);
    });

    await page.goto(`/profiles/${PROFILE_ID}`);
    await openSafetyAction(page, "Signaler ce profil");
    await page.getByLabel("Informations complémentaires").fill("Nouveaux faits observés.");
    await page.getByRole("button", { name: "Envoyer le signalement" }).click();

    await expect(page.getByRole("dialog", { name: "Signaler ce profil" })).toBeVisible();
    await expect(page.getByRole("alert")).toContainText(
      "Ce profil a déjà été signalé récemment.",
    );
    await expect(page.getByLabel("Informations complémentaires")).toHaveValue(
      "Nouveaux faits observés.",
    );
  });

  test("un blocage confirmé désactive la relation et renvoie vers Découvrir", async ({ page }) => {
    await page.route(`**/api/v1/safety/profiles/${PROFILE_ID}/block/`, async (route) => {
      expect(route.request().postDataJSON()).toEqual({ confirm: true });
      await json(route, {
        created: true,
        message: "Profil bloqué.",
        deactivated_matches: 1,
      }, 201);
    });

    await page.route("**/api/v1/profiles/discovery/**", async (route) => {
      await json(route, { count: 0, next: null, previous: null, results: [] });
    });

    await page.goto(`/profiles/${PROFILE_ID}`);
    await openSafetyAction(page, "Bloquer ce profil");
    await expect(page.getByText("Un match actif sera désactivé.")).toBeVisible();
    await page.getByRole("button", { name: "Confirmer le blocage" }).click();

    await expect(page).toHaveURL(/\/discovery$/);
  });

  test("un blocage échoué ne ferme pas la confirmation et expose une erreur utile", async ({ page }) => {
    await page.route(`**/api/v1/safety/profiles/${PROFILE_ID}/block/`, async (route) => {
      await json(route, { detail: "Blocage temporairement indisponible." }, 503);
    });

    await page.goto(`/profiles/${PROFILE_ID}`);
    await openSafetyAction(page, "Bloquer ce profil");
    await page.getByRole("button", { name: "Confirmer le blocage" }).click();

    await expect(page.getByRole("dialog", { name: "Bloquer Arielle Test ?" })).toBeVisible();
    await expect(page.getByRole("alert")).toContainText(
      "Blocage temporairement indisponible.",
    );
    await expect(page).toHaveURL(new RegExp(`/profiles/${PROFILE_ID}$`));
  });

  test("une coupure réseau affiche un message sûr et conserve le signalement", async ({ page }) => {
    await page.route(`**/api/v1/safety/profiles/${PROFILE_ID}/report/`, async (route) => {
      await route.abort("failed");
    });

    await page.goto(`/profiles/${PROFILE_ID}`);
    await openSafetyAction(page, "Signaler ce profil");
    await page.getByLabel("Informations complémentaires").fill(
      "Comportement observé avant la coupure.",
    );
    await page.getByRole("button", { name: "Envoyer le signalement" }).click();

    await expect(page.getByRole("alert")).toContainText(
      "Le service est temporairement indisponible. Vérifie ta connexion puis réessaie.",
    );
    await expect(page.getByLabel("Informations complémentaires")).toHaveValue(
      "Comportement observé avant la coupure.",
    );
    await expect(page.getByText("Failed to fetch")).toHaveCount(0);
  });

  test("le bouton est verrouillé pendant l'envoi pour éviter les doublons", async ({ page }) => {
    let requestCount = 0;

    await page.route(`**/api/v1/safety/profiles/${PROFILE_ID}/report/`, async (route) => {
      requestCount += 1;
      await new Promise((resolve) => setTimeout(resolve, 250));
      await json(route, {
        created: true,
        message: "Signalement unique transmis.",
      }, 201);
    });

    await page.goto(`/profiles/${PROFILE_ID}`);
    await openSafetyAction(page, "Signaler ce profil");
    const submitButton = page.getByRole("button", { name: "Envoyer le signalement" });
    await submitButton.click();

    await expect(page.getByRole("button", { name: "Envoi…" })).toBeDisabled();
    await expect(page.getByText("Signalement unique transmis.")).toBeVisible();
    await expect.poll(() => requestCount).toBe(1);
  });
});
