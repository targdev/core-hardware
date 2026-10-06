"""Testes unitários para os mini dashboards de benchmarks e comparativos de hardware."""

import pytest
from app.benchmarks import (
    gerar_dashboard_comparativo_notebooks,
    gerar_dashboard_gpu,
    gerar_dashboard_perifericos,
    gerar_dashboard_monitor,
    obter_dashboard_benchmarks,
)


def test_gerar_dashboard_comparativo_notebooks():
    """Valida a estrutura do dashboard comparativo dos 3 notebooks."""
    dash = gerar_dashboard_comparativo_notebooks()
    assert dash["tipo"] == "comparativo_notebooks"
    assert len(dash["produtos"]) == 3

    mac = next(p for p in dash["produtos"] if p["id"] == "NOTE-01")
    legion = next(p for p in dash["produtos"] if p["id"] == "NOTE-03")

    assert mac["estoque"] == 4
    assert mac["status"] == "disponivel"
    assert "scores" in mac
    assert mac["scores"]["Bateria (até 18h)"] == 98

    # Lenovo Legion Pro 5 deve refletir estoque esgotado
    assert legion["estoque"] == 0
    assert legion["status"] == "esgotado"
    assert legion["scores"]["GPU / Gráficos"] >= 90


def test_gerar_dashboard_gpu():
    """Valida o dashboard de telemetria da GPU RTX 4060 Ti."""
    dash = gerar_dashboard_gpu()
    assert dash["tipo"] == "benchmark_gpu"
    assert dash["produto"]["id"] == "GPU-01"
    assert dash["produto"]["estoque"] == 3
    assert len(dash["benchmarks_jogos"]) >= 3
    assert any(j["fps"] > 100 for j in dash["benchmarks_jogos"])


def test_gerar_dashboard_perifericos():
    """Valida o dashboard comparativo de periféricos."""
    dash = gerar_dashboard_perifericos()
    assert dash["tipo"] == "comparativo_perifericos"
    assert len(dash["produtos"]) == 2
    assert any("Logitech" in p["nome"] for p in dash["produtos"])
    assert any("Keychron" in p["nome"] for p in dash["produtos"])


def test_obter_dashboard_benchmarks_por_intencao():
    """Valida a detecção automática de dashboard via intenção do usuário."""
    dash_nb = obter_dashboard_benchmarks("Gostaria de ver o comparativo de notebooks")
    assert dash_nb is not None
    assert dash_nb["tipo"] == "comparativo_notebooks"

    dash_gpu = obter_dashboard_benchmarks("Qual o desempenho e benchmark da RTX 4060?")
    assert dash_gpu is not None
    assert dash_gpu["tipo"] == "benchmark_gpu"

    dash_none = obter_dashboard_benchmarks("Olá, tudo bem?")
    assert dash_none is None
