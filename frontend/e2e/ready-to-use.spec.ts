import { expect, test } from "@playwright/test";

test("ready-to-use gameplay smoke path", async ({ page }) => {
  test.setTimeout(90000);

  await page.goto("http://localhost:8080");
  await expect(page.locator(".title-logo")).toContainText(
    "Yggdrasil Chronicles",
    { timeout: 15000 },
  );
  await page.screenshot({ path: "artifacts/ready-01-title-screen.png" });

  await page.getByRole("button", { name: "New Game" }).click();
  await page.getByLabel("Character name").fill("Ready Tester");
  await page.screenshot({ path: "artifacts/ready-02-character-creation.png" });
  await page.getByRole("button", { name: "Create character" }).click();

  await expect(page.getByRole("button", { name: "Travel" })).toBeVisible({
    timeout: 15000,
  });
  await page.screenshot({ path: "artifacts/ready-03-world.png" });

  await page.getByRole("button", { name: "Quests" }).click();
  await expect(page.getByRole("heading", { name: "Quest Journal" })).toBeVisible();
  await page.screenshot({ path: "artifacts/ready-04-quest-journal.png" });

  const browseShop = page.getByRole("button", { name: "Browse Shop" });
  if (await browseShop.isVisible()) {
    await browseShop.click();
    await expect(page.getByText("Your Gold:")).toBeVisible();
    await page.screenshot({ path: "artifacts/ready-05-shop.png" });
    const buyButton = page.getByRole("button", { name: "Buy" }).first();
    if (await buyButton.isVisible()) {
      await buyButton.click();
      await expect(page.getByRole("status")).toContainText("Purchased");
    }
    await page.getByRole("button", { name: "Close" }).click();
  }

  const restButton = page.getByRole("button", { name: /Rest \(50g\)/ });
  if (await restButton.isVisible()) {
    await restButton.click();
    await expect(page.getByRole("status")).toContainText("Rested at the Inn");
    await page.screenshot({ path: "artifacts/ready-06-inn-rest.png" });
  }

  const closeButton = page.locator("button.menu-close-btn");
  if (await closeButton.isVisible()) {
    await closeButton.click();
  }

  await page.getByRole("button", { name: "Encounters" }).click();
  await page.screenshot({ path: "artifacts/ready-07-encounters.png" });
  const combatButton = page.getByRole("button", { name: "Begin combat" }).first();
  if (await combatButton.isVisible()) {
    await combatButton.click();
    await expect(page.getByLabel("Combat encounter")).toBeVisible({
      timeout: 10000,
    });
    await page.screenshot({ path: "artifacts/ready-08-combat.png" });
  }

  await page.getByRole("button", { name: /Save Chronicle|Saved/ }).click();
  await expect(page.getByRole("button", { name: /Saved/ })).toBeVisible({
    timeout: 10000,
  });
  await page.screenshot({ path: "artifacts/ready-09-saved.png" });

  await page.reload();
  await expect(page.getByRole("button", { name: /Continue: Ready Tester/ })).toBeVisible({
    timeout: 15000,
  });
  await page.getByRole("button", { name: /Continue: Ready Tester/ }).click();
  await expect(page.getByRole("button", { name: "Travel" })).toBeVisible({
    timeout: 15000,
  });
  await page.screenshot({ path: "artifacts/ready-10-continue-loaded.png" });
});
