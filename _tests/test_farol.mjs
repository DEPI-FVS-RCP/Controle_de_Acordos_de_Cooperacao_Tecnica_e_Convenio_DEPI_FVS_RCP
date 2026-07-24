#!/usr/bin/env node
// =====================================================================
// FAROL DEPI/FVS-RCP — Suíte de testes das funções de vigência (Onda 2)
// =====================================================================
//
// O QUE É: rede de regressão para as regras de negócio críticas do painel
// (parseDateAny, isArquivado, computeStatus, isConcluido). Extrai as funções
// PURAS diretamente do index.html (sem duplicar código) e as executa num
// contexto isolado (node:vm) com a data "hoje" fixada em 2026-07-24, para que
// os resultados sejam determinísticos independentemente do dia em que rodar.
//
// POR QUE: garante que alterações futuras no index.html não quebrem, sem querer,
// a classificação de prazos, a separação Ativos/Concluídos ou o parse de datas.
//
// COMO RODAR (a partir da raiz do projeto):
//     node _tests/test_farol.mjs
//
// Sai com código 0 se tudo passar; 1 se qualquer teste falhar.
// Este arquivo NÃO é publicado no GitHub Pages (a pasta começa com "_").
// NÃO altera o index.html — apenas lê.
// =====================================================================

import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";
import vm from "node:vm";

const __dirname = dirname(fileURLToPath(import.meta.url));
const INDEX_PATH = join(__dirname, "..", "index.html");
const src = readFileSync(INDEX_PATH, "utf8");

// ---------------------------------------------------------------------
// Extração por balanceamento de chaves: acha "function NOME(" e recorta
// do "function" até a chave "}" que fecha o corpo. Robusto a mudanças de
// linha/indentação (não depende de números de linha fixos).
// ---------------------------------------------------------------------
function extractFunction(source, name) {
  const sig = `function ${name}(`;
  const start = source.indexOf(sig);
  if (start === -1) throw new Error(`Função não encontrada no index.html: ${name}`);
  const braceOpen = source.indexOf("{", start);
  if (braceOpen === -1) throw new Error(`Corpo não encontrado para: ${name}`);
  let depth = 0;
  for (let i = braceOpen; i < source.length; i++) {
    const c = source[i];
    if (c === "{") depth++;
    else if (c === "}") {
      depth--;
      if (depth === 0) return source.slice(start, i + 1);
    }
  }
  throw new Error(`Chaves não balanceadas em: ${name}`);
}

// Extrai uma constante "const NOME = <valor>;" (número simples).
function extractConst(source, name) {
  const re = new RegExp(`const\\s+${name}\\s*=\\s*([0-9]+)\\s*;`);
  const m = source.match(re);
  if (!m) throw new Error(`Constante não encontrada: ${name}`);
  return `const ${name} = ${m[1]};`;
}

// Extrai um objeto "const NOME = { ... };" por balanceamento de chaves.
function extractObject(source, name) {
  const sig = `const ${name} = {`;
  const start = source.indexOf(sig);
  if (start === -1) throw new Error(`Objeto não encontrado: ${name}`);
  const braceOpen = source.indexOf("{", start);
  let depth = 0;
  for (let i = braceOpen; i < source.length; i++) {
    const c = source[i];
    if (c === "{") depth++;
    else if (c === "}") {
      depth--;
      if (depth === 0) return source.slice(start, i + 1) + ";";
    }
  }
  throw new Error(`Chaves não balanceadas em objeto: ${name}`);
}

const FUNC_NAMES = [
  "escapeHTML", // dependência indireta de makeUl; incluída por segurança
  "getFirst",
  "norm",
  "parseDateAny",
  "isArquivado",
  "computeStatus",
  "isConcluido",
];

const pieces = [];
pieces.push(extractConst(src, "PRAZO_CRITICO_DIAS"));
pieces.push(extractConst(src, "PRAZO_ALERTA_DIAS"));
pieces.push(extractObject(src, "CAMPOS")); // SCHEMA central de aliases (Onda 2/B)
for (const fn of FUNC_NAMES) pieces.push(extractFunction(src, fn));

// Exporta as funções para fora do sandbox
pieces.push(`
globalThis.__exports = {
  PRAZO_CRITICO_DIAS, PRAZO_ALERTA_DIAS, CAMPOS,
  getFirst, norm, parseDateAny, isArquivado, computeStatus, isConcluido
};`);

const assembled = pieces.join("\n\n");

// ---------------------------------------------------------------------
// Data determinística: "hoje" = 2026-07-24 (meia-noite local).
// new Date()        -> data fixa
// new Date(y,m,d)   -> comportamento normal
// new Date(string)  -> comportamento normal
// ---------------------------------------------------------------------
const FIXED_TODAY = [2026, 6, 24, 0, 0, 0, 0]; // mês 6 = julho (0-based)
class MockDate extends Date {
  constructor(...args) {
    if (args.length === 0) super(...FIXED_TODAY);
    else super(...args);
  }
  static now() {
    return new Date(...FIXED_TODAY).getTime();
  }
}

