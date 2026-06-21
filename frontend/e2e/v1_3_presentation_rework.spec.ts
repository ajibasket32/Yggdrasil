import { expect, test, type Page } from "@playwright/test";

declare const process: { env: Record<string, string | undefined> };

const baseUrl = process.env.E2E_BASE_URL ?? "http://localhost:8080";

const auditWorld = async (page: Page) =>
  page.evaluate(() => window.__YGGDRASIL_AUDIT__?.world);

const auditCombat = async (page: Page) =>
  page.evaluate(
    () => window.__YGGDRASIL_AUDIT__?.combat as { status?: string } | undefined,
  );

const auditAudio = async (page: Page) =>
  page.evaluate(() => window.__YGGDRASIL_AUDIT__?.audio);

const closeMenuIfOpen = async (page: Page) => {
  const closeButton = page.locator("button.menu-close-btn");
  if (await closeButton.isVisible().catch(() => false)) {
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
  await expect
    .poll(() => auditWorld(page))
    .toMatchObject({
      location: locationName,
    });
};

const attackUntilVictory = async (page: Page) => {
  const attack = page.getByRole("button", { name: "Attack" });
  for (let round = 0; round < 12; round += 1) {
    const combat = await auditCombat(page);
    if (combat?.status === "VICTORY") return;
    if (await attack.isVisible().catch(() => false)) await attack.click();
    await page.waitForTimeout(700);
  }
};

test("v1.3 presentation journey stays scoped and visible", async ({ page }) => {
  test.setTimeout(120000);
  const consoleErrors: string[] = [];
  const pageErrors: string[] = [];
  page.on("console", (message) => {
    if (message.type() === "error") consoleErrors.push(message.text());
  });
  page.on("pageerror", (error) => pageErrors.push(error.message));

  const playerId = crypto.randomUUID();
  await page.addInitScript((value) => {
    localStorage.setItem("yggdrasil-player-id", value);
  }, playerId);
  await page.goto(`${baseUrl}/?audit=1`);
  await page.getByRole("button", { name: "New Game" }).click();
  await page.getByLabel("Character name").fill("Audit Vale");
  await page.getByLabel("Starting job").selectOption({ label: "Warrior" });
  await page.getByRole("button", { name: "Create character" }).click();

  await expect
    .poll(() => auditWorld(page))
    .toMatchObject({
      location: "Valeris City",
      musicKey: "city",
    });
  await expect
    .poll(() => auditAudio(page))
    .toMatchObject({
      bgmKey: "city",
      muted: false,
      ready: true,
    });

  await page.getByRole("button", { name: "Quests" }).click();
  const hagar = page.locator("article.grid-card").filter({
    hasText: "Blacksmith Hagar",
  });
  await expect(hagar).toBeVisible();
  await expect(hagar.getByText(/Rest \(/)).toHaveCount(0);
  await expect(hagar.getByText("Browse Shop")).toHaveCount(0);
  await hagar.getByText("Speak").click();
  await expect
    .poll(() => auditWorld(page))
    .toMatchObject({
      location: "Blacksmith Interior",
      musicKey: "interior",
    });

  await closeMenuIfOpen(page);
  await travelTo(page, "Valeris Outskirts");
  await expect
    .poll(() => auditWorld(page))
    .toMatchObject({
      musicKey: "outskirts",
    });
  await travelTo(page, "Greenwood Verge");
  await expect
    .poll(() => auditWorld(page))
    .toMatchObject({
      musicKey: "forest",
    });

  await page.getByRole("button", { name: "Quests" }).click();
  const elena = page.locator("article.grid-card").filter({
    hasText: "Innkeeper Elena",
  });
  await expect(elena).toBeVisible();
  await expect(
    elena.getByRole("button", { name: /Rest \(50g\)/ }),
  ).toBeVisible();
  await expect(elena.getByText("Browse Shop")).toHaveCount(0);
  await elena.getByText("Speak").click();
  await expect
    .poll(() => auditWorld(page))
    .toMatchObject({
      location: "Inn Interior",
      musicKey: "interior",
    });

  await travelTo(page, "Sylvan Branch");
  await expect
    .poll(() => auditWorld(page))
    .toMatchObject({
      location: "Sylvan Branch",
      combatBackgroundKey: "forest",
    });

  await page.getByRole("button", { name: "Encounters" }).click();
  await page.getByRole("button", { name: "Begin combat" }).first().click();
  await expect
    .poll(() => auditCombat(page))
    .toMatchObject({ status: "ACTIVE" });
  await expect.poll(() => auditAudio(page)).toMatchObject({ bgmKey: "battle" });
  await attackUntilVictory(page);
  await expect(page.getByText(/Victory!/)).toBeVisible({ timeout: 15000 });
  await page.getByRole("button", { name: "Continue" }).click();
  await expect
    .poll(() => auditWorld(page))
    .toMatchObject({
      location: "Sylvan Branch",
    });

  await page.getByRole("button", { name: /Save Chronicle|Saved/ }).click();
  await expect(page.getByRole("button", { name: /Saved/ })).toBeVisible();
  await page.reload();
  await page.getByRole("button", { name: "Continue: Audit Vale" }).click();
  await expect
    .poll(() => auditWorld(page))
    .toMatchObject({
      location: "Sylvan Branch",
    });
  await expect(page.getByText(/Rest \(/)).toHaveCount(0);

  expect(pageErrors).toEqual([]);
  expect(consoleErrors).toEqual([]);
});
