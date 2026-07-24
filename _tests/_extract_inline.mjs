import { readFileSync, writeFileSync } from "node:fs";
const s = readFileSync(new URL("../index.html", import.meta.url), "utf8");
const re = /<script>([\s\S]*?)<\/script>/g;
let m, last = null;
while ((m = re.exec(s)) !== null) last = m[1];
writeFileSync("/tmp/farol_inline.js", last ?? "");
console.log("inline extraído:", (last ?? "").length, "chars");
