"""Módulo de Benchmarks e Mini Dashboards Comparativos da CORE Hardware.

Fornece dados de telemetria, métricas de desempenho e comparações pré-montadas
integradas em tempo real com o estoque da loja.
"""

from typing import Any, Dict, List, Optional
from app.inventory import consultar_estoque

DADOS_BENCHMARKS: Dict[str, Any] = {
    "NOTE-01": {
        "id": "NOTE-01",
        "nome": "MacBook Air 15\" M3",
        "badge": "🏆 Campeão em Bateria & Silêncio",
        "destaque": "Melhor Eficiência Térmica (Sem Ventoinha)",
        "scores": {
            "CPU Single-Core": 96,
            "CPU Multi-Core": 88,
            "GPU / Gráficos": 74,
            "Bateria (até 18h)": 98,
            "Portabilidade": 95,
        },
        "metricas_adicionais": {
            "Autonomia": "Até 18 horas",
            "Peso": "1.51 kg",
            "Ruído Operacional": "0 dB (Fanless)",
            "Perfil Ideal": "Produtividade, Programação, Criação de Conteúdo, Mobilidade",
        },
    },
    "NOTE-02": {
        "id": "NOTE-02",
        "nome": "Dell XPS 13 Plus",
        "badge": "💎 Melhor Display OLED 3.5K",
        "destaque": "Design Futurista com Barra de Função Touch",
        "scores": {
            "CPU Single-Core": 85,
            "CPU Multi-Core": 89,
            "GPU / Gráficos": 68,
            "Bateria (até 10h)": 78,
            "Portabilidade": 96,
        },
        "metricas_adicionais": {
            "Autonomia": "Até 10 horas",
            "Peso": "1.26 kg",
            "Tela": "OLED 3.5K Touchscreen",
            "Perfil Ideal": "Executivos, Desenvolvimento Web, Consumo Multimídia Premium",
        },
    },
    "NOTE-03": {
        "id": "NOTE-03",
        "nome": "Lenovo Legion Pro 5",
        "badge": "⚡ Campeão de FPS & Render 3D",
        "destaque": "RTX 4070 8GB + Ryzen 7 de Alta Potência",
        "scores": {
            "CPU Single-Core": 88,
            "CPU Multi-Core": 95,
            "GPU / Gráficos": 93,
            "Bateria (até 4h)": 50,
            "Portabilidade": 62,
        },
        "metricas_adicionais": {
            "Autonomia": "Até 4 horas",
            "Peso": "2.50 kg",
            "FPS Médio (1440p Ultra)": "85-110 FPS",
            "Perfil Ideal": "Jogos Competitivos, Renderização Blender/Unreal, IA Local",
        },
    },
    "GPU-01": {
        "id": "GPU-01",
        "nome": "Nvidia GeForce RTX 4060 Ti 8GB",
        "badge": "🚀 Campeã de Custo-Benefício 1080p/1440p",
        "destaque": "Arquitetura Ada Lovelace com DLSS 3 Frame Gen",
        "scores": {
            "Rasterização 1080p": 92,
            "Rasterização 1440p": 82,
            "Ray Tracing": 80,
            "DLSS 3 Frame Gen": 96,
            "Eficiência Térmica / TDP": 91,
        },
        "metricas_adicionais": {
            "Consumo Médio (TDP)": "160 Watts",
            "FPS Médio Cyberpunk (1080p RT Ultra + DLSS3)": "104 FPS",
            "FPS Médio Warzone 2 (1440p High)": "115 FPS",
            "Fonte Recomendada": "550W a 650W",
        },
    },
    "PERIF-01": {
        "id": "PERIF-01",
        "nome": "Mouse Logitech MX Master 3S",
        "badge": "👑 Padrão Ouro em Ergonomia de Escritório",
        "destaque": "Roda MagSpeed Eletromagnética e Cliques Silenciosos",
        "scores": {
            "Ergonomia": 98,
            "Precisão / Sensor 8K": 94,
            "Bateria (até 70 dias)": 97,
            "Software / Produtividade": 95,
            "Silêncio dos Cliques": 96,
        },
        "metricas_adicionais": {
            "Autonomia": "Até 70 dias com 1 carga",
            "Conexão": "Bluetooth + Receptor Logi Bolt (até 3 PCs)",
            "Resolução Máxima": "8.000 DPI (funciona em vidro)",
            "Perfil Ideal": "Programadores, Editores de Vídeo, Finanças",
        },
    },
    "PERIF-02": {
        "id": "PERIF-02",
        "nome": "Teclado Keychron K2 Pro",
        "badge": "⌨️ Melhor Teclado Mecânico Custom Wireless",
        "destaque": "Hot-swappable com Suporte QMK/VIA e Keycaps PBT",
        "scores": {
            "Sensação Tátil (Switch Red)": 94,
            "Customização (QMK/VIA)": 98,
            "Construção / Chassi": 92,
            "Bateria (até 300h sem RGB)": 90,
            "Compatibilidade Mac/Windows": 99,
        },
        "metricas_adicionais": {
            "Layout": "75% compacto (84 teclas)",
            "Switches": "Keychron K Pro Red lubrificados de fábrica",
            "Conexão": "Bluetooth 5.1 + Cabo USB-C",
            "Perfil Ideal": "Desenvolvedores, Escritores e Entusiastas de Teclados Mecânicos",
        },
    },
    "MON-01": {
        "id": "MON-01",
        "nome": "Monitor Dell UltraSharp 27\" 4K",
        "badge": "🎨 Referência Absoluta em Fidelidade de Cores",
        "destaque": "Painel IPS Black com Contraste 2000:1 e Hub USB-C 90W",
        "scores": {
            "Fidelidade de Cores": 98,
            "Contraste IPS Black": 92,
            "Nitidez 4K UHD": 96,
            "Conectividade USB-C Hub": 97,
            "Ergonomia e Ajustes": 95,
        },
        "metricas_adicionais": {
            "Gama de Cores": "100% sRGB e 98% DCI-P3",
            "Alimentação USB-C": "Carrega o notebook com até 90W",
            "Ajustes de Suporte": "Altura, inclinação, rotação e pivô (90°)",
            "Perfil Ideal": "Designers Gráficos, Fotógrafos, Editores e Setups Clean",
        },
    },
}


