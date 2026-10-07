import { expect, test, type Page, type Route } from "@playwright/test";

async function json(route: Route, body: unknown, status = 200): Promise<void> {
  await route.fulfill({
    status,
    contentType: "application/json",
    body: JSON.stringify(body),
  });
}

async function installAuthenticatedMember(page: Page): Promise<void> {
  await page.route("**/api/**", async (route) => {
    const request = route.request();
    const url = new URL(request.url());
    const path = url.pathname;
    const method = request.method();

    if (path.endsWith("/auth/me/") && method === "GET") {
      await json(route, {
        id: "11111111-1111-4111-8111-111111111111",
        email: "securite-communaute@mbolo.invalid",
        isEmailVerified: true,
        emailTwoFactorEnabled: true,
      });
      return;
    }

    await route.fallback();
  });
}

test.describe("Sécurité communautaire Mbolo", () => {
  test.beforeEach(async ({ page }) => {
    await installAuthenticatedMember(page);
  });

  test("le membre suit le statut public de ses signalements sans notes internes", async ({ page }) => {
    await page.route("**/api/v1/safety/reports/**", async (route) => {
      await json(route, {
        count: 2,
        next: null,
        previous: null,
        results: [
          {
            id: "report-a",
            reported_profile: {
              id: "profile-a",
              display_name: "Amina",
              age: 29,
              city: "Libreville",
              photos: [],
            },
            reason: "scam",
            description: "Demande d'argent répétée.",
            status: "under_review",
            created_at: "2026-09-27T10:00:00Z",
            updated_at: "2026-09-28T14:00:00Z",
          },
          {
            id: "report-b",
            reported_profile: null,
            reason: "fake_profile",
            description: "",
            status: "resolved",
            created_at: "2026-09-20T10:00:00Z",
            updated_at: "2026-09-21T10:00:00Z",
          },
        ],
      });
    });

    await page.goto("/reports");

    await expect(page.getByRole("heading", { name: "Mes signalements" })).toBeVisible();
    await expect(page.getByText("Amina", { exact: true })).toBeVisible();
    await expect(page.getByText("Arnaque", { exact: true })).toBeVisible();
    await expect(page.getByText("En cours d’examen", { exact: true })).toBeVisible();
    await expect(page.getByText("Profil indisponible", { exact: true })).toBeVisible();
    await expect(page.getByText("Traité", { exact: true })).toBeVisible();
    await expect(page.getByText("identité du modérateur", { exact: false })).toBeVisible();
  });

  test("la pagination ajoute les dossiers sans dupliquer ceux déjà affichés", async ({ page }) => {
    await page.route("**/api/v1/safety/reports/**", async (route) => {
      const currentPage = new URL(route.request().url()).searchParams.get("page");

      await json(route, {
        count: 2,
        next: currentPage === "1" ? "?page=2" : null,
        previous: currentPage === "2" ? "?page=1" : null,
        results: currentPage === "1"
          ? [{
              id: "report-a",
              reported_profile: null,
              reason: "spam",
              description: "Messages répétés.",
              status: "pending",
              created_at: "2026-09-28T10:00:00Z",
              updated_at: "2026-09-28T10:00:00Z",
            }]
          : [
              {
                id: "report-a",
                reported_profile: null,
                reason: "spam",
                description: "Messages répétés.",
                status: "pending",
                created_at: "2026-09-28T10:00:00Z",
                updated_at: "2026-09-28T10:00:00Z",
              },
              {
                id: "report-b",
                reported_profile: null,
                reason: "threat",
                description: "Menace explicite.",
                status: "under_review",
                created_at: "2026-09-27T10:00:00Z",
                updated_at: "2026-09-28T11:00:00Z",
              },
            ],
      });
    });

    await page.goto("/reports");
    await page.getByRole("button", { name: "Charger plus de dossiers" }).click();

    await expect(page.getByText("Messages répétés.")).toHaveCount(1);
    await expect(page.getByText("Menace explicite.")).toBeVisible();
    await expect(page.getByRole("button", { name: "Charger plus de dossiers" })).toHaveCount(0);
  });

  test("annuler un déblocage conserve le profil dans la liste privée", async ({ page }) => {
    await installBlockedUsersApi(page);
    await page.goto("/blocked-users");

    await page.getByRole("button", { name: "Débloquer ce profil" }).click();
    await expect(page.getByRole("dialog", { name: "Débloquer David ?" })).toBeVisible();
    await page.getByRole("button", { name: "Annuler" }).click();

    await expect(page.getByRole("dialog")).toHaveCount(0);
    await expect(page.getByText("David", { exact: true })).toBeVisible();
  });

  test("confirmer un déblocage retire le profil sans restaurer match ni conversation", async ({ page }) => {
    let deleteCalled = false;
    await installBlockedUsersApi(page, () => {
      deleteCalled = true;
    });
    await page.goto("/blocked-users");

    await page.getByRole("button", { name: "Débloquer ce profil" }).click();
    await page.getByRole("button", { name: "Confirmer le déblocage" }).click();

    await expect.poll(() => deleteCalled).toBe(true);
    await expect(page.getByText("David a été débloqué.", { exact: false })).toBeVisible();
    await expect(page.getByText("L’ancien match et l’ancienne conversation ne sont pas restaurés.", { exact: false })).toBeVisible();
    await expect(page.getByRole("heading", { name: "Aucun profil bloqué" })).toBeVisible();
  });
});

async function installBlockedUsersApi(
  page: Page,
  onDelete: () => void = () => undefined,
): Promise<void> {
  await page.route("**/api/v1/safety/blocks/**", async (route) => {
    const method = route.request().method();

    if (method === "DELETE") {
      onDelete();
      await route.fulfill({ status: 204 });
      return;
    }

    await json(route, {
      count: 1,
      next: null,
      previous: null,
      results: [{
        id: "block-david",
        blocked_profile: {
          id: "profile-david",
          display_name: "David",
          age: 31,
          city: "Port-Gentil",
          city_label: "Port-Gentil",
          photos: [],
        },
        created_at: "2026-09-28T12:00:00Z",
      }],
    });
  });
}