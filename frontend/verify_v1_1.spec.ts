import { test, expect } from "@playwright/test";

test("verify v1.1 JRPG features", async ({ page }) => {
  // Go to the app
  await page.goto("http://localhost:8080");

  // 1. Verify Title Screen
  await expect(page.locator(".title-logo")).toContainText(
    "Yggdrasil Chronicles",
  );
  await page.screenshot({ path: "v1_1_title_screen.png" });

  // 2. Start New Game
  await page.click('button:has-text("New Game")');
  await page.fill('input[name="name"]', "Hero");
  await page.screenshot({ path: "v1_1_character_creation.png" });
  await page.click('button:has-text("Create character")');

  // 3. Verify HUD and World
  await page.waitForSelector(".hud-overlay", { timeout: 15000 });
  await page.screenshot({ path: "v1_1_hud_world.png" });

  // 4. Open Quest Journal
  await page.click('button:has-text("Quests")');
  await page.waitForSelector(".world-panel-container");
  await page.screenshot({ path: "v1_1_quest_journal.png" });
  await page.click("button.menu-close-btn");

  // 5. Verify Save Message
  await page.click('button:has-text("Save Chronicle")');
  await expect(page.locator('button:has-text("✓ Saved")')).toBeVisible();
  await page.screenshot({ path: "v1_1_save_feedback.png" });
});
