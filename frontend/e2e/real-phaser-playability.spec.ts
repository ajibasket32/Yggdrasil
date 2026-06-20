import { expect, test, type Page } from "@playwright/test";

const auditWorld = async (page: Page) =>
  page.evaluate(() => window.__YGGDRASIL_AUDIT__?.world);

const auditBgm = async (page: Page) =>
  page.evaluate(() => {
    const audit = window.__YGGDRASIL_AUDIT__ as
      | {
          bgm?: {
            currentKey: string | null;
            status: string;
          };
        }
      | undefined;
    return audit?.bgm;
  });

const hold = async (page: Page, key: string, ms: number) => {
  await page.keyboard.down(key);
  await page.waitForTimeout(ms);
  await page.keyboard.up(key);
};

const moveTo = async (page: Page, targetX: number, targetY: number) => {
  for (let step = 0; step < 30; step += 1) {
    const state = await auditWorld(page);
    expect(state).toBeDefined();
    const xDelta = targetX - state!.playerX;
    const yDelta = targetY - state!.playerY;
    if (Math.abs(xDelta) <= 24 && Math.abs(yDelta) <= 24) return;
    if (Math.abs(xDelta) > 24) {
      await hold(page, xDelta > 0 ? "KeyD" : "KeyA", 120);
    }
    if (Math.abs(yDelta) > 24) {
      await hold(page, yDelta > 0 ? "KeyS" : "KeyW", 120);
    }
  }
  throw new Error(`Could not reach marker near ${targetX}, ${targetY}`);
};

const travelTo = async (page: Page, locationName: string) => {
  await page.getByRole("button", { name: "Travel" }).click();
  await page
    .locator("article")
    .filter({ hasText: locationName })
    .getByRole("button", { name: "Travel here" })
    .click();
  await expect(page.getByText(locationName).first()).toBeVisible();
};

const screenshotDir = "../docs/release/v1.3-map-audio-overhaul/screenshots";

const capture = async (page: Page, name: string) => {
  await page.screenshot({ path: `${screenshotDir}/${name}.png` });
};

const attackUntilVictory = async (page: Page) => {
  const attack = page.getByRole("button", { name: "Attack" });
  for (let round = 0; round < 12; round += 1) {
    const combat = await page.evaluate(
      () => window.__YGGDRASIL_AUDIT__?.combat,
    );
    if (
      typeof combat === "object" &&
      combat !== null &&
      "status" in combat &&
      combat.status === "VICTORY"
    ) {
      return;
    }
    for (let wait = 0; wait < 30; wait += 1) {
      const hasContinue = await page.evaluate(() =>
        [...document.querySelectorAll("button")].some((button) =>
          button.textContent?.includes("Continue"),
        ),
      );
      if (hasContinue) return;
      if (await attack.isEnabled().catch(() => false)) {
        await attack.click();
        break;
      }
      await page.waitForTimeout(500);
    }
  }
};

