// The package is "type": "module", so the CommonJS build must use .cjs/.d.cts
// extensions for Node and TypeScript to read it as CommonJS.
import { renameSync } from "node:fs";

renameSync("dist/cjs/index.js", "dist/cjs/index.cjs");
renameSync("dist/cjs/index.d.ts", "dist/cjs/index.d.cts");
