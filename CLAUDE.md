# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Static single-page application (no build step, no dependencies, no package manager) listing researchers affiliated with the PAIC/FVS-RCP program (Programa de Apoio à Iniciação Científica da Fundação de Vigilância em Saúde do Amazonas).

## Running Locally

Because `index.html` loads `pesquisadores.json` via `fetch`, you must serve the project through an HTTP server (opening `index.html` directly as a `file://` URL will fail due to CORS restrictions):

```bash
python3 -m http.server 8080
# then open http://localhost:8080
```

## Architecture

The project consists of two main files:

- **`pesquisadores.json`** — the data source. An array of 15 researcher objects, sorted A-Z. Each object has the fields listed below.
- **`index.html`** — the full single-page application. Contains:
  - **CSS** (lines 7–423): embedded in `<style>`. Uses CSS custom properties (`--brand`, `--ink`, `--muted`, etc.) defined in `:root`. Responsive breakpoint at 780px. Footer uses class `.site-footer` with hardcoded color `#5f7f73` (not a CSS variable).
  - **HTML** (lines 425–493): static shell — header with logos, search/filter controls, empty `#cards` container, footer.
  - **JavaScript** (lines 494–end): embedded in `<script>`. No frameworks. Key concerns:
    - `PESQUISADORES` is initialized with all 15 researchers hardcoded inline in the script. This ensures the page always renders even if the fetch fails (e.g., GitHub Pages cache delay).
    - On page load, `fetch('pesquisadores.json')` also runs and overwrites `PESQUISADORES` if successful, keeping the JSON as the authoritative source for future updates.
    - `getFiltered()` — applies text search + sort to the data array. Always sorts A-Z by default before applying any user-selected sort override.
    - `render()` — builds and injects HTML strings into `#cards` via `innerHTML`. Uses `escapeHtml()` and `escapeAttr()` to prevent XSS.
    - If the fetch fails, the page still renders using the inline data.

## Asset Structure

```
pesquisadores.json   researcher data (sorted A-Z)
fotos/               researcher photos (filename referenced in pesquisadores.json[].foto)
logos/               institutional logos loaded in the header
img/                 placeholder_pesquisador.png (present but unused — inline SVG is used instead)
```

Photos are referenced as `"fotos/" + x.foto`. If a photo fails to load, an inline SVG silhouette placeholder is shown. Logo images fall back to text abbreviations via `onerror`.

## Adding or Updating a Researcher

Edit `pesquisadores.json`. Each object must have exactly these fields:

```json
{
  "nome": "",
  "foto": "filename.jpg",
  "lattes": "https://...",
  "email": "",
  "formacao_base": "",
  "descricao_titulacao": "",
  "diretoria_lotacao": "",
  "linhas": ["linha 1", "linha 2"]
}
```

The page always renders researchers sorted A-Z regardless of the order entries appear in the JSON file (sorting is applied after fetch).

**Important:** whenever a researcher is added or updated, **both** `pesquisadores.json` and the inline `PESQUISADORES` array in `index.html` must be updated to stay in sync.

### Padrão obrigatório para `diretoria_lotacao`

O campo `diretoria_lotacao` deve sempre seguir o formato **Nome completo do local - SIGLA**, por exemplo:

- `"Departamento de Vigilância Epidemiológica - DVE"` ✓
- `"Laboratório Central de Saúde Pública - LACEN"` ✓
- `"Diretoria de Ensino, Pesquisa e Inovação - DEPI"` ✓

**Nunca** use o formato invertido `"SIGLA (Nome)"` ou `"Nome - SIGLA"` com nome abreviado. O formulário Google Forms pode inserir os dados na ordem errada (sigla antes do nome); sempre corrigir para o padrão acima ao inserir ou atualizar dados.

## Efeito Hover nos Cards (reutilizável)

Borda esquerda colorida que acende na cor institucional (`var(--brand)`) ao passar o mouse, com transição suave. Para reutilizar em outro projeto, substitua `var(--line)` pela cor neutra de borda e `var(--brand)` pela cor de destaque do projeto.