test("real Phaser keyboard movement and playability path", async ({ page }) => {
  test.setTimeout(120000);
  const consoleErrors: string[] = [];
  const pageErrors: string[] = [];
  page.on("console", (message) => {
    if (message.type() === "error") consoleErrors.push(message.text());
  });
  page.on("pageerror", (error) => pageErrors.push(error.message));

  await page.goto("http://localhost:8080/?audit=1");
  await page.evaluate(() => window.localStorage.clear());
  await page.reload();
  await capture(page, "01-title");
  await page.getByRole("button", { name: "New Game" }).click();
  await page.getByLabel("Character name").fill("Phaser Audit");
  await page.getByLabel("Starting job").selectOption({ label: "Warrior" });
  await page.getByRole("button", { name: "Create character" }).click();
  await page.waitForFunction(() => window.__YGGDRASIL_AUDIT__?.world);
  await page.getByRole("button", { name: "Audio On" }).first().click();
  await page.getByRole("button", { name: "Audio Off" }).first().click();
  await expect
    .poll(async () => (await auditBgm(page))?.currentKey)
    .toBe("valeris_outskirts");
  await expect.poll(async () => (await auditBgm(page))?.status).toBe("playing");
  await capture(page, "02-valeris-outskirts-start");

  await page.mouse.click(640, 360);
  const before = await auditWorld(page);
  await page.keyboard.down("ArrowRight");
  await page.waitForTimeout(400);
  const moving = await auditWorld(page);
  await page.keyboard.up("ArrowRight");
  const afterArrow = await auditWorld(page);

  expect(moving?.moving).toBe(true);
  expect(moving?.animation).toBe("player-walk");
  expect(afterArrow!.playerX).toBeGreaterThan(before!.playerX);

  await hold(page, "KeyD", 400);
  const afterWasd = await auditWorld(page);
  expect(afterWasd!.playerX).toBeGreaterThan(afterArrow!.playerX);

  await travelTo(page, "Valeris City");
  await expect
    .poll(async () => (await auditWorld(page))?.mapId)
    .toBe("valeris_city");
  await expect
    .poll(async () => (await auditWorld(page))?.musicKey)
    .toBe("valeris_city");
  await expect
    .poll(async () => (await auditBgm(page))?.currentKey)
    .toBe("valeris_city");
  await capture(page, "03-valeris-city");
  await moveTo(page, 610, 455);
  await page.keyboard.press("KeyE");
  await expect(
    page.getByRole("heading", { name: "People nearby" }),
  ).toBeVisible();
  await page.getByRole("button", { name: "Browse Shop" }).first().click();
  await expect(
    page.getByRole("heading", { name: /Sundries|Shop|Blacksmith|Market/i }),
  ).toBeVisible();
  await capture(page, "04-shop-zone");
  await page.getByRole("button", { name: "Close" }).click();
  const continueButton = page.getByRole("button", { name: /Continue/ });
  if (await continueButton.isVisible().catch(() => false)) {
    await continueButton.click();
  }

  await travelTo(page, "Valeris Outskirts");
  await expect
    .poll(async () => (await auditWorld(page))?.mapId)
    .toBe("valeris_outskirts");
  await expect
    .poll(async () => (await auditWorld(page))?.musicKey)
    .toBe("valeris_outskirts");
  await expect
    .poll(async () => (await auditBgm(page))?.currentKey)
    .toBe("valeris_outskirts");
  await capture(page, "05-valeris-outskirts");
  await travelTo(page, "Greenwood Verge");
  await expect
    .poll(async () => (await auditWorld(page))?.mapId)
    .toBe("greenwood_verge");
  await capture(page, "06-greenwood-verge-inn");
  await moveTo(page, 375, 650);
  await page.keyboard.press("KeyE");
  await expect(
    page.getByRole("heading", { name: "People nearby" }),
  ).toBeVisible();
  await capture(page, "07-inn-zone");
  await page.locator("button.menu-close-btn").click();
  if (await continueButton.isVisible().catch(() => false)) {
    await continueButton.click();
  }
  await travelTo(page, "Sylvan Branch");
  await expect
    .poll(async () => (await auditWorld(page))?.mapId)
    .toBe("sylvan_branch");
  await expect
    .poll(async () => (await auditWorld(page))?.musicKey)
    .toBe("sylvan_branch");
  await expect
    .poll(async () => (await auditBgm(page))?.currentKey)
    .toBe("sylvan_branch");
  await capture(page, "08-sylvan-branch");
  await page.getByRole("button", { name: "Encounters" }).click();
  await page.getByRole("button", { name: "Begin combat" }).first().click();
  await page.waitForFunction(() => window.__YGGDRASIL_AUDIT__?.combat);
  await expect(page.getByLabel("Combat encounter")).toBeVisible();
  await expect
    .poll(async () => (await auditBgm(page))?.currentKey)
    .toBe("battle_theme");
  await capture(page, "09-battle");
  await attackUntilVictory(page);
  await expect(page.getByText(/Victory!/)).toBeVisible();
  await page.getByRole("button", { name: "Continue" }).click();
  await expect(page.getByRole("button", { name: "Travel" })).toBeVisible();
  await expect
    .poll(async () => (await auditWorld(page))?.musicKey)
    .toBe("sylvan_branch");
  await expect
    .poll(async () => (await auditBgm(page))?.currentKey)
    .toBe("sylvan_branch");

  await page.getByRole("button", { name: "Save Chronicle" }).click();
  await expect(
    page.getByRole("button").filter({ hasText: "Saved" }),
  ).toBeVisible();
  await page.reload();
  await page.getByRole("button", { name: "Continue: Phaser Audit" }).click();
  await expect(page.getByRole("button", { name: "Travel" })).toBeVisible();

  expect(pageErrors).toEqual([]);
  expect(consoleErrors).toEqual([]);
});
