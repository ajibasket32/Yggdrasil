const fs = require("fs");
let c = fs.readFileSync("src/App.test.tsx", "utf8");

// 1. Rename Navigation and Tabs
c = c.replace(/name: "Combat & Encounters"/g, 'name: "Encounters"');
c = c.replace(/name: "Quests & NPCs"/g, 'name: "Quests"');
c = c.replace(/name: "Status & Inv"/g, 'name: "Status"');
c = c.replace(/name: "Inventory & Equipment"/g, 'name: "Status"');

// 2. Quit -> Conclude -> Finalize (Ending the Chronicle)
// Ends the chronicle
c = c.replace(
  /const endButton = screen\.getByRole\("button", \{\n\s*name: "End Chronicle",\n\s*\}\);\n\s*fireEvent\.click\(endButton\);/g,
  'const concludeButton = await screen.findByRole("button", { name: "Conclude" });\n    fireEvent.click(concludeButton);\n    const endButton = await screen.findByRole("button", { name: "Finalize & Delete Save" });\n    fireEvent.click(endButton);',
);
// Cancels ending the chronicle
c = c.replace(
  /fireEvent\.click\(\n\s*await screen\.findByRole\("button", \{ name: "End Chronicle" \},\n\s*\),\n\s*\);/g,
  'fireEvent.click(await screen.findByRole("button", { name: "Conclude" }));',
);
// Any others
c = c.replace(/name: "End Chronicle"/g, 'name: "Conclude"');

// 3. Combat Escape and Continue
c = c.replace(/name: "Escape"/g, 'name: "Flee"');
c = c.replace(/name: "Return to archive"/g, 'name: "Continue"');
c = c.replace(/The party escaped the encounter\./g, "Escaped!");

// 4. Save
c = c.replace(/name: "Save Chronicle"/g, 'name: "Save"');
c = c.replace(/name: "Save Game"/g, 'name: "Save"');

// 5. Slime on the Verge heading
c = c.replace(
  /await screen\.findByRole\("heading",\s*\{\s*name: "Slime on the Verge"(?:,\s*level: 2)?\s*\}\s*\)/g,
  "await screen.findByText(/Slime on the Verge/i)",
);
c = c.replace(
  /screen\.getByRole\("heading",\s*\{\s*name: "Slime on the Verge"(?:,\s*level: 2)?\s*\}\s*\)/g,
  "screen.getByText(/Slime on the Verge/i)",
);

// 6. Gained XP text length issue
c = c.replace(
  /expect\(screen\.getAllByText\(\/Gained 45 XP and 18 gold\/\)\)\.toHaveLength\(2\);/g,
  "expect(screen.getByText(/Gained 45 XP and 18 gold/)).toBeInTheDocument();\n    expect(screen.getByText(/Victory! \\+45 XP/)).toBeInTheDocument();",
);
c = c.replace(
  /expect\(screen\.getAllByText\(\/The party was defeated\.\/\)\)\.toHaveLength\(2\);/g,
  "expect(screen.getByText(/The party was defeated\\./)).toBeInTheDocument();\n    expect(screen.getByText(/Defeated!/)).toBeInTheDocument();",
);
c = c.replace(/Gained 10 XP and 4 gold\./g, "Victory! +10 XP, +4 Gold.");
c = c.replace(
  /The party was defeated\. The character returns with 1 HP\./g,
  "Defeated!",
);

// 7. Quest Actions
// Revert only "Accept The Rootbound Watch", Offer help stays "Offer help"
c = c.replace(/name: "Accept The Rootbound Watch"/g, 'name: "Accept quest"');

// 8. One extra fix for descriptions
c = c.replace(
  /expect\(screen\.getByRole\("heading", \{ name: "Aster Vale" \}\)\)\.toBeInTheDocument\(\);/g,
  'expect(screen.getByText("Aster Vale")).toBeInTheDocument();',
);
// In App.test.tsx the title "Aster Vale" used to be a heading. Now it is a <strong> inside the HUD. So findByRole("heading", { name: "Aster Vale" }) will FAIL.
c = c.replace(
  /await screen\.findByRole\("heading", \{ name: "Aster Vale" \}\)/g,
  'await screen.findByText("Aster Vale")',
);
c = c.replace(
  /screen\.getByRole\("heading", \{ name: "Aster Vale" \}\)/g,
  'screen.getByText("Aster Vale")',
);

fs.writeFileSync("src/App.test.tsx", c);
console.log("Done");
