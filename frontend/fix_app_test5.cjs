const fs = require("fs");
let c = fs.readFileSync("src/App.test.tsx", "utf8");

c = c.replace(
  /getByRole\("heading", \{ name: "Slime on the Verge" \}\)/g,
  "getByText(/Slime on the Verge/i)",
);
c = c.replace(
  /findByRole\("heading", \{ name: "Slime on the Verge" \}\)/g,
  "findByText(/Slime on the Verge/i)",
);

fs.writeFileSync("src/App.test.tsx", c);
console.log("Done");
