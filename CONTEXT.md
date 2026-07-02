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

- **Data da última atualização:** 02/07/2026
- **Versão alvo:** v1.0 (prazo: 06/08/2026)
- **Fase atual:** SEMANA 2 — Projeção das demonstrações
- **O que está PRONTO e VALIDADO:**
  - Estrutura inicial de pastas e pacotes Python criada.
  - Arquivos de configuração criados: `config/setores.json`, `config/mapeamento_cvm.json` e `config/parametros.json`.
  - Templates de premissas criados em `data/premissas/` com campos individuais por ano.
  - `src/coleta/coletor_cvm.py` implementado para descobrir CD_CVM via dados da CVM, coletar DFP/ITR, mapear contas, registrar contas não mapeadas e persistir JSONs em `data/raw/cvm/`.
  - Coletor CVM validado localmente para DIRR3 e MGLU3: gera `_meta.json`, DRE, BP e DFC em JSON para as duas empresas.
  - DIRR3 e MGLU3 foram detectadas como `nao_financeira`.
  - Ambiente Python 3.11.9 com `.venv` criado; `pip check`, `black`, `flake8` e `pytest` executados com sucesso.
  - Excel de referência da Direcional movido para `tests/fixtures/Direcional_DIRR3_referencia.xlsx`.
  - `src/projecao/projetor_dre.py` criado: lê 8 premissas individuais de crescimento de receita e 8 de margem EBITDA, usa Ano 0 diretamente de `data/raw/cvm/` quando não há Parquet em `data/processed/`, projeta DRE de `ano1` a `ano8` e grava `data/processed/<TICKER>_projecao.json`.
  - `src/projecao/schedule_wk.py` criado: lê DSO/DIO/DPO de `data/premissas/<TICKER>_premissas.json`, usa a receita projetada em `data/processed/<TICKER>_projecao.json`, calcula contas a receber, estoques, fornecedores, NWC e ΔNWC de `ano1` a `ano8`, e grava o schedule em `wk` no JSON de projeção.
  - `data/premissas/MGLU3_premissas.json` criado a partir do template de não-financeiras com premissas genéricas conservadoras e campos anuais individuais para testar o pipeline.
  - `config/mapeamento_cvm.json` ampliado com nomes padronizados usados pela DRE projetada e pelo schedule WK: `ano_projecao`, `taxa_crescimento_receita`, `margem_ebitda`, `ebitda`, `nwc` e `delta_nwc`.
  - Testes do projetor de DRE criados em `tests/test_projetor_dre.py`; `black --check`, `flake8` e `pytest tests -v` passaram.
  - Testes do schedule WK criados em `tests/test_schedule_wk.py`; `black --check`, `flake8` e `pytest tests -v` passaram.
- **O que está EM PROGRESSO:**
  - Etapa 2 / Semana 2: projeção integrada das três demonstrações.
  - Validação humana dos números coletados para DIRR3 e MGLU3.
- **PRÓXIMA TAREFA:**
  - Semana 2: implementar o schedule PP&E.
- **Decisões de arquitetura tomadas nesta sessão:**
  - O coletor usa o cadastro de companhias abertas e os arquivos FCA da CVM para relacionar ticker negociado ao `CD_CVM`.
  - Como o FCA recente traz `CNPJ_Companhia` em vez de `CD_CVM`, o coletor cruza `FCA.CNPJ_Companhia` com `cad_cia_aberta.CNPJ_CIA` para obter o `CD_CVM`.
  - A persistência do Módulo 1 fica em `data/raw/cvm/<TICKER>_meta.json`, `data/raw/cvm/<TICKER>_dre.json`, `data/raw/cvm/<TICKER>_bp.json` e `data/raw/cvm/<TICKER>_dfc.json`.
  - Contas CVM fora de `config/mapeamento_cvm.json` são registradas em `logs/contas_cvm_nao_mapeadas.log` sem interromper a coleta.
  - Os dados persistidos mantêm campos brutos da CVM e adicionam `nome_padronizado`, `sinal_esperado` e `valor_padronizado`.
  - `.gitignore` foi ajustado para ignorar dados gerados (`data/raw`, `data/processed`, `outputs`, `logs`) e manter templates/estrutura via `.gitkeep`.
  - O projetor de DRE usa `data/processed/<TICKER>*.parquet` se existir; se não existir, usa diretamente `data/raw/cvm/<TICKER>_dre.json` com `nome_padronizado` e `valor_padronizado`.
  - A D&A fica como placeholder explícito em `depreciacao_amortizacao = 0.0` até o schedule PP&E sobrescrever a coluna.
  - O resultado financeiro fica como placeholder explícito em `resultado_financeiro = 0.0` até o schedule de dívida sobrescrever a coluna.
  - O IR/CSLL é gravado com sinal negativo; para empresas gerais usa 34% sobre EBT positivo, e para construtoras em RET usa 4% sobre receita.
  - O schedule WK mantém `fornecedores` como passivo negativo no BP; por isso o NWC é calculado como `contas_receber + estoques + fornecedores`, equivalente a `contas_receber + estoques - fornecedores_abs`.
  - O `delta_nwc` é gravado como variação aritmética (`NWC_t - NWC_(t-1)`); quando positivo, representa consumo de caixa e deve entrar no FCF como `-delta_nwc`.
  - Enquanto a DRE projetada não trouxer CPV/CMV projetado, o schedule WK usa o índice histórico `abs(cpv_cmv_ano0) / receita_ano0` como base de CPV para estoques e fornecedores; se não houver CPV histórico, cai para margem bruta opcional ou receita líquida como proxy comentada no código.
- **Bugs conhecidos / pendências:**
  - A validação numérica de Receita Líquida e Lucro Líquido contra RI/Status Invest ainda depende de conferência humana.
  - O RET deveria incidir sobre Receita Bruta, mas o coletor atual só traz Receita Líquida (CVM 3.01); a DRE projetada usa Receita Líquida como proxy até existir uma linha confiável de Receita Bruta.
  - `data/premissas/DIRR3_premissas.json` não está presente no repo local; a execução direta de `src/projecao/projetor_dre.py` e `src/projecao/schedule_wk.py` falha para DIRR3 com erro explícito até o arquivo real de premissas ser recolocado.

---

## 9. Divisão de Trabalho Humano vs. IA

- **Humano (Lucas):** ativa venv, preenche premissas com julgamento real, valida números contra fontes públicas, descreve bugs, commita no GitHub, atualiza este CONTEXT.md.
- **Codex:** cria/edita todos os arquivos Python, corrige bugs descritos, roda testes, gera gráficos, exporta Excel.
- **DeepSeek:** reservado apenas para validação de fórmula matemática (caso de borda).
- **Claude Code:** reservado apenas para revisão final de código.