const sandbox = { Date: MockDate, String, Number, Math, isNaN, RegExp, console };
vm.createContext(sandbox);
vm.runInContext(assembled, sandbox);
const F = sandbox.__exports;

// ---------------------------------------------------------------------
// Mini-framework de asserção
// ---------------------------------------------------------------------
let passed = 0;
let failed = 0;
const failures = [];

function eq(actual, expected, msg) {
  const a = JSON.stringify(actual);
  const e = JSON.stringify(expected);
  if (a === e) {
    passed++;
  } else {
    failed++;
    failures.push(`  ✗ ${msg}\n      esperado: ${e}\n      obtido:   ${a}`);
  }
}

// Helper: monta uma linha só com vigencia_termino
const rowVenc = (v) => ({ vigencia_termino: v });
// Helper: data futura/passada em dd/mm/aaaa relativa a 2026-07-24
const TODAY = new Date(2026, 6, 24);
function dateOffsetBR(days) {
  const d = new Date(2026, 6, 24 + days);
  const dd = String(d.getDate()).padStart(2, "0");
  const mm = String(d.getMonth() + 1).padStart(2, "0");
  return `${dd}/${mm}/${d.getFullYear()}`;
}

// ---------------------------------------------------------------------
// 1) parseDateAny
// ---------------------------------------------------------------------
(function testParseDateAny() {
  const p = F.parseDateAny;
  eq(p("15/03/2025") instanceof Date, true, "parseDateAny: dd/mm/aaaa retorna Date");
  eq(p("15/03/2025").getFullYear(), 2025, "parseDateAny: dd/mm/aaaa ano correto");
  eq(p("15/03/2025").getMonth(), 2, "parseDateAny: dd/mm/aaaa mês correto (0-based)");
  eq(p("15/03/2025").getDate(), 15, "parseDateAny: dd/mm/aaaa dia correto");
  eq(p("15-03-2025") instanceof Date, true, "parseDateAny: dd-mm-aaaa (hífen) aceito");
  eq(p("2025-03-15") instanceof Date, true, "parseDateAny: aaaa-mm-dd (ISO) aceito");
  eq(p("2025-03-15").getMonth(), 2, "parseDateAny: ISO mês correto");
  eq(p(""), null, "parseDateAny: string vazia -> null");
  eq(p(null), null, "parseDateAny: null -> null");
  eq(p(undefined), null, "parseDateAny: undefined -> null");
  eq(p("texto qualquer"), null, "parseDateAny: texto inválido -> null");
  // ACHADO DOCUMENTADO (não é bug corrigido aqui): parseDateAny NÃO valida
  // faixas de dia/mês — confia no rollover nativo do Date do JS. Assim,
  // "32/13/2025" vira new Date(2025,12,32) = 01/02/2026. Este teste FIXA esse
  // comportamento atual para detectar regressões; endurecer a validação exigiria
  // alterar a lógica de vigência no index.html (requer autorização — governança).
  const rolled = p("32/13/2025");
  eq(rolled instanceof Date, true, "parseDateAny: 32/13/2025 NÃO retorna null (rollover do Date — permissividade conhecida)");
  eq([rolled.getFullYear(), rolled.getMonth(), rolled.getDate()], [2026, 1, 1],
     "parseDateAny: 32/13/2025 normaliza para 01/02/2026 (rollover documentado)");
})();

// ---------------------------------------------------------------------
// 2) isArquivado
// ---------------------------------------------------------------------
(function testIsArquivado() {
  const a = F.isArquivado;
  eq(a({ arquivado: "SIM" }), true, "isArquivado: SIM -> true");
  eq(a({ arquivado: "sim" }), true, "isArquivado: 'sim' minúsculo -> true");
  eq(a({ arquivado: "S" }), true, "isArquivado: S -> true");
  eq(a({ arquivado: "1" }), true, "isArquivado: '1' -> true");
  eq(a({ arquivado: "TRUE" }), true, "isArquivado: TRUE -> true");
  eq(a({ arquivado: "ARQUIVADO" }), true, "isArquivado: contém ARQUIV -> true");
  eq(a({ arquivado: "NÃO" }), false, "isArquivado: NÃO -> false");
  eq(a({ arquivado: "" }), false, "isArquivado: vazio -> false");
  eq(a({}), false, "isArquivado: sem coluna -> false");
})();

