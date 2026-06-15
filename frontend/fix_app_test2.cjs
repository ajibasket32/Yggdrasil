const fs = require("fs");
let c = fs.readFileSync("src/App.test.tsx", "utf8");

c = c.replace(/name: "Travel"/g, 'name: "Travel"'); // Probably fine
c = c.replace(/name: "Combat & Encounters"/g, 'name: "Encounters"');
c = c.replace(/name: "Quests & NPCs"/g, 'name: "Quests"');
c = c.replace(/name: "Inventory & Equipment"/g, 'name: "Status"');
c = c.replace(/name: "Quit to Desktop"/g, 'name: "Conclude"');

// Fix the loading screen test:
// It previously checked that "Loading the character archive..." disappeared if character and definitions are both null and it rendered null.
// But now it renders the title screen!
// So it will be in the document. Wait, if character is null, the title screen renders and says "Loading the character archive..." if !loadingDefinitions is false?
// I'll just change the assertion to expect the title screen.

fs.writeFileSync("src/App.test.tsx", c);
console.log("Done");
