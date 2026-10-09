import { expect, test } from "@playwright/test";

test("la procédure publique de suppression de compte reste accessible", async ({
  page,
}) => {
  await page.goto("/account-deletion");

  await expect(
    page.getByRole("heading", {
      name: "Supprimer définitivement un compte MBOLO.",
    }),
  ).toBeVisible();
  await expect(
    page.getByRole("link", {
      name: "Se connecter pour supprimer mon compte",
    }),
  ).toHaveAttribute("href", "/login");
  await expect(page.getByText("Ce qui est supprimé")).toBeVisible();
});
