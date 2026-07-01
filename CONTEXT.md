# CONTEXT.md — Estado do Projeto DCF Automatizado

> **Este é o documento de continuidade entre sessões de IA (OpenAI Codex).**
> É colado no início de cada sessão do Codex e atualizado obrigatoriamente ao final de cada sessão.
> Sem ele, cada sessão de IA começa do zero e toma decisões de arquitetura conflitantes.
> **Trate este arquivo como a fonte única de verdade sobre o estado do projeto.**

---

## 1. Identidade do Projeto

- **Nome:** DCF Automatizado — Sistema de Valuation para Ações da B3
- **Autor:** Lucas Cruz — Ciências da Computação, Insper (2026)
- **Objetivo:** Automatizar o trabalho mecânico de um valuation por DCF (coleta, cálculo, visualização, exportação) preservando o trabalho intelectual (premissas) nas mãos do analista.
- **Benchmark de qualidade:** o modelo Excel da Direcional (DIRR3) do trainee InFinance, em `tests/fixtures/Direcional_DIRR3_referencia.xlsx`.

---

## 2. Escopo da v1.0 (NÃO EXPANDIR SEM AUTORIZAÇÃO EXPLÍCITA)

A v1.0 é **deliberadamente enxuta**. O objetivo é profundidade, não amplitude.

- **DIRR3 (construção civil):** implementação de referência, validada contra o Excel do trainee.
- **MGLU3 (varejo):** prova de universalidade, segundo setor não-financeiro.
- **Trilha financeira (FCFE/Ke):** a arquitetura é construída, mas a validação contra banco real fica para a v1.5. Não invista tempo tentando validar ITUB4 na v1.0.
- **Tickers fora de escopo na v1.0:** VALE3, PETR4, ITUB4 (todos v1.5).

> ⚠️ **Regra de ouro:** se surgir a tentação de "já que está quase pronto, adiciona mais um setor", NÃO faça. Cada setor novo é um poço de casos de borda de dados da CVM. Mantenha o foco em DIRR3 impecável + MGLU3 como prova.

---

## 3. Stack Técnica

- **Linguagem:** Python 3.11+
- **Coleta:** yfinance, python-bcb, requests
- **Processamento:** pandas, numpy, pyarrow (Parquet)
- **Visualização:** plotly, kaleido (PNG)
- **Exportação:** openpyxl (Excel 7 abas)
- **Front-end:** streamlit, streamlit-aggrid
- **Qualidade:** pytest, black, flake8
- **Infra:** python-dotenv

**Decisão de front-end travada:** Streamlit interativo + export HTML estático. O motor Python é a fonte única de verdade — NÃO reimplementar cálculo em JavaScript. O mesmo código que gera o Excel gera o dashboard.

---

## 4. Arquitetura — 5 Módulos Sequenciais

1. **Coleta** (`src/coleta/`) → CVM, yfinance, BACEN. Detecta financeira x não-financeira.
2. **Métricas históricas** (`src/metricas/`) → duas trilhas por tipo. Âncora para premissas.
3. **Interface de premissas** (`app.py` / `interface/`) → único input humano. 8 valores individuais por ano.
4. **Motor de cálculo** (`src/projecao/`, `src/valuation/`) → DRE/BP/DFC projetados, FCFF/FCFE, WACC/Ke, VT, EV, Target Price.
5. **Dashboard e outputs** (`src/visualizacao/`, `src/exportacao/`, `app.py`) → gráficos, Excel, front-end.

A ordem de cálculo do Módulo 4 é obrigatória: DRE → schedule WK → schedule PP&E → schedule Dívida → FCFF → WACC → VT → EV → Target Price.

---

## 5. Convenções de Código (SEGUIR EM TODO O PROJETO)

- **Idioma:** nomes de função, variável e comentário em português (o domínio é financeiro brasileiro). Ex.: `calcular_wacc`, `receita_liquida`, `divida_bruta`.
- **Nomes de colunas de DataFrame:** padronizados via `config/mapeamento_cvm.json`. Nunca inventar um nome de coluna novo sem registrar no mapeamento. Nomes consistentes entre TODOS os módulos (a mesma coluna se chama igual na coleta, na projeção e na exportação).
- **Sinais:** despesas e saídas de caixa sempre negativas. Receitas e entradas positivas.
- **Anos de projeção:** sempre 8, nomeados `ano1` a `ano8`. Crescimento, margem e CAPEX têm 8 campos individuais — NUNCA uma taxa única replicada.
- **Robustez da CVM:** todo acesso a campo da CVM trata o caso de campo ausente/renomeado sem quebrar silenciosamente. Campo não mapeado vai para log, não derruba o pipeline.
- **Valores negativos válidos:** ROIC, FCFF e LL podem ser negativos (empresa com prejuízo/crescimento agressivo). Não travar nesses casos.
- **Docstrings:** toda função tem docstring. Todo cálculo financeiro tem comentário com a fórmula.
- **Formatação:** black + flake8 antes de cada commit.
- **Testes:** cálculos financeiros têm teste pytest correspondente.