def gerar_dashboard_comparativo_notebooks() -> Dict[str, Any]:
    """Gera o mini dashboard comparando os 3 notebooks do catálogo da CORE Hardware."""
    itens_ids = ["NOTE-01", "NOTE-02", "NOTE-03"]
    produtos_comparados = []

    for item_id in itens_ids:
        estoque_info = consultar_estoque(item_id)
        bench = DADOS_BENCHMARKS.get(item_id, {})
        produtos_comparados.append(
            {
                "id": item_id,
                "nome": estoque_info.get("nome", bench.get("nome")),
                "preco": estoque_info.get("preco"),
                "estoque": estoque_info.get("estoque"),
                "status": estoque_info.get("status"),
                "badge": bench.get("badge"),
                "destaque": bench.get("destaque"),
                "scores": bench.get("scores", {}),
                "metricas": bench.get("metricas_adicionais", {}),
            }
        )

    return {
        "tipo": "comparativo_notebooks",
        "titulo": "Dashboard Comparativo: Notebooks de Alta Performance",
        "subtitulo": "Análise técnica de benchmarks, eficiência térmica e perfil de uso",
        "categorias_avaliacao": [
            "CPU Single-Core",
            "CPU Multi-Core",
            "GPU / Gráficos",
            "Bateria & Eficiência",
            "Portabilidade",
        ],
        "produtos": produtos_comparados,
        "veredito": (
            "• **MacBook Air M3**: Vencedor absoluto para mobilidade, autonomia e trabalho sem ruído.\n"
            "• **Dell XPS 13 Plus**: Melhor fidelidade visual para quem exige tela OLED 3.5K e peso pluma.\n"
            "• **Lenovo Legion Pro 5**: Campeão em poder bruto e FPS para jogos e IA (atualmente esgotado)."
        ),
    }


def gerar_dashboard_gpu() -> Dict[str, Any]:
    """Gera o mini dashboard de desempenho da GPU RTX 4060 Ti."""
    item_id = "GPU-01"
    estoque_info = consultar_estoque(item_id)
    bench = DADOS_BENCHMARKS.get(item_id, {})

    return {
        "tipo": "benchmark_gpu",
        "titulo": "Dashboard de Telemetria: Nvidia RTX 4060 Ti 8GB",
        "subtitulo": "Desempenho em 1080p/1440p, Ray Tracing e consumo térmico",
        "produto": {
            "id": item_id,
            "nome": estoque_info.get("nome", bench.get("nome")),
            "preco": estoque_info.get("preco"),
            "estoque": estoque_info.get("estoque"),
            "status": estoque_info.get("status"),
            "badge": bench.get("badge"),
            "destaque": bench.get("destaque"),
            "scores": bench.get("scores", {}),
            "metricas": bench.get("metricas_adicionais", {}),
        },
        "benchmarks_jogos": [
            {"jogo": "Cyberpunk 2077 (1080p Ultra RT + DLSS 3)", "fps": 104, "status": "Excelente"},
            {"jogo": "Warzone 2 / MW3 (1440p High)", "fps": 115, "status": "Competitivo"},
            {"jogo": "Forza Horizon 5 (1440p Maxed Out)", "fps": 98, "status": "Excelente"},
            {"jogo": "Red Dead Redemption 2 (1440p Ultra)", "fps": 76, "status": "Muito Fluido"},
        ],
        "veredito": (
            "A RTX 4060 Ti é ideal para jogadores que buscam mais de 100 FPS em 1080p e 1440p com consumo baixíssimo de 160W "
            "e tecnologia DLSS 3 Frame Generation ativa."
        ),
    }


