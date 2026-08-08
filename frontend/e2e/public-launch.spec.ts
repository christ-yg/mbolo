import { expect, test } from "@playwright/test";

const publicPages = [
  { path: "/", heading: /rencontr/i },
  { path: "/about", heading: /rencontre africaine moderne/i },
  { path: "/how-it-works", heading: /découverte à la conversation/i },
  { path: "/help", heading: /réponses essentielles/i },
  { path: "/contact", heading: /bon canal d.assistance/i },
  { path: "/accessibility", heading: /plus grand nombre/i },
  { path: "/safety", heading: /espace de protection/i },
  { path: "/legal/notice", heading: /mentions légales/i },
  { path: "/legal/privacy", heading: /confidentialité/i },
];

test.describe("Lancement public Mbolo", () => {
  for (const publicPage of publicPages) {
    test(`${publicPage.path} répond et affiche son contenu`, async ({ page }) => {
      const response = await page.goto(publicPage.path);
      expect(response?.status()).toBe(200);
      await expect(page.locator("main")).toBeVisible();
      await expect(page.getByRole("heading", { level: 1, name: publicPage.heading })).toBeVisible();
    });
  }

  test("la page d'accueil expose les métadonnées de lancement", async ({ page }) => {
    await page.goto("/");
    await expect(page).toHaveTitle(/Mbolo/i);
    await expect(page.locator('html[lang="fr"]')).toHaveCount(1);
    await expect(page.locator('meta[name="description"]')).toHaveAttribute("content", /Gabon/i);
    await expect(page.locator('meta[property="og:site_name"]')).toHaveAttribute("content", "Mbolo");
  });

  test("robots.txt et sitemap.xml publient les pages de confiance", async ({ request }) => {
    const robotsResponse = await request.get("/robots.txt");
    expect(robotsResponse.status()).toBe(200);
    expect(await robotsResponse.text()).toContain("Sitemap: https://mbolo.ga/sitemap.xml");

    const sitemapResponse = await request.get("/sitemap.xml");
    expect(sitemapResponse.status()).toBe(200);
    const sitemap = await sitemapResponse.text();
    for (const path of ["/about", "/contact", "/accessibility", "/legal/notice", "/legal/privacy"]) {
      expect(sitemap).toContain(`https://mbolo.ga${path}`);
    }
  });

  test("les pages essentielles restent utilisables sur mobile", async ({ page }) => {
    await page.setViewportSize({ width: 390, height: 844 });
    for (const path of ["/", "/about", "/how-it-works", "/help", "/contact", "/accessibility"]) {
      await page.goto(path);
      await expect(page.locator("main")).toBeVisible();
      await expect(page.getByRole("heading", { level: 1 })).toBeVisible();
    }
  });

  test("un visiteur anonyme est redirigé hors de la découverte", async ({ page }) => {
    await page.goto("/discovery");
    await expect(page).toHaveURL(/\/login(?:\?|$)/);
    await expect(page.getByRole("heading", { level: 1 })).toBeVisible();
  });
});
