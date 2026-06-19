import { expect, test, type Page } from "@playwright/test";

const closeMenuIfOpen = async (page: Page) => {
  const closeButton = page.locator("button.menu-close-btn");
  if (await closeButton.isVisible()) {
    await closeButton.click();
  }
};

const travelTo = async (page: Page, locationName: string) => {
  await closeMenuIfOpen(page);
  await page.getByRole("button", { name: "Travel" }).click();
  await page
    .locator("article")
    .filter({ hasText: locationName })
    .getByRole("button", { name: "Travel here" })
    .click();
  await expect(page.getByText(locationName).first()).toBeVisible({
    timeout: 15000,
  });
};

const attackUntilVictory = async (page: Page) => {
  const victoryText = page.getByText(/Victory!/);
  const attackButton = page.getByRole("button", { name: "Attack" });

  for (let round = 0; round < 12; round += 1) {
    if (await victoryText.isVisible()) {
      return;
    }

    const nextAction = await Promise.race([
      victoryText
        .waitFor({ state: "visible", timeout: 15000 })
        .then(() => "victory" as const),
      attackButton
        .waitFor({ state: "visible", timeout: 15000 })
        .then(async () => {
          await expect(attackButton).toBeEnabled({ timeout: 15000 });
          return "attack" as const;
        }),
    ]);

    if (nextAction === "victory") {
      return;
    }

    await attackButton.click();
  }
};

test("ready-to-use gameplay smoke path", async ({ page }) => {
  test.setTimeout(90000);

  await page.goto("http://localhost:8080");
  await page.evaluate(() => window.localStorage.clear());
  await page.reload();
  await expect(page.locator(".title-logo")).toContainText(
    "Yggdrasil Chronicles",
    { timeout: 15000 },
  );
  await page.screenshot({ path: "artifacts/ready-01-title-screen.png" });

  await page.getByRole("button", { name: "New Game" }).click();
  await page.getByLabel("Character name").fill("Ready Tester");
  await page.getByLabel("Starting job").selectOption({ label: "Warrior" });
  await page.screenshot({ path: "artifacts/ready-02-character-creation.png" });
  await page.getByRole("button", { name: "Create character" }).click();

  await expect(page.getByRole("button", { name: "Travel" })).toBeVisible({
    timeout: 15000,
  });
  await page.screenshot({ path: "artifacts/ready-03-world.png" });

  await page.getByRole("button", { name: "Quests" }).click();
  await expect(
    page.getByRole("heading", { name: "Quest Journal" }),
  ).toBeVisible();
  await page.screenshot({ path: "artifacts/ready-04-quest-journal.png" });

  await page.getByRole("button", { name: "Greet" }).first().click();
  await expect(page.getByRole("status")).toBeVisible();
  await page.screenshot({ path: "artifacts/ready-05-npc-greet.png" });
  await closeMenuIfOpen(page);

  await travelTo(page, "Valeris City");
  await page.getByRole("button", { name: "Quests" }).click();
  await page.getByRole("button", { name: "Browse Shop" }).click();
  await expect(page.getByText("Your Gold:")).toBeVisible();
  await page.screenshot({ path: "artifacts/ready-06-shop.png" });
  await page.getByRole("button", { name: "Buy" }).first().click();
  await expect(page.getByRole("status")).toContainText("Purchased");
  await page.getByRole("button", { name: "Close", exact: true }).click();

  await travelTo(page, "Valeris Outskirts");
  await travelTo(page, "Greenwood Verge");
  await page.getByRole("button", { name: "Quests" }).click();
  await page.getByRole("button", { name: /Rest \(50g\)/ }).click();
  await expect(page.getByText("Rested at the Inn")).toBeVisible();
  await page.screenshot({ path: "artifacts/ready-07-inn-rest.png" });

  await closeMenuIfOpen(page);

  await page.getByRole("button", { name: "Encounters" }).click();
  await page.screenshot({ path: "artifacts/ready-08-encounters.png" });
  await page.getByRole("button", { name: "Begin combat" }).first().click();
  await expect(page.getByLabel("Combat encounter")).toBeVisible({
    timeout: 10000,
  });
  await page.screenshot({ path: "artifacts/ready-09-combat.png" });
  await attackUntilVictory(page);
  await expect(page.getByText(/Victory!/)).toBeVisible({ timeout: 10000 });
  await page.getByRole("button", { name: "Continue" }).click();
  await expect(page.getByRole("button", { name: "Travel" })).toBeVisible({
    timeout: 15000,
  });

  await page.getByRole("button", { name: /Save Chronicle|Saved/ }).click();
  await expect(page.getByRole("button", { name: /Saved/ })).toBeVisible({
    timeout: 10000,
  });
  await page.screenshot({ path: "artifacts/ready-10-saved.png" });

  await page.reload();
  await expect(
    page.getByRole("button", { name: /Continue: Ready Tester/ }),
  ).toBeVisible({
    timeout: 15000,
  });
  await page.getByRole("button", { name: /Continue: Ready Tester/ }).click();
  await expect(page.getByRole("button", { name: "Travel" })).toBeVisible({
    timeout: 15000,
  });
  await page.screenshot({ path: "artifacts/ready-11-continue-loaded.png" });
});
