const fs = require("fs");
let c = fs.readFileSync("src/App.test.tsx", "utf8");

c = c.replace(/name: "Escape"/g, 'name: "Flee"');
c = c.replace(/name: "Return to archive"/g, 'name: "Continue"');
c = c.replace(/name: "Status & Inv"/g, 'name: "Status"');
c = c.replace(/name: "Save Chronicle"/g, 'name: "Save"');
c = c.replace(/The party escaped the encounter\./g, "Escaped!");
c = c.replace(/Gained 10 XP and 4 gold\./g, "Victory! +10 XP, +4 Gold.");
c = c.replace(
  /The party was defeated\. The character returns with 1 HP\./g,
  "Defeated!",
);
c = c.replace(/name: "Accept quest"/g, "name: /Accept/i");

fs.writeFileSync("src/App.test.tsx", c);
console.log("Done");