def gerar_dashboard_perifericos() -> Dict[str, Any]:
    """Gera o mini dashboard comparando o mouse MX Master 3S e o teclado Keychron K2 Pro."""
    itens_ids = ["PERIF-01", "PERIF-02"]
    produtos = []
    for item_id in itens_ids:
        estoque_info = consultar_estoque(item_id)
        bench = DADOS_BENCHMARKS.get(item_id, {})
        produtos.append(
            {
                "id": item_id,
                "nome": estoque_info.get("nome", bench.get("nome")),
                "preco": estoque_info.get("preco"),
                "estoque": estoque_info.get("estoque"),
                "status": estoque_info.get("status"),
                "badge": bench.get("badge"),
                "destaque": bench.get("destaque"),
                "scores": bench.get("scores", {}),
                "metricas": bench.get("metricas_adicionais", {}),
            }
        )

    return {
        "tipo": "comparativo_perifericos",
        "titulo": "Dashboard de Periféricos de Elite: Setup Master Pro",
        "subtitulo": "A combinação definitiva de ergonomia e digitação mecânica de alta precisão",
        "produtos": produtos,
        "veredito": (
            "O combo **Logitech MX Master 3S + Keychron K2 Pro** forma o ecossistema ideal para desenvolvedores "
            "e profissionais que passam mais de 8 horas diárias no computador, aliando ergonomia silenciosa com sensação tátil premium."
        ),
    }


def gerar_dashboard_monitor() -> Dict[str, Any]:
    """Gera o mini dashboard analítico do Monitor Dell UltraSharp 27 4K."""
    item_id = "MON-01"
    estoque_info = consultar_estoque(item_id)
    bench = DADOS_BENCHMARKS.get(item_id, {})

    return {
        "tipo": "analise_monitor",
        "titulo": "Dashboard Visual: Monitor Dell UltraSharp 27\" 4K (U2723QE)",
        "subtitulo": "Painel IPS Black com contraste duplo e Hub USB-C de 90W",
        "produto": {
            "id": item_id,
            "nome": estoque_info.get("nome", bench.get("nome")),
            "preco": estoque_info.get("preco"),
            "estoque": estoque_info.get("estoque"),
            "status": estoque_info.get("status"),
            "badge": bench.get("badge"),
            "destaque": bench.get("destaque"),
            "scores": bench.get("scores", {}),
            "metricas": bench.get("metricas_adicionais", {}),
        },
        "veredito": (
            "Com certificação 98% DCI-P3 e painel IPS Black, é o monitor ideal para designers, editores de cor "
            "e profissionais que utilizam MacBook ou notebook com USB-C Hub de 90W em um único cabo."
        ),
    }


def obter_dashboard_benchmarks(mensagem_ou_termo: str) -> Optional[Dict[str, Any]]:
    """Identifica se a mensagem solicita um comparativo ou benchmark e retorna o dashboard pré-montado."""
    texto = mensagem_ou_termo.lower()

    # Intenções de comparação de notebooks ou hardware geral
    gatilhos_notebooks = [
        "comparar", "comparativo", "comparacao", "comparação", "versus", "vs",
        "qual melhor", "qual o melhor", "notebooks", "macbook vs", "xps vs", "legion vs",
        "dashboard de comparacao", "dashboard de comparação", "desempenho dos notebooks", "benchmarks notebooks"
    ]
    if any(g in texto for g in gatilhos_notebooks) and ("notebook" in texto or "macbook" in texto or "xps" in texto or "legion" in texto or "qual" in texto or "comparar" in texto):
        return gerar_dashboard_comparativo_notebooks()

    # Intenções de GPU / RTX / Placa de vídeo
    gatilhos_gpu = ["rtx", "4060", "gpu", "placa de video", "placa de vídeo", "benchmark gpu", "fps", "cyberpunk", "jogos"]
    if any(g in texto for g in gatilhos_gpu):
        return gerar_dashboard_gpu()

    # Intenções de Periféricos / Mouse / Teclado
    gatilhos_perifs = ["mouse", "teclado", "periferico", "periférico", "keychron", "mx master", "logitech vs"]
    if any(g in texto for g in gatilhos_perifs):
        return gerar_dashboard_perifericos()

    # Intenções de Monitor
    gatilhos_monitor = ["monitor", "ultrasharp", "4k", "ips black", "u2723qe", "display"]
    if any(g in texto for g in gatilhos_monitor):
        return gerar_dashboard_monitor()

    # Gatilhos genéricos de dashboard / benchmark
    if "dashboard" in texto or "benchmark" in texto or "desempenho" in texto:
        return gerar_dashboard_comparativo_notebooks()

    return None
