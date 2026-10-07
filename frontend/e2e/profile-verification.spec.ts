import { expect, test, type Page, type Route } from "@playwright/test";

const INITIAL_STATE = {
  status: "not_submitted",
  status_label: "Non envoyé",
  can_submit: true,
  is_verified: false,
  rejection_reason: "",
  submitted_at: null,
  reviewed_at: null,
  updated_at: "2026-09-28T15:00:00Z",
};

const PENDING_STATE = {
  ...INITIAL_STATE,
  status: "pending",
  status_label: "En attente",
  can_submit: false,
  submitted_at: "2026-09-28T16:00:00Z",
  updated_at: "2026-09-28T16:00:00Z",
};

async function json(route: Route, body: unknown, status = 200): Promise<void> {
  await route.fulfill({
    status,
    contentType: "application/json",
    body: JSON.stringify(body),
  });
}

async function installVerificationApi(page: Page): Promise<void> {
  let state = INITIAL_STATE;

  await page.route("**/api/**", async (route) => {
    const request = route.request();
    const path = new URL(request.url()).pathname;
    const method = request.method();

    if (path.endsWith("/auth/me/") && method === "GET") {
      await json(route, {
        id: "11111111-1111-4111-8111-111111111111",
        email: "verification-profil@mbolo.invalid",
        isEmailVerified: true,
        emailTwoFactorEnabled: true,
      });
      return;
    }

    if (path.endsWith("/profiles/verification/me/") && method === "GET") {
      await json(route, state);
      return;
    }

    if (path.endsWith("/profiles/verification/me/") && method === "POST") {
      expect(request.headers()["content-type"]).toContain("multipart/form-data");
      expect(request.postDataBuffer()?.toString()).toContain("selfie-test.png");
      state = PENDING_STATE;
      await json(route, state, 201);
      return;
    }

    await json(route, { detail: `Endpoint E2E non simulé: ${method} ${path}` }, 501);
  });
}

test.describe("Vérification de confiance du profil Mbolo", () => {
  test.beforeEach(async ({ page }) => {
    await installVerificationApi(page);
    await page.goto("/profile/verification");
    await expect(page.getByRole("heading", { name: "Vérifier mon profil" })).toBeVisible();
    await expect(page.getByText("Profil non vérifié", { exact: true })).toBeVisible();
  });

  test("un fichier qui n'est pas une image est refusé localement", async ({ page }) => {
    await page.getByLabel("Sélectionner mon selfie").setInputFiles({
      name: "document.txt",
      mimeType: "text/plain",
      buffer: Buffer.from("ceci n'est pas un selfie"),
    });

    await expect(
      page.getByText("Choisis une image au format JPEG, PNG ou WebP."),
    ).toBeVisible();
    await expect(page.getByRole("button", { name: /Envoyer ma demande/ })).toBeDisabled();
  });

  test("un selfie valide passe en examen sans être publié", async ({ page }) => {
    await page.getByLabel("Sélectionner mon selfie").setInputFiles({
      name: "selfie-test.png",
      mimeType: "image/png",
      buffer: Buffer.from("89504e470d0a1a0a", "hex"),
    });

    await expect(page.getByAltText("Aperçu local du selfie sélectionné")).toBeVisible();
    await page.getByRole("button", { name: /Envoyer ma demande/ }).click();

    await expect(
      page.getByText("Ta demande a été transmise de manière sécurisée."),
    ).toBeVisible();
    await expect(page.getByText("Demande reçue", { exact: true })).toBeVisible();
    await expect(page.getByText("Envoi temporairement indisponible")).toBeVisible();
    await expect(page.getByText("Jamais visible sur ton profil")).toBeVisible();
  });
});
