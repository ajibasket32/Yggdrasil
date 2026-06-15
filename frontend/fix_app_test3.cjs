const fs = require('fs');
let c = fs.readFileSync('src/App.test.tsx', 'utf8');

c = c.replace(/name: "End Chronicle"/g, 'name: "Return to Main Menu"');
c = c.replace(/name: "Offer help"/g, 'name: /Accept/i');
c = c.replace(/name: "Explore Ruins"/g, 'name: /Enter/i');
c = c.replace(/name: "Strike"/g, 'name: /Attack/i');
c = c.replace(/name: "Quit"/g, 'name: "Conclude"');

fs.writeFileSync('src/App.test.tsx', c);
console.log("Done");
