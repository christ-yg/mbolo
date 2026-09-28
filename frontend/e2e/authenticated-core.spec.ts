import { expect, test, type Page, type Route } from "@playwright/test";

const USER = {
  id: "11111111-1111-4111-8111-111111111111",
  email: "e2e-ui@mbolo.invalid",
  isEmailVerified: true,
  emailTwoFactorEnabled: false,
};

const PROFILE = {
  id: "22222222-2222-4222-8222-222222222222",
  display_name: "Arielle Test",
  age: 29,
  gender: "woman",
  gender_label: "Femme",
  city: "libreville",
  city_label: "Libreville",
  biography: "Profil fictif utilisé uniquement par les tests navigateur.",
  dating_intent: "serious_relationship",
  dating_intent_label: "Relation sérieuse",
  is_verified: true,
  photos: [],
  interests: ["music"],
  interest_labels: ["Musique"],
  common_interests: ["music"],
  common_interest_labels: ["Musique"],
  compatibility_score: 91,
  distance_label: "5 km environ",
};

const CONVERSATION = {
  id: "33333333-3333-4333-8333-333333333333",
  match_id: "44444444-4444-4444-8444-444444444444",
  other_profile: PROFILE,
  last_message: {
    id: "55555555-5555-4555-8555-555555555555",
    body: "Bonsoir depuis le test Mbolo",
    created_at: "2026-08-08T18:00:00Z",
    read_at: null,
    is_read: false,
    read_receipts_available: false,
    is_mine: false,
  },
  unread_count: 1,
  other_presence: {
    is_online: true,
    last_seen_at: "2026-08-08T18:00:00Z",
  },
  created_at: "2026-08-08T17:00:00Z",
  updated_at: "2026-08-08T18:00:00Z",
};

const PHOTO = {
  id: "66666666-6666-4666-8666-666666666666",
  image_url: null,
  position: 1,
  is_primary: true,
  moderation_status: "approved",
  moderation_status_label: "Approuvée",
  created_at: "2026-08-08T16:00:00Z",
  updated_at: "2026-08-08T16:30:00Z",
};

const FIRST_SENT_MESSAGE = {
  id: "88888888-8888-4888-8888-888888888888",
  body: "Bonsoir Arielle, ravi de faire ta connaissance !",
  created_at: "2026-09-28T14:10:00Z",
  read_at: null,
  is_read: false,
  read_receipts_available: false,
  is_mine: true,
};

async function json(route: Route, body: unknown, status = 200): Promise<void> {
  await route.fulfill({
    status,
    contentType: "application/json",
    body: JSON.stringify(body),
  });
}