```css
.card {
  border: 1px solid var(--line);
  border-left: 4px solid var(--line);        /* borda esquerda mais grossa, cor neutra no repouso */
  transition: transform .22s ease, box-shadow .22s ease, border-color .22s ease;
}

.card:hover {
  transform: translateY(-2px);               /* leve lift */
  border-color: #d6e4de;                     /* borda geral clareia */
  border-left-color: var(--brand);           /* borda esquerda acende na cor institucional */
  box-shadow: 0 10px 22px rgba(28, 54, 47, 0.08);
}
```

## GitHub Pages Deployment

The entry point for GitHub Pages is `index.html` at the repository root. This file is the full application (not a redirect). Both `index.html` and `pesquisadores.json` must be present at the repository root for the page to work.

## Changelog

| Date       | Description                                                  |
|------------|--------------------------------------------------------------|
| 2026-03-21 | Initial review. Created CLAUDE.md, .gitignore, index.html redirect for GitHub Pages. |
| 2026-03-21 | Refactor: extracted researcher data into pesquisadores.json (sorted A-Z); rewrote index.html to load data via fetch with automatic A-Z sort and fetch error handling; deleted index_pesquisadores.html; added *.xlsx and *.xls to .gitignore; fixed Samyly's Lattes URL from http:// to https://; updated CLAUDE.md. |
| 2026-03-21 | Footer redesign: replaced two-column footer (`<footer>`) with centered single-column layout (`<footer class="site-footer">`). New footer shows FVS-RCP • DEPI title, full institution name, DEPI, address. Background color changed from `var(--brand)` to hardcoded `#5f7f73`. Old CSS classes (`.footer-inner`, `.footer-left`, `.footer-text`, `.footer-label`, `.footer-address`) removed; new classes (`.site-footer`, `.site-footer-inner`, `.footer-title`, `.footer-divider`, `.footer-copy`) added. |
| 2026-03-21 | Card hover enhancements: added `border-left: 4px solid var(--line)` to `.card` (default state) that transitions to `border-left-color: var(--brand)` on hover, creating a colored left-side accent. The existing translateY(-2px) lift and photo zoom (scale 1.045) effects were preserved. |
| 2026-03-21 | Added researcher Lara Bezerra de Oliveira de Assis (Enfermeira, Mestre em Enfermagem em Saúde Pública, DVE) to pesquisadores.json. Photo to be added manually as fotos/lara_bezerra.jpg. |
| 2026-03-21 | Architecture change: PESQUISADORES array in index.html now initialized with all 15 researchers hardcoded inline, eliminating blank-page risk from GitHub Pages cache/fetch delays. The fetch from pesquisadores.json still runs and overwrites the data when available. Both files must be kept in sync when adding or updating researchers. |
| 2026-03-21 | Data correction: normalized `diretoria_lotacao` across all researchers. "Laboratório Central - LACEN" → "Laboratório Central de Saúde Pública - LACEN" (5 researchers). "DVE (Vigilância Epidemiológica)" and "Vigilância Epidemiológica - DVE" → "Departamento de Vigilância Epidemiológica - DVE" (Lara Bezerra and Samyly Coutinho). Defined standard format: Nome completo - SIGLA. Updated both pesquisadores.json and index.html inline array. |
| 2026-03-22 | Visual and structural refinement of index.html (only file changed; pesquisadores.json untouched). Bug fix: `render()` was never called with inline data on page load — fetch failure showed an error instead of rendering the fallback data; fixed by calling `render()` immediately and making the fetch catch block silent. Removed `.num` sequential badge (lost meaning when filtered). Card redesigned: photo column narrowed (100×128px), content hierarchy tightened (name 700/17px → formação 600/13.5px → titulação italic/muted → diretoria badge → research lines → contact footer). Diretoria badge changed from full pill (`border-radius:999px`) to soft rectangle (`7px`) to support long names without overflow; inline building SVG icon added. Card footer bar added with email and Lattes links separated by a border line, each with inline SVG icon. Select styled with embedded SVG chevron (no external dependency). Search input wrapped in `<label>` with positioned SVG icon. Accessibility: `:focus-visible` global rule added; `aria-label` on all controls; `aria-live="polite"` on count badge; `.sr-only` utility class; `role="list/listitem"` on card container. Empty state redesigned with SVG illustration and descriptive text. Footer background changed to `--brand-dark` (#3a5e55) for better contrast. Token `--brand` adjusted to `#4d7269`. Responsive: mobile stacks photo above content, reduced photo size (84×108px), header subtitle hidden on small screens. |
| 2026-03-22 | Novo filtro "Diretoria / Lotação": adicionado `<select id="filtroDiretoria">` ao `search-row`; função `populateDiretoriaFilter()` gera as opções dinamicamente a partir dos dados carregados (deduplicadas, ordenadas A-Z, seleção preservada ao recarregar); `getFiltered()` estendida com filtro por igualdade exata em `diretoria_lotacao`; evento `change` no novo select; chamadas a `populateDiretoriaFilter()` na inicialização e após fetch bem-sucedido. Apenas `index.html` alterado. |
| 2026-03-22 | Botão "Voltar ao PAIC": adicionado `<a href="#" class="btn-voltar">` com ícone SVG inline, estilo pill discreto (borda `var(--brand)`, fundo transparente, hover `var(--brand-light)`), posicionado antes da `section.controls-bar` dentro de `<main>`. Apenas CSS + HTML, sem JS. |
| 2026-03-22 | Substituição da paleta de verde institucional: `--brand` #4d7269 → #2f6f5f; `--brand-dark` #3a5e55 → #1e5444; `--brand-light` #eaf3ef → #e8f1ee; `--dir-bg` #e6f1ec → #e8f1ee; `theme-color` meta atualizado; rgba de focus rings e sombras de hover recalculados (77,114,105 → 47,111,95 e 22,49,44 → 30,84,68); texto de linhas de pesquisa #2e5048 → #1e4a3c. Cores extraídas do site institucional depi-fvs-rcp.github.io/Editais-Abertos-FAPEAM/ (variáveis `--btn: #2f6f5f` e `--pill: #e8f1ee`). Zero ocorrências residuais do verde anterior confirmadas. |
| 2026-03-22 | Filtro de Titulação: adicionado `<select id="filtroTitulacao">` ao `search-row`; função `categoriaTitulacao()` classifica `descricao_titulacao` em 6 categorias (Pós-Doutorado, Doutorado, Mestrado, Especialização, Residência, Graduação) por `includes()` case-insensitive; `populateTitulacaoFilter()` popula o select apenas com categorias presentes nos dados, ordenadas por hierarquia acadêmica definida em `TITULACAO_ORDEM`; filtro aplicado em `getFiltered()` compondo-se com busca de texto e filtro de diretoria; evento `change` e chamadas na inicialização e após fetch. |
| 2026-03-22 | Reorganização do header: `flex-wrap: wrap` → `flex-wrap: nowrap` em `.header-inner` (logos e título nunca quebram para nova linha); `flex-direction: row` + `flex-shrink: 0` explicitados em `.logos` (três logos em linha horizontal garantida); `min-width: 180px` → `min-width: 0` em `.header-title` (comprime livremente sem forçar quebra). Apenas CSS, sem HTML novo. |
| 2026-03-22 | Reestruturação do header e controles (sessão 3): botão "Voltar ao PAIC" migrado do `<main>` para o `.header-inner` ao lado do badge de contagem; CSS do `.btn-voltar` reescrito para contexto de header escuro (branco/semi-transparente); adicionado token `--header-bg: #5f7f73` (extraído do arquivo local FAPEAM); `.site-header` e `.site-footer` passam a usar `var(--header-bg)` em vez de `--brand` e `--brand-dark`; removido `max-width/margin:auto` do `.header-inner` (logos flush ao canto superior esquerdo, padrão FAPEAM); controles divididos em dois rows — `search-row` (busca + Nome A-Z) e `filter-row` (Titulação + Diretoria); ordem dos selects reordenada: Nome A-Z em cima, Titulação+Diretoria em baixo; `.t2` do header recebeu `font-weight: 700`. |
| 2026-03-22 | Correção de dados (sessão 4): "Doutor em" → "Doutor(a) em" em todos os 8 campos `descricao_titulacao` que continham doutorado (`pesquisadores.json` + array inline `index.html`); "Mestre em Enfermagem em Saúde Pública" → "Mestre em Enfermagem e Saúde Pública" (Lara Bezerra, apenas `pesquisadores.json` — `index.html` já estava correto). |
| 2026-03-22 | Sessão de auditoria e documentação. Nenhum arquivo de código foi alterado. Consulta realizada: data/hora da última modificação de index.html (22/03/2026 às 12:16 via `ls -la`). Diagnóstico: projeto não possui repositório git, impossibilitando recuperação do histórico de comandos de sessões anteriores. Recomendação registrada: inicializar `git init` para rastreabilidade futura. Atualização do CLAUDE.md com novo padrão de entrada de histórico técnico (seções: Alterações realizadas, Justificativa técnica, Impacto no sistema, Arquivos afetados, Recomendações futuras). |

---

## Atualização — 2026-03-22

### Alterações realizadas

- Nenhum arquivo de código-fonte foi modificado nesta sessão.
- Realizada consulta de metadados do arquivo `index.html` via `ls -la` para verificar data e hora da última modificação: **22/03/2026 às 12:16**.
- Diagnosticado que o projeto **não possui repositório git** (`git init` nunca foi executado), o que impede a recuperação do histórico de comandos e commits de sessões anteriores.
- Atualizado `CLAUDE.md`: adicionada nova entrada no Changelog (linha da tabela) e criado o presente bloco de histórico técnico detalhado no novo formato padronizado.

### Justificativa técnica

O usuário solicitou rastreabilidade da sessão de trabalho. Como o projeto não utiliza controle de versão git, o único registro disponível de modificações anteriores é o timestamp do sistema de arquivos (`mtime`). O histórico de comandos entre sessões do Claude Code não persiste — cada sessão é independente. A documentação manual no CLAUDE.md é, portanto, o único mecanismo de rastreabilidade disponível enquanto o projeto não tiver um repositório git.

### Impacto no sistema

- Nenhum impacto funcional. A aplicação permanece inalterada.
- CLAUDE.md passa a ter um novo padrão de registro técnico detalhado, complementar à tabela de Changelog já existente.

### Arquivos afetados

| Arquivo     | Tipo de alteração          |
|-------------|----------------------------|
| `CLAUDE.md` | Atualizado (documentação)  |

### Recomendações futuras

1. **Inicializar repositório git** (`git init` + `.gitignore` já presente) e fazer um commit inicial com o estado atual do projeto. Isso permitirá rastrear exatamente quais arquivos foram alterados, quando e com qual mensagem descritiva — tornando desnecessário o registro manual de comandos.
2. **Adotar este formato de entrada** para todas as sessões de trabalho futuras, mantendo tanto a tabela de Changelog (visão rápida) quanto o bloco detalhado (contexto técnico completo).
3. Considerar adicionar um campo `"updated_at"` ou similar ao `pesquisadores.json` para rastrear a última atualização de cada pesquisador individualmente.

---

## Atualização — 2026-03-22 (sessão 2)

### Alterações realizadas

1. **Filtro "Diretoria / Lotação"** (`<select id="filtroDiretoria">`):
   - Adicionado ao `search-row` antes do select de ordenação.
   - Função `populateDiretoriaFilter()`: extrai valores únicos de `diretoria_lotacao`, ordena A-Z, reconstrói o select preservando seleção ao recarregar.
   - `getFiltered()` estendida com filtro por igualdade exata (`===`) em `diretoria_lotacao`.
   - Evento `change` registrado; chamadas na inicialização e após fetch bem-sucedido.

2. **Botão "Voltar ao PAIC"** (`.btn-voltar`):
   - `<a href="#" class="btn-voltar">` com ícone SVG inline de seta, inserido dentro de `<main>` antes da `section.controls-bar`.
   - Estilo pill discreto: borda `1.5px solid var(--brand)`, fundo transparente, hover preenche `var(--brand-light)` e escurece borda.
   - Implementação exclusivamente HTML + CSS, sem JavaScript.

3. **Substituição da paleta de verde institucional**:
   - Cores extraídas do site `depi-fvs-rcp.github.io/Editais-Abertos-FAPEAM/` via fetch do CSS-fonte.
   - `--brand`: `#4d7269` → `#2f6f5f` (verde de ação institucional, variável `--btn` do site de referência).
   - `--brand-dark`: `#3a5e55` → `#1e5444`.
   - `--brand-light`: `#eaf3ef` → `#e8f1ee` (verde claro de pills, variável `--pill` do site de referência).
   - `--dir-bg`: `#e6f1ec` → `#e8f1ee`.
   - `theme-color` meta: `#4d7269` → `#2f6f5f`.
   - `rgba(77,114,105,…)` → `rgba(47,111,95,…)` (focus rings — 2 ocorrências).
   - `rgba(22,49,44,.09)` → `rgba(30,84,68,.09)` (sombra hover card).
   - `#2e5048` → `#1e4a3c` (texto das linhas de pesquisa).
   - Verificação pós-substituição: 0 ocorrências residuais do verde anterior.

4. **Filtro de Titulação** (`<select id="filtroTitulacao">`):
   - Inserido no `search-row` antes do `filtroDiretoria`.
   - Constante `TITULACAO_ORDEM`: define hierarquia acadêmica — `["Pós-Doutorado","Doutorado","Mestrado","Especialização","Residência","Graduação"]`.
   - Função `categoriaTitulacao(descricao)`: classifica texto livre em 6 categorias por `includes()` case-insensitive, com variantes ortográficas tratadas (`residência/residencia`, `pós-doc/pos-doc`, `graduação/graduacao`). Retorna `null` se não encaixar.
   - Função `populateTitulacaoFilter()`: coleta categorias presentes, ordena pela `TITULACAO_ORDEM`, reconstrói select preservando seleção.
   - Filtro aplicado em `getFiltered()` após filtro de texto e antes do filtro de diretoria.
   - Evento `change` e chamadas na inicialização e após fetch.

5. **Reorganização do header** (apenas CSS):
   - `.header-inner`: `flex-wrap: wrap` → `flex-wrap: nowrap`. Logos, título e badge nunca quebram para nova linha.
   - `.logos`: adicionados `flex-direction: row` e `flex-shrink: 0` explicitamente. Três logos garantidas em linha horizontal sem encolhimento.
   - `.header-title`: `min-width: 180px` → `min-width: 0`. Título comprime livremente quando espaço é limitado, sem forçar quebra.

### Justificativa técnica

- **Filtros dinâmicos**: gerados a partir dos dados reais em vez de valores hardcoded, garantindo que novas diretorias ou titulações inseridas em `pesquisadores.json` apareçam automaticamente sem alterar o código. A seleção é preservada ao recarregar para não degradar UX após o fetch.
- **Categorização de titulação**: o campo `descricao_titulacao` é texto livre (ex.: "Doutor em Ciências", "Mestre em Saúde Pública"), portanto não pode ser filtrado por igualdade exata. A função `categoriaTitulacao()` normaliza para categorias canônicas via correspondência por substring, tornando o filtro robusto a variações de redação.
- **Paleta institucional**: a cor `#2f6f5f` é mais saturada e contrastante que a anterior `#4d7269`, melhorando a legibilidade em elementos de ação (bordas de hover, links, botões). O `#e8f1ee` é idêntico ao usado nos badges do site FAPEAM, garantindo consistência visual entre os dois produtos.
- **Header nowrap**: `flex-wrap: wrap` em um flex container com três elementos de tamanhos díspares (logos fixas + título flexível + badge) produz quebras imprevisíveis em viewports intermediárias (~600–780px). `nowrap` + `min-width: 0` no título resolve o problema pelo mecanismo correto de flexbox.

### Impacto no sistema

- Três novos controles de filtro ativos e compostos: busca por texto + titulação + diretoria + ordenação funcionam simultaneamente.
- A paleta de cor afeta todos os elementos de destaque visual: hover de cards, focus rings, pills de diretoria, botão voltar, links de contato, borda esquerda dos cards, sombras.
- O header é visualmente estável em todas as viewports (desktop, tablet, mobile), sem risco de quebra de linha.
- Nenhuma alteração em `pesquisadores.json`. Nenhuma alteração na estrutura dos cards ou tipografia.

### Arquivos afetados

| Arquivo      | Tipo de alteração                        |
|--------------|------------------------------------------|
| `index.html` | Atualizado (HTML + CSS + JS)             |
| `CLAUDE.md`  | Atualizado (documentação)                |

### Recomendações futuras

1. **Limpar o `href="#"` do botão "Voltar ao PAIC"** assim que a URL de destino estiver definida.
2. **Testar os filtros com dados novos**: ao adicionar pesquisadores com titulações não previstas, verificar se `categoriaTitulacao()` retorna `null` e decidir se uma categoria genérica ("Outros") é necessária.
3. **Avaliar `flex-wrap: nowrap` no mobile muito estreito** (< 360px): o badge de contagem pode ser eliminado ou ocultado via media query se o espaço for insuficiente.
4. **Inicializar repositório git** — recomendação reiterada da sessão anterior.

---

## Atualização — 2026-03-22 (sessão 3)

### Alterações realizadas

1. **Botão "Voltar ao PAIC" migrado para o header**:
   - Removido de `<main>` (onde ficava antes da `section.controls-bar`) e inserido dentro de `.header-inner`, após o badge `#chipTotal`.
   - CSS `.btn-voltar` completamente reescrito para contexto de header escuro: `color: #fff`, `border: 1.5px solid rgba(255,255,255,.45)`, `background: transparent`, `flex-shrink: 0`, `white-space: nowrap`. Hover: `background: rgba(255,255,255,.14)` + `border-color: rgba(255,255,255,.75)`. Removidos `margin-bottom` e referências a `var(--brand)` e `var(--brand-light)`.

2. **Cor de fundo do header e footer alinhada ao padrão FAPEAM**:
   - Adicionado token `--header-bg: #5f7f73` ao `:root` (extraído do arquivo local `Editais-Abertos-FAPEAM-main/index.html`, variável `--brand` do projeto de referência).
   - `.site-header`: `background: var(--brand)` → `background: var(--header-bg)`.
   - `.site-footer`: `background: var(--brand-dark)` → `background: var(--header-bg)`.
   - Header e footer passam a ter o mesmo verde médio institucional (`#5f7f73`), consistente com o site FAPEAM. O token `--brand` (`#2f6f5f`) permanece exclusivo para elementos de ação e destaque (hover, focus, links).

3. **Layout do header — logos flush à esquerda (padrão FAPEAM)**:
   - Removidos `max-width: 1100px` e `margin: 0 auto` do `.header-inner`. O header agora é full-width com `padding: 12px 20px`, e as logos ficam literalmente no canto superior esquerdo da página — idêntico ao comportamento do site FAPEAM de referência.

4. **Controles de busca divididos em dois rows**:
   - `.search-row` (linha de cima): campo de busca + select **Nome (A–Z)** (`#ord`).
   - `.filter-row` (linha de baixo): select **Titulação (todas)** (`#filtroTitulacao`) + select **Diretoria (todas)** (`#filtroDiretoria`).
   - Adicionada classe `.filter-row` ao CSS com mesma estrutura do `.search-row` mais `margin-top: 10px`.
   - Ordem final resultado de duas iterações: primeiro titulação em cima + nome em baixo; depois invertido para nome em cima + titulação/diretoria em baixo (estado atual).

5. **Subtítulo do header em negrito**:
   - `.header-title .t2`: adicionado `font-weight: 700`. Cor e opacidade (`.82`) mantidas.

### Justificativa técnica

- **Botão no header**: o botão de navegação global pertence ao header (elemento persistente sticky), não ao conteúdo da página. Posicioná-lo ao lado do badge de contagem cria uma zona de ação coesa no canto direito do header, sem ocupar espaço do conteúdo principal.
- **`--header-bg` separado de `--brand`**: o verde de fundo do header/footer (`#5f7f73`) é mais claro e suave que o verde de ação (`#2f6f5f`). Usar o mesmo token para ambos produziria contraste insuficiente em elementos interativos. A separação em tokens distintos é a abordagem correta para sistemas de design com múltiplos papéis de cor.
- **Remoção do `max-width` no header**: no site FAPEAM de referência o header é full-width, o que cria a percepção de solidez institucional. A `max-width` no header produzia um efeito visual de "header flutuante" inconsistente com o rodapé (também full-width). O conteúdo principal (`<main>`) mantém seu `max-width: 1100px`.
- **Dois rows de controles**: separa semanticamente busca/ordenação (row 1) de filtragem por categoria (row 2), tornando a interface mais escaneável. A ordenação (Nome A-Z) fica próxima ao campo de busca por ser o controle mais usado; os filtros de categoria ficam agrupados na linha inferior.

### Impacto no sistema

- O header agora usa `#5f7f73` (mais claro) em vez de `#2f6f5f` (mais escuro), alterando a percepção visual de profundidade do topo da página.
- O rodapé agora usa `#5f7f73` em vez de `#1e5444`, ficando mais claro e alinhado com o header — header e footer visualmente "enquadram" a página com a mesma cor.
- Nenhuma alteração em `pesquisadores.json`, estrutura dos cards, tipografia ou lógica JS de filtros.

### Arquivos afetados

| Arquivo      | Tipo de alteração             |
|--------------|-------------------------------|
| `index.html` | Atualizado (HTML + CSS)       |
| `CLAUDE.md`  | Atualizado (documentação)     |

### Recomendações futuras

1. **Definir a URL de destino do botão "Voltar ao PAIC"** — atualmente `href="#"`.
2. **Avaliar visibilidade do header em mobile muito estreito** (< 380px): com `flex-wrap: nowrap`, logos + título + badge + botão podem ficar comprimidos. Considerar ocultar o botão "Voltar ao PAIC" abaixo de um breakpoint via `display: none`.
3. **Inicializar repositório git** — recomendação reiterada.

---

## Atualização — 2026-03-22 (sessão 4)

### Alterações realizadas

1. **Linguagem inclusiva em titulações de doutorado**:
   - Substituído `"Doutor em"` por `"Doutor(a) em"` em todos os 8 registros com doutorado, em `pesquisadores.json` e no array inline do `index.html`.
   - Pesquisadores afetados: Augusto Kluczkovski Jr., Claudio Fernández, Elder Figueira, Erian Santos, Leíse Fernandes *(Médica Veterinária)*, Rejane Simões *(Bióloga)*, Tatiana Amaral *(Biomédica)*, Walter Oliva.
   - A função `categoriaTitulacao()` permanece funcional — a busca por substring `"doutor"` (case-insensitive) continua presente em `"doutor(a)"`.

2. **Correção textual da titulação de Lara Bezerra**:
   - `pesquisadores.json`: `"Mestre em Enfermagem em Saúde Pública"` → `"Mestre em Enfermagem e Saúde Pública"`.
   - `index.html` já continha a forma correta — nenhuma alteração necessária nesse arquivo para este campo.

### Justificativa técnica

- **Doutor(a)**: o campo `descricao_titulacao` exibia a forma masculina para pesquisadoras com `formacao_base` feminina (ex.: "Biomédica", "Bióloga", "Médica Veterinária"), criando inconsistência de gênero visível no card. A forma inclusiva `Doutor(a)` resolve a inconsistência sem exigir lógica de inferência de gênero no código.
- **"em" → "e"**: a preposição "em" tornava a frase ambígua ("Enfermagem em Saúde Pública" pode ser lida como uma subárea). A conjunção "e" expressa corretamente dois campos distintos de formação.

### Impacto no sistema

- Alteração exclusivamente de dados — nenhuma lógica JS, CSS ou estrutura HTML foi modificada.
- O filtro de titulação (categoria "Doutorado") continua funcionando corretamente, pois `categoriaTitulacao()` usa `includes("doutor")` case-insensitive.
- Os dois arquivos de dados (`pesquisadores.json` e array inline) estão em sincronia.

### Arquivos afetados

| Arquivo               | Tipo de alteração          |
|-----------------------|----------------------------|
| `pesquisadores.json`  | Atualizado (dados)         |
| `index.html`          | Atualizado (dados inline)  |
| `CLAUDE.md`           | Atualizado (documentação)  |

### Recomendações futuras

1. **Revisar titulações de mestrado** da mesma forma — verificar se algum campo "Mestre em" deveria ser "Mestre(a) em" para consistência de gênero, ou adotar a forma inclusiva globalmente.
2. **Padronizar capitalização** em titulações: "Mestre em saúde pública" (minúscula) vs "Mestre em Saúde Pública" (maiúscula) — há inconsistências nos dados atuais. *(Resolvido na sessão 2026-03-23.)*
3. **Inicializar repositório git** — recomendação reiterada.

---

## Atualização — 2026-03-23

### Alterações realizadas

1. **Correção de capitalização em dois campos `descricao_titulacao`**:
   - `"Mestre em saúde pública"` → `"Mestre em Saúde Pública"` (Layssa do Carmo Barroso).
   - `"Mestre em Doenças tropicais e infecciosas"` → `"Mestre em Doenças Tropicais e Infecciosas"` (Lisele Maria Brasileiro Martins).
   - Alteração aplicada em **ambos** os arquivos (`pesquisadores.json` e array inline de `index.html`).

2. **Inserção de dois novos pesquisadores**:

   - **Jair dos Santos Pinheiro** — Enfermeiro, Mestre em Enfermagem, DIPRE.
     - Lattes: `https://lattes.cnpq.br/9843437860851297`
     - E-mail: `jpsantos.jair@gmail.com`
     - Foto: `fotos/jair_pinheiro.jpg` *(a ser adicionada manualmente)*
     - Linhas: Gestão do trabalho e educação em vigilância em saúde; Vigilância das doenças transmissíveis e não transmissíveis na Amazônia.

   - **Fabiana Bianchet** — Enfermeira, Mestre em Saúde e Gestão do Trabalho, DVHQ.
     - Lattes: `https://lattes.cnpq.br/3322590851570635`
     - E-mail: `fabianabianchet@gmail.com`
     - Foto: `fotos/fabiana_bianchet.jpg` *(a ser adicionada manualmente)*
     - `diretoria_lotacao`: `"Diretoria de Vigilância Hospitalar e Qualidade - DVHQ"` — nova diretoria ainda não presente nos dados anteriores; o filtro de Diretoria a exibirá automaticamente.
     - Linhas: Gestão do trabalho e educação em vigilância em saúde; Vigilância das doenças transmissíveis e não transmissíveis na Amazônia.

   - Inserção feita no final do array em **ambos** os arquivos, mantendo identação e formatação existentes. Total de pesquisadores: **17**.

### Justificativa técnica

- **Capitalização**: o padrão adotado no projeto é title case para nomes de áreas do conhecimento (ex.: "Saúde Pública", "Doenças Tropicais"). As duas entradas corretas estavam em minúscula, criando inconsistência visual e potencial problema no filtro de titulação (a função `categoriaTitulacao()` usa `includes()` case-insensitive, portanto não era afetada funcionalmente, mas a exibição no card ficava inconsistente).
- **Novos pesquisadores**: inseridos no final do array conforme padrão do projeto. A ordenação A-Z é aplicada dinamicamente pela função `getFiltered()` em tempo de execução, de modo que a posição de inserção no array não afeta a ordem de exibição.
- **`diretoria_lotacao` da Fabiana Bianchet**: seguiu o padrão obrigatório do projeto — "Nome completo - SIGLA". A DVHQ é uma nova diretoria que passará a aparecer automaticamente no filtro dinâmico `populateDiretoriaFilter()` sem nenhuma alteração de código.
- **Fonte dos dados**: dados oriundos de formulário Google Forms (23/03/2026). Nome `"JAIR DOS SANTOS PINHEIRO"` corrigido para `"Jair dos Santos Pinheiro"` (primeira letra maiúscula, demais minúsculas) conforme padrão do projeto. Lattes de Jair continha `"ttps://"` (sem o `h` inicial) no formulário — corrigido para `"https://"`.

### Impacto no sistema

- Total de pesquisadores passa de 15 para **17**.
- O filtro de Diretoria ganha uma nova opção: `"Diretoria de Vigilância Hospitalar e Qualidade - DVHQ"`.
- O filtro de Titulação não ganha nova categoria — "Mestre em Enfermagem" e "Mestre em Saúde e Gestão do Trabalho" são classificados como "Mestrado" pela função `categoriaTitulacao()` (via `includes("mestre")`).
- Nenhuma alteração em CSS, HTML estrutural, filtros, header ou footer.
- Os dois arquivos de dados (`pesquisadores.json` e array inline) estão em sincronia.

### Arquivos afetados

| Arquivo               | Tipo de alteração                              |
|-----------------------|------------------------------------------------|
| `pesquisadores.json`  | Atualizado (correção de dados + 2 novos)       |
| `index.html`          | Atualizado (correção de dados + 2 novos inline)|
| `CLAUDE.md`           | Atualizado (documentação)                      |

### Recomendações futuras

1. **Adicionar as fotos** `fotos/jair_pinheiro.jpg` e `fotos/fabiana_bianchet.jpg` manualmente — até lá, o card exibirá o silhueta SVG de placeholder.
2. **Inicializar repositório git** — recomendação reiterada. Com 17 pesquisadores e histórico crescente, o controle de versão torna-se cada vez mais necessário para rastrear alterações de dados sem depender do CLAUDE.md.
