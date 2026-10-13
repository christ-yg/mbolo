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
    await expect(page.locator(".reports-premium-list").getByText("En cours d’examen", { exact: true })).toBeVisible();
    await expect(page.getByText("Profil indisponible", { exact: true })).toBeVisible();
    await expect(page.locator(".reports-premium-list").getByText("Traité", { exact: true })).toBeVisible();
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

test.describe("Centre de confiance interactif Web", () => {
  test.beforeEach(async ({ page }) => { await installAuthenticatedMember(page); });

  test("recherche, statut et réinitialisation des signalements", async ({ page }) => {
    await page.route("**/api/v1/safety/reports/**", route => json(route, {
      count: 2, next: null, previous: null, results: [
        { id: "a", reported_profile: null, reason: "spam", description: "Messages répétés", status: "pending", created_at: "2026-10-12T10:00:00Z", updated_at: "2026-10-12T10:00:00Z" },
        { id: "b", reported_profile: null, reason: "scam", description: "Demande argent", status: "resolved", created_at: "2026-10-11T10:00:00Z", updated_at: "2026-10-12T10:00:00Z" },
      ],
    }));
    await page.goto("/reports");
    const cards = page.locator(".reports-premium-card");
    await expect(cards).toHaveCount(2);
    await page.getByRole("searchbox").fill("argent");
    await expect(cards).toHaveCount(1);
    await page.getByLabel("Statut du dossier", { exact: true }).selectOption("pending");
    await expect(cards).toHaveCount(0);
    await page.getByRole("button", { name: "Réinitialiser les filtres" }).click();
    await expect(cards).toHaveCount(2);
    await page.getByLabel("Ordre chronologique", { exact: true }).selectOption("oldest");
    await expect(cards.first()).toContainText("Demande argent");
  });

  test("recherche des profils bloqués sans les débloquer", async ({ page }) => {
    let deletes = 0;
    await installBlockedUsersApi(page, () => { deletes += 1; });
    await page.goto("/blocked-users");
    await page.getByRole("searchbox").fill("introuvable");
    await expect(page.locator(".blocked-user-card")).toHaveCount(0);
    await page.getByRole("button", { name: "Réinitialiser les filtres" }).click();
    await expect(page.getByText("David", { exact: true })).toBeVisible();
    expect(deletes).toBe(0);
  });

  test("un déblocage paginé recharge la première page", async ({ page }) => {
    let deleted = false;
    const pages: string[] = [];
    await page.route("**/api/v1/safety/blocks/**", async route => {
      if (route.request().method() === "DELETE") { deleted = true; await route.fulfill({ status: 204 }); return; }
      const current = new URL(route.request().url()).searchParams.get("page") ?? "1";
      pages.push(current);
      const person = deleted ? "Alice" : "David";
      await json(route, { count: deleted ? 1 : 2, next: deleted ? null : "?page=2", previous: null,
        results: [{ id: person, blocked_profile: { id: person, display_name: person, age: 30, city: "Libreville", photos: [] }, created_at: "2026-10-12T10:00:00Z" }] });
    });
    await page.goto("/blocked-users");
    await page.getByRole("button", { name: "Débloquer ce profil" }).click();
    await page.getByRole("button", { name: "Confirmer le déblocage" }).click();
    await expect(page.getByText("Alice", { exact: true })).toBeVisible();
    expect(pages).toEqual(["1", "1"]);
    await expect(page.getByRole("button", { name: "Charger plus de profils" })).toHaveCount(0);
  });

  test("actualisation et reprise après une erreur de signalements", async ({ page }) => {
    let failed = true;
    await page.route("**/api/v1/safety/reports/**", route => json(route, failed ? { detail: "Indisponible" } : { count: 0, next: null, previous: null, results: [] }, failed ? 503 : 200));
    await page.goto("/reports");
    await expect(page.getByRole("heading", { name: "Impossible d’afficher tes dossiers" })).toBeVisible();
    failed = false;
    await page.getByRole("button", { name: "Actualiser la liste" }).click();
    await expect(page.getByRole("heading", { name: "Aucun signalement envoyé" })).toBeVisible();
    await expect(page.getByRole("button", { name: "Actualiser la liste" })).toBeEnabled();
  });
});
