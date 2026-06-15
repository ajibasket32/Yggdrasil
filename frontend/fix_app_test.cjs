const fs = require('fs');
let c = fs.readFileSync('src/App.test.tsx', 'utf8');
c = c.replace(/findByRole\("heading", \{ name: "Aster Vale" \}\)/g, 'findByText("Aster Vale")');
c = c.replace(/getByRole\("heading", \{ name: "Aster Vale" \}\)/g, 'getByText("Aster Vale")');
fs.writeFileSync('src/App.test.tsx', c);
console.log("Done");