---

## 6. Fórmulas de Referência (fonte: Damodaran, McKinsey, Assaf Neto)

```
FCFF   = NOPAT + D&A − ΔNWC − CAPEX          onde NOPAT = EBIT × (1 − t)
FCFE   = LL + D&A − ΔNWC − CAPEX + ΔDívida Líquida
Ke_USD = Rf + Beta_realavancado × (ERP_EUA + CRP_Brasil)
Ke_BRL = [(1 + Ke_USD) × (1 + IPCA)] / (1 + CPI_EUA) − 1
WACC   = (E/V) × Ke_BRL + (D/V) × Kd × (1 − t)
TV     = FCFF₈ × (1 + g) / (WACC − g)         [não-financeira]
TV     = FCFE₈ × (1 + g) / (Ke − g)           [financeira]
EV     = Σ VP(FCFF_t) + VP(TV)
Equity = EV − Dívida Bruta + Caixa + Aplicações − Minoritários + Coligadas + Ativos Não Operacionais
Target Price = Equity Value / Ações Fully Diluted
```

**Regra tributária:** empresas gerais IR/CSLL sobre o EBT (34%). Construtoras no RET: 4% sobre a Receita Bruta.

**Tratamento de FCFF₈ negativo:** usar NOPAT normalizado do último ano como base do VT, com comentário explicando o ajuste.

---

## 7. Checklist de Consistência (Módulo 4)

Universais: g < taxa de desconto; g ≤ 5% BRL; taxa de reinvestimento 0-100%; VP(VT) < 85% do EV; ações fully diluted usadas.
Não-financeiras: balanço fecha nos 8 anos; ROIIC < 50% nos 2 últimos anos; CAPEX ≥ D&A na perpetuidade; FCO/EBITDA > 0,7x; Dívida Líquida/EBITDA < 4x.

---

## 8. Estado Atual do Projeto

> **ATUALIZAR ESTA SEÇÃO AO FINAL DE CADA SESSÃO.**

- **Data da última atualização:** 01/07/2026
- **Versão alvo:** v1.0 (prazo: 06/08/2026)
- **Fase atual:** SEMANA 0 — Fundação + Coleta inicial
- **O que está PRONTO e VALIDADO:**
  - Estrutura inicial de pastas e pacotes Python criada.
  - Arquivos de configuração criados: `config/setores.json`, `config/mapeamento_cvm.json` e `config/parametros.json`.
  - Templates de premissas criados em `data/premissas/` com campos individuais por ano.
  - `src/coleta/coletor_cvm.py` implementado para descobrir CD_CVM via dados da CVM, coletar DFP/ITR, mapear contas, registrar contas não mapeadas e persistir JSONs em `data/raw/cvm/`.
- **O que está EM PROGRESSO:**
  - Validação humana dos números coletados para DIRR3 e MGLU3.
- **PRÓXIMA TAREFA:**
  - Semana 1: implementar `src/coleta/coletor_mercado.py`.
- **Decisões de arquitetura tomadas nesta sessão:**
  - O coletor usa o cadastro de companhias abertas e os arquivos FCA da CVM para relacionar ticker negociado ao `CD_CVM`.
  - A persistência do Módulo 1 fica em `data/raw/cvm/<TICKER>_meta.json`, `data/raw/cvm/<TICKER>_dre.json`, `data/raw/cvm/<TICKER>_bp.json` e `data/raw/cvm/<TICKER>_dfc.json`.
  - Contas CVM fora de `config/mapeamento_cvm.json` são registradas em `logs/contas_cvm_nao_mapeadas.log` sem interromper a coleta.
  - Os dados persistidos mantêm campos brutos da CVM e adicionam `nome_padronizado`, `sinal_esperado` e `valor_padronizado`.
- **Bugs conhecidos / pendências:**
  - Execução do coletor, `black` e `flake8` não foram validados neste ambiente porque `py`, `python`, `black` e `flake8` não estão disponíveis no PATH.
  - O Excel `tests/fixtures/Direcional_DIRR3_referencia.xlsx` não está presente neste workspace atual; não havia arquivo `.xlsx` na raiz para mover.

---

## 9. Divisão de Trabalho Humano vs. IA

- **Humano (Lucas):** ativa venv, preenche premissas com julgamento real, valida números contra fontes públicas, descreve bugs, commita no GitHub, atualiza este CONTEXT.md.
- **Codex:** cria/edita todos os arquivos Python, corrige bugs descritos, roda testes, gera gráficos, exporta Excel.
- **DeepSeek:** reservado apenas para validação de fórmula matemática (caso de borda).
- **Claude Code:** reservado apenas para revisão final de código.
