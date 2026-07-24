// NEUTRALIZADO — script one-shot já aplicado (SCHEMA/CAMPOS em index.html).
// Mantido como registro histórico. NÃO reexecutar: reinserção duplicaria o
// objeto CAMPOS e quebraria o painel. A trava abaixo aborta se CAMPOS já existe.
import { readFileSync } from "node:fs";
const src = readFileSync(new URL("../index.html", import.meta.url), "utf8");
if (src.includes("const CAMPOS = {")) {
  console.error("Abortado: CAMPOS já existe no index.html. Refactor já aplicado.");
  process.exit(1);
}
console.error("Script desativado. Consulte o histórico de versões se precisar reaplicar.");
process.exit(1);
