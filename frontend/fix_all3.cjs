const fs = require('fs');
let c = fs.readFileSync('src/App.test.tsx', 'utf8');

const target = `    expect(
      await screen.findByRole("heading", {
        name: "Slime on the Verge",
        level: 2,
      }),
    ).toBeInTheDocument();`;

const replacement = `    expect(
      await screen.findByText(/Slime on the Verge/i)
    ).toBeInTheDocument();`;

c = c.replaceAll(target, replacement);

fs.writeFileSync('src/App.test.tsx', c);
console.log("Done");
