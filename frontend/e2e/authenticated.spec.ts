import {
  expect,
  test,
  type Page,
} from "@playwright/test";

/**
 * Les secrets E2E ne sont jamais inscrits dans le dépôt.
 * Ils sont transmis au processus Playwright via l'environnement local.
 */
interface E2ECredentials {
  email: string;
  password: string;
}

function getCredentials(): E2ECredentials {
  const email = process.env.MBOLO_E2E_EMAIL;
  const password = process.env.MBOLO_E2E_PASSWORD;

  if (!email || !password) {
    throw new Error(
      "Les variables MBOLO_E2E_EMAIL et MBOLO_E2E_PASSWORD " +
        "sont obligatoires pour les tests authentifiés.",
    );
  }

  return { email, password };
}

/**
 * Authentification par le vrai formulaire Mbolo.
 * Aucun appel interne ne contourne la session Django ou la protection CSRF.
 */
async function login(page: Page): Promise<void> {
  const credentials = getCredentials();

  await page.goto("/login");

  await page
    .locator('input[name="email"]')
    .fill(credentials.email);

  await page
    .locator('input[name="password"]')
    .fill(credentials.password);

  await page
    .locator('button[type="submit"]')
    .click();

  /**
   * Une connexion sans second facteur mène normalement à /discovery.
   * Si le compte exige la 2FA, le test échoue intentionnellement :
   * le scénario E2E ne doit jamais contourner ce contrôle de sécurité.
   */
  await expect(page).toHaveURL(
    /\/discovery(?:$|[?#])/,
  );
}

test.describe("Mbolo — session authentifiée", () => {
  test(
    "un membre connecté accède aux zones principales",
    async ({ page }) => {
      await login(page);

      await expect(page).toHaveURL(
        /\/discovery(?:$|[?#])/,
      );

      await page.goto("/matches");
      await expect(page).toHaveURL(
        /\/matches(?:$|[?#])/,
      );

      await page.goto("/messages");
      await expect(page).toHaveURL(
        /\/messages(?:$|[?#])/,
      );

      await page.goto("/account");
      await expect(page).toHaveURL(
        /\/account(?:$|[?#])/,
      );
    },
  );
});
