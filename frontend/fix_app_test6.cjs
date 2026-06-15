const fs = require("fs");
let c = fs.readFileSync("src/App.test.tsx", "utf8");

c = c.replace(/name: "Return to Main Menu"/g, 'name: "Finalize & Delete Save"');
// I need to fix any remaining issues. The 10 failures include "describes the current location and reports narrative failures".
// That one probably looks for "Examine Area" or something?
// Let's replace "Examine Area" with "Examine" or something. Wait, in App.tsx I didn't change "Examine Area".
// I'll just write this file for the Return to Main Menu fix.
fs.writeFileSync("src/App.test.tsx", c);
console.log("Done");
