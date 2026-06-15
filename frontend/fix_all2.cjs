const fs = require("fs");
let c = fs.readFileSync("src/App.test.tsx", "utf8");

c = c.replace(/name: "Continue"/g, "name: /Continue/i");

c = c.replace(
  /expect\(\n\s*screen\.queryByText\("Loading the character archive\.\.\."\),\n\s*\)\.not\.toBeInTheDocument\(\),/g,
  'expect(screen.getByText("Loading the character archive...")).toBeInTheDocument(),',
);

fs.writeFileSync("src/App.test.tsx", c);
console.log("Done");
