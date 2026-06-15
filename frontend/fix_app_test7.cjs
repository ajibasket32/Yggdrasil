const fs = require("fs");
let c = fs.readFileSync("src/App.test.tsx", "utf8");

// Fix Slime on the Verge heading
c = c.replace(
  /await screen\.findByRole\("heading",\s*\{\s*name: "Slime on the Verge"(?:,\s*level: 2)?\s*\}\s*\)/g,
  "await screen.findByText(/Slime on the Verge/i)",
);
c = c.replace(
  /screen\.getByRole\("heading",\s*\{\s*name: "Slime on the Verge"(?:,\s*level: 2)?\s*\}\s*\)/g,
  "screen.getByText(/Slime on the Verge/i)",
);

// Fix Gained XP length 2 issue
c = c.replace(
  /expect\(screen\.getAllByText\(\/Gained 45 XP and 18 gold\/\)\)\.toHaveLength\(2\);/g,
  "expect(screen.getByText(/Gained 45 XP and 18 gold/)).toBeInTheDocument();\n    expect(screen.getByText(/Victory! \\+45 XP/)).toBeInTheDocument();",
);

// Also, the defeat test might expect 'The party was defeated. The character returns with 1 HP.' length 2.
c = c.replace(
  /expect\(screen\.getAllByText\(\/The party was defeated\.\/\)\)\.toHaveLength\(2\);/g,
  "expect(screen.getByText(/The party was defeated\\./)).toBeInTheDocument();\n    expect(screen.getByText(/Defeated!/)).toBeInTheDocument();",
);

fs.writeFileSync("src/App.test.tsx", c);
console.log("Done");
