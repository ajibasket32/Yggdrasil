const fs = require("fs");
let content = fs.readFileSync("src/App.tsx", "utf8");

// Use any to bypass the unsafe assignment errors in App.tsx
content = content.replace(
  "/* eslint-disable @typescript-eslint/no-explicit-any, @typescript-eslint/no-unsafe-member-access */\n",
  "/* eslint-disable @typescript-eslint/no-explicit-any */\n",
);

fs.writeFileSync("src/App.tsx", content);
