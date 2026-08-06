import { defineConfig, devices } from "@playwright/test";

/**
 * Configuration des tests End-to-End de Mbolo.
 *
 * Playwright teste la préproduction Docker locale exactement comme
 * un navigateur utilisateur : Nginx/React -> API Django -> PostgreSQL/Redis.
 */
export default defineConfig({
  testDir: "./e2e",

  /**
   * Les résultats techniques Playwright sont temporaires et ne doivent pas
   * polluer le dépôt Git. Sous Linux/WSL, /tmp est adapté à ces artefacts.
   */
  outputDir: "/tmp/mbolo-playwright-test-results",

  /**
   * Un seul worker évite que plusieurs authentifications simultanées
   * déclenchent artificiellement la protection anti-bruteforce de Mbolo.
   */
  workers: 1,

  timeout: 30_000,

  expect: {
    timeout: 10_000,
  },

  use: {
    /**
     * URL de la préproduction locale. Une variable d'environnement permet
     * de cibler plus tard un autre environnement sans modifier ce fichier.
     */
    baseURL:
      process.env.MBOLO_E2E_BASE_URL ??
      "http://127.0.0.1:8080",

    /**
     * Les artefacts visuels ne sont conservés qu'en cas d'échec afin de
     * limiter la conservation inutile de données visibles dans les profils.
     */
    screenshot: "only-on-failure",
    trace: "retain-on-failure",
    video: "off",
    ignoreHTTPSErrors: false,
  },

  reporter: [["list"]],

  /**
   * On commence par Chromium. Firefox et WebKit seront ajoutés pendant
   * la phase dédiée à la compatibilité multi-navigateurs.
   */
  projects: [
    {
      name: "chromium",
      use: {
        ...devices["Desktop Chrome"],
      },
    },
  ],
});
