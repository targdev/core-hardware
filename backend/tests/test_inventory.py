"""Testes unitários para o módulo de inventário e busca de estoque."""

import pytest
from app.inventory import (
    CATALOGO_PRODUTOS,
    consultar_estoque,
    listar_produtos,
)


def test_cenario_a_produto_existente_em_estoque():
    """Cenário A: Consulta por termo exato ou parcial deve retornar disponível e quantidade > 0."""
    # Teste 1: Termo parcial "MacBook"
    res_mac = consultar_estoque("MacBook")
    assert res_mac["encontrado"] is True
    assert res_mac["status"] == "disponivel"
    assert res_mac["estoque"] > 0
    assert res_mac["stock"] > 0
    assert "M3" in res_mac["nome"]
    assert res_mac["preco"] == 11999.00

    # Teste 2: Termo parcial "MX Master 3S"
    res_mouse = consultar_estoque("MX Master 3S")
    assert res_mouse["encontrado"] is True
    assert res_mouse["status"] == "disponivel"
    assert res_mouse["estoque"] == 11
    assert res_mouse["stock"] == 11
    assert "Logitech" in res_mouse["nome"]

    # Teste 3: Termo "Keychron"
    res_teclado = consultar_estoque("Keychron")
    assert res_teclado["encontrado"] is True
    assert res_teclado["estoque"] == 6


def test_cenario_b_produto_esgotado():
    """Cenário B: Consulta por 'Legion Pro 5' deve retornar estoque zero e status esgotado."""
    res_legion = consultar_estoque("Legion Pro 5")
    assert res_legion["encontrado"] is True
    assert res_legion["estoque"] == 0
    assert res_legion["stock"] == 0
    assert res_legion["status"] == "esgotado"
    assert "Lenovo Legion Pro 5" in res_legion["nome"]


def test_cenario_c_produto_inexistente():
    """Cenário C: Consulta por item inexistente deve retornar indicador de não encontrado sem exceção."""
    res_ps5 = consultar_estoque("PlayStation 5")
    assert res_ps5["encontrado"] is False
    assert res_ps5["total_encontrados"] == 0
    assert len(res_ps5["produtos"]) == 0
    assert "mensagem" in res_ps5

    # Consulta com string vazia ou caracteres aleatórios
    res_vazio = consultar_estoque("")
    assert res_vazio["encontrado"] is False
    assert res_vazio["total_encontrados"] == 0


def test_listar_produtos_todas_e_por_categoria():
    """Valida listagem de produtos com e sem filtro de categoria."""
    todos = listar_produtos()
    assert len(todos) == len(CATALOGO_PRODUTOS)
    assert len(todos) == 7

    notebooks = listar_produtos("Notebooks")
    assert len(notebooks) == 3
    assert all(p["categoria"] == "Notebooks" for p in notebooks)

    perifericos = listar_produtos("periféricos")
    assert len(perifericos) == 2

    categoria_inexistente = listar_produtos("Smartphones")
    assert len(categoria_inexistente) == 0
