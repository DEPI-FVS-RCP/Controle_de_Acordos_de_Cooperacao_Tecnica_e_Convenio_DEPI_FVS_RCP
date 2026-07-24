import { readFileSync } from "node:fs";
const s = readFileSync(new URL("../index.html", import.meta.url), "utf8");
const re = /getFirst\(\s*([A-Za-z_$][\w$]*)\s*,\s*(\[[^\]]*\])\s*\)/g;
let m;
const arr = [];
while ((m = re.exec(s)) !== null) {
  arr.push({ v: m[1], a: m[2].replace(/\s+/g, " ").trim() });
}
console.log("TOTAL getFirst com array literal:", arr.length);
const reAny = /getFirst\(/g;
let c = 0;
while (reAny.exec(s) !== null) c++;
console.log("TOTAL ocorrencias getFirst( :", c);
const map = new Map();
for (const o of arr) map.set(o.a, (map.get(o.a) || 0) + 1);
const uniq = [...map.entries()].sort((x, y) => y[1] - x[1]);
console.log("ARRAYS DISTINTOS:", uniq.length);
console.log("----");
uniq.forEach(([a, n], i) =>
  console.log(String(i + 1).padStart(2) + "  x" + String(n).padStart(2) + "  " + a)
);
