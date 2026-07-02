"""Testes do schedule de capital de giro da Semana 2."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.projecao.schedule_wk import projetar_wk


def salvar_json(caminho: Path, conteudo: object) -> None:
    """Salva JSON auxiliar para montar fixtures temporarias."""
    caminho.parent.mkdir(parents=True, exist_ok=True)
    with caminho.open("w", encoding="utf-8") as arquivo:
        json.dump(conteudo, arquivo, ensure_ascii=False)


def criar_mapeamento_wk_minimo(raiz: Path) -> None:
    """Cria o mapeamento minimo exigido pelo schedule WK."""
    campos = {
        "ano_projecao": {},
        "contas_receber": {},
        "estoques": {},
        "fornecedores": {},
        "nwc": {},
        "delta_nwc": {},
    }
    salvar_json(raiz / "config" / "mapeamento_cvm.json", {"campos": campos})


def criar_premissas_wk(raiz: Path, ticker: str = "TEST3") -> None:
    """Cria premissas com prazos medios em dias."""
    salvar_json(
        raiz / "data" / "premissas" / f"{ticker}_premissas.json",
        {
            "ticker": ticker,
            "setor": "varejo",
            "tipo": "nao_financeira",
            "dso": 36.5,
            "dio": 73.0,
            "dpo": 36.5,
        },
    )


def criar_projecao_dre(raiz: Path, ticker: str = "TEST3") -> None:
    """Cria DRE projetada minima com oito anos de receita."""
    dre = {}
    for ano in range(1, 9):
        dre[f"ano{ano}"] = {
            "ano_projecao": f"ano{ano}",
            "receita_liquida": 900.0 + (ano * 100.0),
        }
    salvar_json(
        raiz / "data" / "processed" / f"{ticker}_projecao.json",
        {
            "ticker": ticker,
            "tipo": "nao_financeira",
            "setor": "varejo",
            "ano0": {"receita_liquida": 1000.0},
            "dre": dre,
        },
    )


def criar_base_historica_wk(raiz: Path, ticker: str = "TEST3") -> None:
    """Cria saldos historicos CVM minimos para Ano 0 e indice CPV/receita."""
    base = {
        "ano_arquivo": 2025,
        "DT_FIM_EXERC": "2025-12-31",
        "ORDEM_EXERC": "ÚLTIMO",
    }
    bp = [
        {
            **base,
            "CD_CONTA": "1.01.03",
            "nome_padronizado": "contas_receber",
            "valor_padronizado": 100.0,
        },
        {
            **base,
            "CD_CONTA": "1.01.04",
            "nome_padronizado": "estoques",
            "valor_padronizado": 80.0,
        },
        {
            **base,
            "CD_CONTA": "2.01.02",
            "nome_padronizado": "fornecedores",
            "valor_padronizado": -60.0,
        },
    ]
    dre = [
        {
            **base,
            "CD_CONTA": "3.01",
            "nome_padronizado": "receita_liquida",
            "valor_padronizado": 1000.0,
        },
        {
            **base,
            "CD_CONTA": "3.02",
            "nome_padronizado": "cpv_cmv",
            "valor_padronizado": -400.0,
        },
    ]
    salvar_json(raiz / "data" / "raw" / "cvm" / f"{ticker}_bp.json", bp)
    salvar_json(raiz / "data" / "raw" / "cvm" / f"{ticker}_dre.json", dre)


def test_projetar_wk_calcula_nwc_e_delta_nwc(tmp_path: Path) -> None:
    """Valida formulas de saldos em dias e Delta NWC como consumo."""
    criar_mapeamento_wk_minimo(tmp_path)
    criar_premissas_wk(tmp_path)
    criar_projecao_dre(tmp_path)
    criar_base_historica_wk(tmp_path)

    resultado = projetar_wk("TEST3", raiz_projeto=tmp_path)
    wk = resultado["wk"]

    assert resultado["ano0_wk"]["nwc"] == pytest.approx(120.0)
    assert wk["ano1"]["contas_receber"] == pytest.approx(100.0)
    assert wk["ano1"]["estoques"] == pytest.approx(80.0)
    assert wk["ano1"]["fornecedores"] == pytest.approx(-40.0)
    assert wk["ano1"]["nwc"] == pytest.approx(140.0)
    assert wk["ano1"]["delta_nwc"] == pytest.approx(20.0)
    assert wk["ano2"]["delta_nwc"] == pytest.approx(14.0)

    caminho = tmp_path / "data" / "processed" / "TEST3_projecao.json"
    persistido = json.loads(caminho.read_text(encoding="utf-8"))
    assert persistido["ano0"]["wk"]["nwc"] == pytest.approx(120.0)
    assert persistido["wk"]["ano1"]["delta_nwc"] == pytest.approx(20.0)
