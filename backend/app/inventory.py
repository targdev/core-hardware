"""Módulo de Catálogo e Inventário da CORE Hardware.

Responsável por armazenar o inventário oficial de produtos e expor
ferramentas de consulta de estoque e listagem de produtos.
"""

from typing import Any, Dict, List, Optional
import unicodedata

# Catálogo oficial de produtos de alta performance
CATALOGO_PRODUTOS: List[Dict[str, Any]] = [
    {
        "id": "NOTE-01",
        "nome": "MacBook Air 15\" M3",
        "categoria": "Notebooks",
        "especificacoes": "Chip Apple M3, 16GB RAM, 512GB SSD, Cinza-espacial",
        "preco": 11999.00,
        "estoque": 4,
    },
    {
        "id": "NOTE-02",
        "nome": "Dell XPS 13 Plus",
        "categoria": "Notebooks",
        "especificacoes": "Intel Core i7 13ª Ger, 32GB RAM, 1TB SSD, Tela 3.5K OLED",
        "preco": 10850.00,
        "estoque": 2,
    },
    {
        "id": "NOTE-03",
        "nome": "Lenovo Legion Pro 5",
        "categoria": "Notebooks",
        "especificacoes": "AMD Ryzen 7 7745HX, RTX 4070 8GB, 32GB RAM, 1TB SSD",
        "preco": 9400.00,
        "estoque": 0,
    },
    {
        "id": "PERIF-01",
        "nome": "Mouse Logitech MX Master 3S",
        "categoria": "Periféricos",
        "especificacoes": "Sensor 8K DPI, Conexão Bluetooth/Logi Bolt, Grafite",
        "preco": 650.00,
        "estoque": 11,
    },
    {
        "id": "PERIF-02",
        "nome": "Teclado Keychron K2 Pro",
        "categoria": "Periféricos",
        "especificacoes": "Switch Red, Layout 75%, Hot-swappable, Conexão Sem Fio",
        "preco": 780.00,
        "estoque": 6,
    },
    {
        "id": "MON-01",
        "nome": "Monitor Dell UltraSharp 27\" 4K",
        "categoria": "Monitores",
        "especificacoes": "Painel IPS Black (U2723QE), 4K UHD, Hub USB-C 90W",
        "preco": 3790.00,
        "estoque": 5,
    },
    {
        "id": "GPU-01",
        "nome": "Nvidia GeForce RTX 4060 Ti 8GB",
        "categoria": "Hardware",
        "especificacoes": "8GB GDDR6, Dual Fan, Ray Tracing, DLSS 3",
        "preco": 2650.00,
        "estoque": 3,
    },
]


def _normalizar_texto(texto: str) -> str:
    """Remove acentos e converte para minúsculas para busca resiliente."""
    if not texto:
        return ""
    texto_norm = unicodedata.normalize("NFKD", texto)
    sem_acentos = "".join(c for c in texto_norm if not unicodedata.combining(c))
    return sem_acentos.lower().strip()


def consultar_estoque(nome_ou_termo: str) -> Dict[str, Any]:
    """Consulta o estoque de um produto por nome, ID ou termo de busca.

    Retorna se o item existe, a quantidade exata em estoque, o preço e as
    especificações técnicas.
    """
    if not nome_ou_termo or not isinstance(nome_ou_termo, str):
        return {
            "encontrado": False,
            "total_encontrados": 0,
            "produtos": [],
            "mensagem": "Termo de busca inválido ou não informado.",
        }

    termo_norm = _normalizar_texto(nome_ou_termo)
    palavras_termo = termo_norm.split()

    resultados: List[Dict[str, Any]] = []

    for item in CATALOGO_PRODUTOS:
        nome_norm = _normalizar_texto(item["nome"])
        id_norm = _normalizar_texto(item["id"])
        categoria_norm = _normalizar_texto(item["categoria"])
        specs_norm = _normalizar_texto(item["especificacoes"])

        # 1. Match direto de substring no nome, ID ou specs
        match_direto = (
            termo_norm in nome_norm
            or termo_norm in id_norm
            or termo_norm in specs_norm
            or termo_norm in categoria_norm
        )

        # 2. Match onde todas as palavras do termo estão presentes no nome ou specs
        match_palavras = False
        if not match_direto and len(palavras_termo) > 1:
            texto_completo = f"{nome_norm} {specs_norm} {categoria_norm}"
            match_palavras = all(p in texto_completo for p in palavras_termo)

        if match_direto or match_palavras:
            item_formatado = {
                **item,
                "status": "disponivel" if item["estoque"] > 0 else "esgotado",
                "stock": item["estoque"],
            }
            resultados.append(item_formatado)

    if not resultados:
        return {
            "encontrado": False,
            "total_encontrados": 0,
            "produtos": [],
            "mensagem": f"Nenhum produto correspondente a '{nome_ou_termo}' foi encontrado no estoque.",
        }

    # Se for apenas 1 produto encontrado, retorna dados consolidados e a lista
    if len(resultados) == 1:
        prod = resultados[0]
        return {
            "encontrado": True,
            "total_encontrados": 1,
            "id": prod["id"],
            "nome": prod["nome"],
            "categoria": prod["categoria"],
            "especificacoes": prod["especificacoes"],
            "preco": prod["preco"],
            "estoque": prod["estoque"],
            "stock": prod["estoque"],
            "status": prod["status"],
            "produtos": resultados,
        }

    return {
        "encontrado": True,
        "total_encontrados": len(resultados),
        "produtos": resultados,
        "status": "multiplos_encontrados",
    }


def listar_produtos(categoria: Optional[str] = None) -> List[Dict[str, Any]]:
    """Lista os produtos disponíveis no catálogo.

    Se uma categoria for fornecida, filtra os produtos por ela.
    Caso contrário, retorna todo o catálogo.
    """
    lista_formatada = [
        {
            **item,
            "status": "disponivel" if item["estoque"] > 0 else "esgotado",
            "stock": item["estoque"],
        }
        for item in CATALOGO_PRODUTOS
    ]

    if not categoria or categoria.strip().lower() in ("todas", "todos", "all"):
        return lista_formatada

    cat_norm = _normalizar_texto(categoria)
    return [
        item
        for item in lista_formatada
        if cat_norm in _normalizar_texto(item["categoria"])
    ]
