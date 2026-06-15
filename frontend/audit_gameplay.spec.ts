import { test, expect } from '@playwright/test';

test('JRPG Gameplay Loop Audit', async ({ page }) => {
  test.setTimeout(60000);

  // Navigate to the game
  await page.goto('http://localhost:8080');

  // Title Screen
  await expect(page.getByText('Loading the character archive...')).not.toBeVisible({ timeout: 10000 });
  await page.screenshot({ path: 'artifacts/01-title-screen.png' });

  await page.waitForTimeout(2000); // Give React time to render after loading

  // Check if character exists
  const asterButton = page.getByRole('button', { name: /Aster Vale/i });
  try {
    await asterButton.waitFor({ state: 'visible', timeout: 5000 });
    await asterButton.click();
  } catch (e) {
    // Create new character
    // Assuming there's an input name, maybe wait for it
    await page.waitForSelector('input[name="name"]', { state: 'visible' });
    await page.fill('input[name="name"]', 'Aster Vale');
    // The dropdowns might not use standard name attributes if they were restyled?
    // Wait, let me just try to click "Create Character" if the dropdowns have defaults
    await page.selectOption('select', { label: 'Human' }).catch(() => {});
    await page.click('button:has-text("Create character")');
  }

  // Wait a bit to see what happens
  await page.waitForTimeout(3000);
  await page.screenshot({ path: 'artifacts/01.5-after-create.png' });

  // World Exploration / Main UI
  await expect(page.getByRole('button', { name: 'Travel' })).toBeVisible({ timeout: 10000 });
  await page.screenshot({ path: 'artifacts/02-world-ui.png' });

  // Status / Inventory Menu
  await page.click('button:has-text("Status")');
  await expect(page.getByText('Inventory')).toBeVisible();
  await page.screenshot({ path: 'artifacts/03-status-menu.png' });
  await page.click('button:has-text("×")');

  // Quest / Journal
  await page.click('button:has-text("Quests")');
  await expect(page.getByRole('heading', { name: 'Quest journal' })).toBeVisible();
  await page.screenshot({ path: 'artifacts/04-quest-journal.png' });
  await page.click('button:has-text("×")');

  // NPC Interaction
  await page.click('button:has-text("Travel")');
  await page.screenshot({ path: 'artifacts/05-travel-menu.png' });
  await page.click('button:has-text("×")');

  await page.click('button:has-text("Encounters")');
  await page.screenshot({ path: 'artifacts/06-encounters-menu.png' });
  
  // Start combat
  const slimeButton = page.getByRole('button', { name: /Slime on the Verge/i });
  if (await slimeButton.isVisible()) {
      await slimeButton.click();
      
      // Combat UI
      await expect(page.getByRole('button', { name: 'Attack' })).toBeVisible({ timeout: 5000 });
      await page.screenshot({ path: 'artifacts/07-combat-ui.png' });

      // Take action
      await page.click('button:has-text("Attack")');
      await page.waitForTimeout(1000); // Wait for animation
      await page.screenshot({ path: 'artifacts/08-combat-action.png' });
      
      // We can't guarantee victory without looping, but we have evidence of combat.
  } else {
      await page.click('button:has-text("×")');
  }
  
  // Save/Load
  await page.click('button:has-text("Save")');
  // Wait for save notification
  await page.waitForTimeout(1000);
  await page.screenshot({ path: 'artifacts/09-save-game.png' });

  // End Chronicle
  await page.getByRole('button', { name: 'Conclude' }).click({ force: true });

  await page.screenshot({ path: 'artifacts/10-end-chronicle.png' });
});
