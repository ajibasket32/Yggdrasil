const fs = require("fs");
let c = fs.readFileSync("src/App.test.tsx", "utf8");

c = c.replace(/name: "Save Game"/g, 'name: "Save"');
c = c.replace(/name: "Continue"/g, "name: /Continue/i");

fs.writeFileSync("src/App.test.tsx", c);
console.log("Done");