// ---------------------------------------------------------------------
// 3) computeStatus
// ---------------------------------------------------------------------
(function testComputeStatus() {
  const c = F.computeStatus;
  // arquivado tem prioridade máxima
  eq(c({ arquivado: "SIM", vigencia_termino: dateOffsetBR(10) }), "ARQUIVADO",
     "computeStatus: arquivado vence tudo -> ARQUIVADO");
  // sem data
  eq(c(rowVenc("")), "SEM DATA", "computeStatus: sem data de término -> SEM DATA");
  eq(c({}), "SEM DATA", "computeStatus: linha sem coluna de término -> SEM DATA");
  // faixas por data (sem override textual)
  eq(c(rowVenc(dateOffsetBR(400))), "VIGENTE",
     "computeStatus: >180 dias -> VIGENTE");
  eq(c(rowVenc(dateOffsetBR(200))), "VIGENTE",
     "computeStatus: 200 dias -> VIGENTE");
  eq(c(rowVenc(dateOffsetBR(180))), "ALERTA 180 DIAS",
     "computeStatus: exatamente 180 dias -> ALERTA 180 DIAS");
  eq(c(rowVenc(dateOffsetBR(120))), "ALERTA 180 DIAS",
     "computeStatus: 120 dias -> ALERTA 180 DIAS");
  eq(c(rowVenc(dateOffsetBR(61))), "ALERTA 180 DIAS",
     "computeStatus: 61 dias -> ALERTA 180 DIAS (limite superior do crítico)");
  eq(c(rowVenc(dateOffsetBR(60))), "CRÍTICO 60 DIAS",
     "computeStatus: exatamente 60 dias -> CRÍTICO 60 DIAS");
  eq(c(rowVenc(dateOffsetBR(10))), "CRÍTICO 60 DIAS",
     "computeStatus: 10 dias -> CRÍTICO 60 DIAS");
  // data passada: cálculo puro retorna CRÍTICO (o rótulo VENCIDO é só de apresentação na tabela)
  eq(c(rowVenc(dateOffsetBR(-30))), "CRÍTICO 60 DIAS",
     "computeStatus: data passada -> CRÍTICO no cálculo puro (VENCIDO é só apresentação)");
  // override textual de status
  eq(c({ status: "VIGENTE", vigencia_termino: dateOffsetBR(10) }), "VIGENTE",
     "computeStatus: texto 'VIGENTE' sobrepõe cálculo por data");
  eq(c({ status: "SEM DATA", vigencia_termino: dateOffsetBR(10) }), "SEM DATA",
     "computeStatus: texto 'SEM DATA' sobrepõe cálculo por data");
})();

// ---------------------------------------------------------------------
// 4) isConcluido  (concluído  <=> vigencia_termino < hoje)
// ---------------------------------------------------------------------
(function testIsConcluido() {
  const k = F.isConcluido;
  eq(k(rowVenc(dateOffsetBR(-1))), true, "isConcluido: ontem -> true");
  eq(k(rowVenc(dateOffsetBR(-365))), true, "isConcluido: 1 ano atrás -> true");
  eq(k(rowVenc(dateOffsetBR(0))), false, "isConcluido: hoje -> false (ainda ativo)");
  eq(k(rowVenc(dateOffsetBR(1))), false, "isConcluido: amanhã -> false");
  eq(k(rowVenc(dateOffsetBR(400))), false, "isConcluido: futuro distante -> false");
  eq(k(rowVenc("")), false, "isConcluido: sem data -> false (permanece em Ativos)");
  eq(k({}), false, "isConcluido: sem coluna -> false");
})();

// ---------------------------------------------------------------------
// 5) Coerência entre limiares e index.html
// ---------------------------------------------------------------------
(function testConstants() {
  eq(F.PRAZO_CRITICO_DIAS, 60, "constante: PRAZO_CRITICO_DIAS === 60");
  eq(F.PRAZO_ALERTA_DIAS, 180, "constante: PRAZO_ALERTA_DIAS === 180");
})();

// ---------------------------------------------------------------------
// 6) SCHEMA (CAMPOS) — integridade do refactor de aliases (Onda 2/B)
// ---------------------------------------------------------------------
(function testSchema() {
  const C = F.CAMPOS;
  eq(typeof C, "object", "CAMPOS: objeto existe");
  // idDisplay e idDedup DEVEM permanecer semanticamente distintos
  eq(JSON.stringify(C.idDisplay) === JSON.stringify(C.idDedup), false,
     "CAMPOS: idDisplay != idDedup (semânticas distintas preservadas)");
  eq(C.idDedup.includes("numero_processo"), true,
     "CAMPOS: idDedup inclui numero_processo (identidade de deduplicação)");
  eq(C.idDisplay.includes("numero_processo"), false,
     "CAMPOS: idDisplay NÃO inclui numero_processo (identidade de exibição)");
  // primeiros aliases coincidem com as colunas canônicas do CSV
  eq(C.termino[0], "vigencia_termino", "CAMPOS.termino canônico");
  eq(C.inicio[0], "vigencia_inicio", "CAMPOS.inicio canônico");
  eq(C.instituicao[0], "instituicao_parceira", "CAMPOS.instituicao canônico");
  // computeStatus continua lendo término via CAMPOS (prova indireta de wiring)
  eq(F.computeStatus({ vigencia_termino: "" }), "SEM DATA",
     "SCHEMA: computeStatus ainda resolve término via CAMPOS");
})();

// ---------------------------------------------------------------------
// Relatório
// ---------------------------------------------------------------------
console.log("");
console.log("FAROL — Suíte de testes de vigência (hoje fixado em 2026-07-24)");
console.log("---------------------------------------------------------------");
if (failed === 0) {
  console.log(`✓ Todos os ${passed} testes passaram.`);
  process.exit(0);
} else {
  console.log(`✗ ${failed} falha(s), ${passed} ok:\n`);
  console.log(failures.join("\n\n"));
  process.exit(1);
}