async function installAuthenticatedApi(page: Page): Promise<void> {
  await page.route("**/api/**", async (route) => {
    const request = route.request();
    const path = new URL(request.url()).pathname;
    const method = request.method();

    if (path.includes("/api/v1/v1/")) {
      await json(route, { detail: "Préfixe API dupliqué détecté" }, 500);
      return;
    }

    if (path.endsWith("/auth/me/") && method === "GET") {
      await json(route, USER);
      return;
    }

    if (path.endsWith("/auth/activity/") && method === "POST") {
      await json(route, { ok: true });
      return;
    }

    if (path.endsWith("/csrf/") && method === "GET") {
      await json(route, { csrfToken: "e2e-ui-csrf-token" });
      return;
    }

    if (path.endsWith("/profiles/discovery/") && method === "GET") {
      await json(route, {
        count: 1,
        next: null,
        previous: null,
        results: [PROFILE],
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

    if (path.endsWith("/interactions/") && method === "POST") {
      await json(route, {
        interaction_id: "77777777-7777-4777-8777-777777777777",
        decision: "like",
        is_super_like: false,
        interaction_created: true,
        matched: true,
        match_created: true,
        match_id: CONVERSATION.match_id,
      }, 201);
      return;
    }

    if (path.endsWith("/conversations/") && method === "POST") {
      await json(route, CONVERSATION, 201);
      return;
    }

    if (path.endsWith("/conversations/") && method === "GET") {
      await json(route, {
        count: 1,
        next: null,
        previous: null,
        results: [CONVERSATION],
      });
      return;
    }

    if (
      path.endsWith(`/conversations/${CONVERSATION.id}/messages/`)
      && method === "POST"
    ) {
      const payload = request.postDataJSON() as { body?: string };

      if (payload.body !== FIRST_SENT_MESSAGE.body) {
        await json(route, { detail: "Corps du premier message invalide" }, 400);
        return;
      }

      await json(route, FIRST_SENT_MESSAGE, 201);
      return;
    }

    if (
      path.endsWith(`/conversations/${CONVERSATION.id}/messages/`)
      && method === "GET"
    ) {
      await json(route, {
        count: 0,
        next: null,
        previous: null,
        results: [],
      });
      return;
    }

    if (
      path.endsWith(`/conversations/${CONVERSATION.id}/typing/`)
      && method === "GET"
    ) {
      await json(route, {
        conversation_id: CONVERSATION.id,
        other_is_typing: false,
      });
      return;
    }

    if (
      path.endsWith(`/conversations/${CONVERSATION.id}/typing/`)
      && method === "POST"
    ) {
      await json(route, {
        conversation_id: CONVERSATION.id,
        is_typing: Boolean(request.postDataJSON()?.is_typing),
        expires_in_seconds: 5,
      });
      return;
    }

    if (path.endsWith("/profiles/photos/") && method === "GET") {
      await json(route, {
        count: 1,
        results: [PHOTO],
      });
      return;
    }

    if (path.endsWith("/subscriptions/overview/") && method === "GET") {
      await json(route, {
        data: {
          subscription: {
            plan: "free",
            plan_name: "Mbolo Gratuit",
            status: "none",
            is_premium: false,
            starts_at: null,
            ends_at: null,
            auto_renew: false,
            entitlements: {
              unlimited_likes: false,
              see_likers: false,
              advanced_filters: false,
              rewind_pass: false,
              read_receipts: false,
              priority_profile: false,
              incognito_mode: false,
              priority_support: false,
              profile_boost: false,
              boosts_per_window: 0,
              super_like: false,
              super_likes_per_day: 0,
            },
          },
          plans: [
            {
              code: "free",
              name: "Mbolo Gratuit",
              description: "L’essentiel pour créer de vraies connexions.",
              features: ["Likes et matchs"],
              price_label: "Gratuit",
              amount_xaf: 0,
              payment_available: false,
            },
            {
              code: "plus",
              name: "Mbolo Plus",
              description: "Plus de contrôle sur tes rencontres.",
              features: ["Voir les personnes qui t’ont liké"],
              price_label: "Tarif en cours de validation",
              amount_xaf: 0,
              payment_available: false,
            },
            {
              code: "prestige",
              name: "Mbolo Prestige",
              description: "L’expérience Mbolo la plus complète.",
              features: ["Mode navigation discrète"],
              price_label: "Tarif en cours de validation",
              amount_xaf: 0,
              payment_available: false,
            },
          ],
          payment_methods: [
            {
              code: "airtel_money",
              name: "Airtel Money",
              description: "Paiement depuis un portefeuille Airtel Money Gabon.",
              available: false,
            },
            {
              code: "moov_money",
              name: "Moov Money",
              description: "Paiement depuis un portefeuille Moov Money Gabon.",
              available: false,
            },
            {
              code: "bank_card",
              name: "Carte bancaire",
              description: "Visa ou Mastercard via un prestataire sécurisé.",
              available: false,
            },
          ],
          currency: "XAF",
          payment_notice: "Les paiements réels ne sont pas encore configurés.",
          privacy: {
            incognito_enabled: false,
            incognito_available: false,
            effective_incognito: false,
          },
          boost: {
            entitled: false,
            active: false,
            active_until: null,
            duration_minutes: 30,
            allowance_per_7_days: 0,
            remaining: 0,
            next_available_at: null,
          },
        },
      });
      return;
    }

    if (path.endsWith("/subscriptions/payments/history/") && method === "GET") {
      await json(route, { data: { transactions: [] } });
      return;
    }

    await json(route, { detail: `Endpoint E2E non simulé: ${method} ${path}` }, 501);
  });
}

test.describe("Parcours privés essentiels Mbolo", () => {
  test.beforeEach(async ({ page }) => {
    await installAuthenticatedApi(page);
  });

  test("Découvrir mène du like réciproque à la conversation privée", async ({ page }) => {
    await page.goto("/discovery");

    await expect(page.getByRole("heading", { name: /Arielle Test/ })).toBeVisible();
    await expect(page.getByText("91%", { exact: true })).toBeVisible();

    await page.getByRole("button", { name: /J’aime/ }).click();

    await expect(
      page.getByRole("heading", { name: "C’est un match avec Arielle Test !" }),
    ).toBeVisible();
    await page.getByRole("button", { name: /Envoyer un message/ }).click();

    await expect(page).toHaveURL(`/messages/${CONVERSATION.id}`);
    await expect(
      page.getByRole("heading", { name: "Arielle Test", exact: true }),
    ).toBeVisible();
    await expect(
      page.getByRole("heading", { name: "Commence la conversation" }),
    ).toBeVisible();
    await expect(
      page.getByText("Cette conversation est privée.", { exact: false }),
    ).toBeVisible();

    await page
      .getByRole("textbox", { name: "Écrire à Arielle Test" })
      .fill(FIRST_SENT_MESSAGE.body);
    await page.getByRole("button", { name: "Envoyer le message" }).click();

    await expect(
      page.getByText(FIRST_SENT_MESSAGE.body, { exact: true }),
    ).toBeVisible();
    await expect(
      page.getByRole("textbox", { name: "Écrire à Arielle Test" }),
    ).toHaveValue("");
  });

  test("Messages affiche une conversation privée et son état non lu", async ({ page }) => {
    await page.goto("/messages");

    await expect(page.getByRole("heading", { name: "Mes messages" })).toBeVisible();
    await expect(page.getByText("Arielle Test", { exact: true }).first()).toBeVisible();
    await expect(page.getByText("Bonsoir depuis le test Mbolo", { exact: true }).first()).toBeVisible();
    await expect(page.getByLabel("1 message non lu")).toBeVisible();
  });

  test("Photos affiche la galerie privée et le statut de modération", async ({ page }) => {
    await page.goto("/profile/photos");

    await expect(
      page.getByRole("heading", { name: "Construis une galerie qui te ressemble." }),
    ).toBeVisible();
    await expect(page.getByText("1/6", { exact: true })).toBeVisible();
    await expect(page.getByText("Approuvée", { exact: true })).toBeVisible();
  });

  test("Premium n'ouvre pas un paiement non configuré", async ({ page }) => {
    await page.goto("/premium");

    await expect(
      page.getByRole("heading", { name: "Une offre pour chaque étape" }),
    ).toBeVisible();
    await expect(page.getByText("Mbolo Plus", { exact: true })).toBeVisible();
    await expect(
      page.getByRole("button", { name: "Bientôt disponible" }).first(),
    ).toBeDisabled();
    await expect(page.getByRole("dialog")).toHaveCount(0);
  });
});
