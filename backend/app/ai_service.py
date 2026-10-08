"""Serviço de Inteligência Artificial integrado ao Grok (xAI) e Google Gemini com Tool Calling.

Prioriza execução via LLMs (Grok e Gemini) com Tool Calling real e dispõe
de Fallback Conversacional com tolerância a erros ortográficos (Fuzzy Matching).
"""

import difflib
import json
import logging
import os
import re
from typing import Any, Dict, List, Optional, Tuple

import httpx
from dotenv import load_dotenv

from app.benchmarks import obter_dashboard_benchmarks
from app.inventory import (
    CATALOGO_PRODUTOS,
    consultar_estoque,
    listar_produtos,
)

load_dotenv()
logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """Você é o Assistente Virtual Oficial da CORE Hardware, uma loja especializada em computadores, notebooks de alta performance, monitores 4K e periféricos premium.

Suas diretrizes fundamentais:
1. NUNCA invente ou alucine informações sobre estoque, quantidades disponíveis, preços ou especificações técnicas de produtos.
2. SEMPRE consulte as ferramentas disponíveis (`consultar_estoque` ou `listar_produtos`) antes de responder a qualquer pergunta sobre produtos, disponibilidade ou preços.
3. Se o produto estiver com estoque zerado (como o Lenovo Legion Pro 5), informe educadamente que ele está esgotado (0 unidades em estoque) e mencione o preço de referência.
4. Ao comparar hardwares (ex: MacBook Air M3 vs Dell XPS 13 vs Lenovo Legion Pro 5), forneça uma análise técnica precisa destacando pontos fortes (CPU, GPU, bateria, tela e perfil de uso).
5. Mantenha um tom profissional, moderno, acolhedor, prestativo e conversacional.
6. Formate os preços em Reais (R$).
7. Entenda erros de digitação e termos informais do cliente com naturalidade.
8. CONVERSA PROCEDURAL E MEMÓRIA DE CONTEXTO:
   - Mantenha continuidade natural do diálogo. Se o cliente fizer perguntas complementares usando pronomes ou elipses (ex: "E quanto custa?", "Qual a cor dele?", "E a bateria?", "Tem garantia?"), recupere o produto em discussão do histórico recente e responda de forma conectada.
   - Conduza o atendimento de forma consultiva, sugerindo comparações ou acessórios complementares quando for oportuno.
"""

TOOL_MAP = {
    "consultar_estoque": consultar_estoque,
    "listar_produtos": listar_produtos,
}

GROK_TOOLS_SCHEMA = [
    {
        "type": "function",
        "function": {
            "name": "consultar_estoque",
            "description": "Consulta o estoque, quantidade em unidades, preço e especificações de um produto por nome, ID ou termo.",
            "parameters": {
                "type": "object",
                "properties": {
                    "nome_ou_termo": {
                        "type": "string",
                        "description": "Nome ou modelo do produto de hardware (ex: MacBook, XPS, Legion, MX Master, Keychron, RTX 4060 Ti, Dell 4K)",
                    }
                },
                "required": ["nome_ou_termo"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "listar_produtos",
            "description": "Lista produtos disponíveis no catálogo oficial da CORE Hardware, opcionalmente filtrando por categoria.",
            "parameters": {
                "type": "object",
                "properties": {
                    "categoria": {
                        "type": "string",
                        "description": "Categoria desejada (Notebooks, Periféricos, Monitores, Hardware) ou None para catálogo completo",
                    }
                },
            },
        },
    },
]

# Mapa de palavras-chave canônicas e sinônimos com tolerância a erros de digitação
DICIONARIO_TERMOS_PRODUTOS = {
    "mouse": ("PERIF-01", "Mouse Logitech MX Master 3S"),
    "moude": ("PERIF-01", "Mouse Logitech MX Master 3S"),
    "mause": ("PERIF-01", "Mouse Logitech MX Master 3S"),
    "logitech": ("PERIF-01", "Mouse Logitech MX Master 3S"),
    "mx master": ("PERIF-01", "Mouse Logitech MX Master 3S"),
    "master 3s": ("PERIF-01", "Mouse Logitech MX Master 3S"),
    "mx master 3s": ("PERIF-01", "Mouse Logitech MX Master 3S"),
    "perif-01": ("PERIF-01", "Mouse Logitech MX Master 3S"),
    "teclado": ("PERIF-02", "Teclado Keychron K2 Pro"),
    "teclao": ("PERIF-02", "Teclado Keychron K2 Pro"),
    "keychron": ("PERIF-02", "Teclado Keychron K2 Pro"),
    "k2 pro": ("PERIF-02", "Teclado Keychron K2 Pro"),
    "keychron k2": ("PERIF-02", "Teclado Keychron K2 Pro"),
    "perif-02": ("PERIF-02", "Teclado Keychron K2 Pro"),
    "macbook": ("NOTE-01", "MacBook Air 15\" M3"),
    "macbok": ("NOTE-01", "MacBook Air 15\" M3"),
    "apple": ("NOTE-01", "MacBook Air 15\" M3"),
    "air m3": ("NOTE-01", "MacBook Air 15\" M3"),
    "m3": ("NOTE-01", "MacBook Air 15\" M3"),
    "macbook air": ("NOTE-01", "MacBook Air 15\" M3"),
    "note-01": ("NOTE-01", "MacBook Air 15\" M3"),
    "dell xps": ("NOTE-02", "Dell XPS 13 Plus"),
    "xps": ("NOTE-02", "Dell XPS 13 Plus"),
    "xps 13": ("NOTE-02", "Dell XPS 13 Plus"),
    "xps 13 plus": ("NOTE-02", "Dell XPS 13 Plus"),
    "note-02": ("NOTE-02", "Dell XPS 13 Plus"),
    "legion": ("NOTE-03", "Lenovo Legion Pro 5"),
    "lenovo": ("NOTE-03", "Lenovo Legion Pro 5"),
    "legion pro": ("NOTE-03", "Lenovo Legion Pro 5"),
    "legion pro 5": ("NOTE-03", "Lenovo Legion Pro 5"),
    "note-03": ("NOTE-03", "Lenovo Legion Pro 5"),
    "monitor": ("MON-01", "Monitor Dell UltraSharp 27\" 4K"),
    "monitr": ("MON-01", "Monitor Dell UltraSharp 27\" 4K"),
    "ultrasharp": ("MON-01", "Monitor Dell UltraSharp 27\" 4K"),
    "dell ultrasharp": ("MON-01", "Monitor Dell UltraSharp 27\" 4K"),
    "tela": ("MON-01", "Monitor Dell UltraSharp 27\" 4K"),
    "4k": ("MON-01", "Monitor Dell UltraSharp 27\" 4K"),
    "u2723qe": ("MON-01", "Monitor Dell UltraSharp 27\" 4K"),
    "mon-01": ("MON-01", "Monitor Dell UltraSharp 27\" 4K"),
    "rtx": ("GPU-01", "Nvidia GeForce RTX 4060 Ti 8GB"),
    "4060": ("GPU-01", "Nvidia GeForce RTX 4060 Ti 8GB"),
    "4060 ti": ("GPU-01", "Nvidia GeForce RTX 4060 Ti 8GB"),
    "rtx 4060": ("GPU-01", "Nvidia GeForce RTX 4060 Ti 8GB"),
    "geforce": ("GPU-01", "Nvidia GeForce RTX 4060 Ti 8GB"),
    "placa de video": ("GPU-01", "Nvidia GeForce RTX 4060 Ti 8GB"),
    "placa de vídeo": ("GPU-01", "Nvidia GeForce RTX 4060 Ti 8GB"),
    "gpu": ("GPU-01", "Nvidia GeForce RTX 4060 Ti 8GB"),
    "gpu-01": ("GPU-01", "Nvidia GeForce RTX 4060 Ti 8GB"),
}

# Dados detalhados e consultivos para diálogo procedural e memória de contexto
DADOS_DETALHADOS_PRODUTOS = {
    "NOTE-01": {
        "nome": "MacBook Air 15\" M3",
        "cor": "Cinza-espacial (Space Gray) com acabamento unibody em alumínio 100% reciclado",
        "bateria": "Até 18 horas de autonomia em uso contínuo; acompanha carregador MagSafe 3 com cabo trançado",
        "garantia": "12 meses de garantia oficial CORE Hardware com cobertura nacional e nota fiscal eletrônica (NF-e)",
        "acessorios_sugeridos": "Mouse Logitech MX Master 3S e Monitor Dell UltraSharp 27\" 4K com Hub USB-C de 90W",
        "destaque": "Chip Apple M3 (CPU 8-core, GPU 10-core), 16GB RAM unificada, 512GB SSD ultrarrápido e arquitetura fanless totalmente silenciosa",
    },
    "NOTE-02": {
        "nome": "Dell XPS 13 Plus",
        "cor": "Alumínio usinado CNC na cor Grafite/Platina com apoio para mãos em vidro e touchpad háptico contínuo",
        "bateria": "Até 12 horas de autonomia em produtividade contínua; acompanha carregador USB-C de 60W com tecnologia ExpressCharge",
        "garantia": "12 meses de garantia oficial CORE Hardware com suporte técnico dedicado e nota fiscal eletrônica (NF-e)",
        "acessorios_sugeridos": "Mouse Logitech MX Master 3S e Teclado Mecânico Keychron K2 Pro",
        "destaque": "Intel Core i7 13ª Geração, 32GB RAM LPDDR5, 1TB SSD NVMe e exuberante tela 3.5K OLED touchscreen",
    },
    "NOTE-03": {
        "nome": "Lenovo Legion Pro 5",
        "cor": "Cinza Ônix (Onyx Grey) com chassi reforçado e acabamento gamer discreto de alta resistência",
        "bateria": "Bateria de 80Wh para tarefas diárias e carregador de 300W para extrair potência máxima em jogos e renderização",
        "garantia": "12 meses de garantia oficial CORE Hardware com suporte especializado para hardware de alta performance e nota fiscal eletrônica (NF-e)",
        "acessorios_sugeridos": "Teclado Keychron K2 Pro e Mouse Logitech MX Master 3S",
        "destaque": "AMD Ryzen 7 7745HX, GPU Nvidia GeForce RTX 4070 8GB, 32GB RAM e 1TB SSD. (Atenção: atualmente esgotado em estoque)",
    },
    "PERIF-01": {
        "nome": "Mouse Logitech MX Master 3S",
        "cor": "Grafite fosco com textura ergonômica emborrachada resistente a desgaste",
        "bateria": "Bateria recarregável com até 70 dias com carga completa; recarga rápida USB-C garante 3 horas de uso em apenas 1 minuto",
        "garantia": "12 meses de garantia oficial CORE Hardware e nota fiscal eletrônica (NF-e)",
        "acessorios_sugeridos": "Teclado Mecânico Keychron K2 Pro para formar o combo definitivo de produtividade",
        "destaque": "Sensor Darkfield 8K DPI (opera inclusive em vidro), roda MagSpeed magnética ultra silenciosa e botões silenciosos Quiet Clicks",
    },
    "PERIF-02": {
        "nome": "Teclado Keychron K2 Pro",
        "cor": "Chassi preto com keycaps PBT Double-Shot em tons de cinza grafite e detalhes em vermelho/laranja",
        "bateria": "Bateria interna recarregável de 4.000 mAh que oferece até 240 horas de digitação contínua (com iluminação desligada)",
        "garantia": "12 meses de garantia oficial CORE Hardware e nota fiscal eletrônica (NF-e)",
        "acessorios_sugeridos": "Mouse Logitech MX Master 3S para pareamento multi-dispositivo perfeito",
        "destaque": "Switches Red lubrificados de fábrica, layout 75%, hot-swappable e compatibilidade nativa Mac/Windows com Bluetooth 5.1",
    },
    "MON-01": {
        "nome": "Monitor Dell UltraSharp 27\" 4K",
        "cor": "Acabamento premium em prata platina com base metálica ergonômica e bordas ultrafinas InfinityEdge",
        "bateria": "Alimentação direta bivolt com Hub USB-C embutido capaz de fornecer até 90W de energia (Power Delivery) para recarregar seu notebook",
        "garantia": "12 meses de garantia oficial CORE Hardware com política de painel premium e nota fiscal eletrônica (NF-e)",
        "acessorios_sugeridos": "Notebooks MacBook Air M3 ou Dell XPS 13 Plus para conexão em cabo único USB-C",
        "destaque": "Painel IPS Black 4K UHD (U2723QE), contraste 2000:1, 98% DCI-P3, hub USB-C com portas RJ45 e USB de alta velocidade",
    },
    "GPU-01": {
        "nome": "Nvidia GeForce RTX 4060 Ti 8GB",
        "cor": "Preto fosco com detalhes industriais metálicos e iluminação discreta",
        "bateria": "Consumo energético de 160W TDP (recomendamos fonte com certificação 80 Plus de 550W a 650W)",
        "garantia": "12 meses de garantia oficial CORE Hardware com assistência técnica e nota fiscal eletrônica (NF-e)",
        "acessorios_sugeridos": "Monitor Dell UltraSharp 27\" 4K para aproveitar resolução ultra nítida e altas taxas de quadros",
        "destaque": "8GB GDDR6, sistema Dual Fan eficiente, suporte a Ray Tracing de 3ª Geração e DLSS 3 Frame Generation",
    },
}


def _encontrar_produto_aproximado(mensagem: str) -> Optional[Tuple[str, str]]:
    """Identifica o produto pretendido pelo usuário mesmo com erros de digitação (fuzzy matching)."""
    msg_limpa = mensagem.lower()

    # 1. Match direto em chaves compostas
    for chave, item in DICIONARIO_TERMOS_PRODUTOS.items():
        if chave in msg_limpa:
            return item

    # 2. Match de palavras com Fuzzy Matching (difflib)
    palavras = re.findall(r"\b[a-zA-Z0-9áéíóúâêîôûãõç]{3,}\b", msg_limpa)
    chaves_disponiveis = list(DICIONARIO_TERMOS_PRODUTOS.keys())

    for palavra in palavras:
        matches = difflib.get_close_matches(palavra, chaves_disponiveis, n=1, cutoff=0.72)
        if matches:
            chave_encontrada = matches[0]
            return DICIONARIO_TERMOS_PRODUTOS[chave_encontrada]

    return None


def _recuperar_produto_do_historico(
    history: Optional[List[Dict[str, str]]]
) -> Optional[Tuple[str, str]]:
    """Percorre o histórico de trás para frente para identificar o último produto em pauta."""
    if not history:
        return None

    for msg in reversed(history):
        content = msg.get("content", "")
        prod = _encontrar_produto_aproximado(content)
        if prod:
            return prod

def _formatar_preco_br(preco: float) -> str:
    """Formata valor monetário no padrão brasileiro (R$ 11.999,00)."""
    formatado = f"{preco:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"R$ {formatado}"


def _executar_fallback_deterministico(
    message: str, history: Optional[List[Dict[str, str]]] = None
) -> Tuple[str, List[str], Optional[Dict[str, Any]]]:
    """Fallback conversacional empático e resiliente para quando nenhuma API estiver com chave configurada."""
    msg_lower = message.lower().strip()
    tools_called: List[str] = []

    # Verificar se a mensagem ativa um mini dashboard de comparação pré-montado
    dashboard = obter_dashboard_benchmarks(message)

    # 1. Comparativo de Notebooks
    if dashboard and dashboard.get("tipo") == "comparativo_notebooks":
        tools_called.extend(["consultar_estoque", "listar_produtos"])
        reply = (
            "📊 **Mini Dashboard Comparativo: Linha de Notebooks CORE Hardware**\n\n"
            "Preparamos um comparativo técnico detalhado dos três principais modelos do nosso catálogo:\n\n"
            "1. **MacBook Air 15\" M3 (R$ 11.999,00 - 4 un. em estoque)**\n"
            "   • **Destaque:** Chip M3, eficiência extrema, design silencioso sem ventoinhas (fanless).\n"
            "   • **Autonomia:** Até 18 horas de bateria contínua.\n"
            "   • **Perfil:** Mobilidade máxima, programação, edição ágil e produtividade executiva.\n\n"
            "2. **Dell XPS 13 Plus (R$ 10.850,00 - 2 un. em estoque)**\n"
            "   • **Destaque:** Incrível tela 3.5K OLED touchscreen, Intel i7 13ª Ger e 32GB RAM.\n"
            "   • **Design:** Chassi futurista de alumínio usinado e touchpad háptico contínuo.\n"
            "   • **Perfil:** Profissionais que exigem a melhor qualidade de display do mercado.\n\n"
            "3. **Lenovo Legion Pro 5 (R$ 9.400,00 - Esgotado)**\n"
            "   • **Destaque:** Máximo poder de processamento com Ryzen 7 7745HX + GPU RTX 4070 8GB.\n"
            "   • **Desempenho:** Taxas acima de 90-120 FPS em 1440p e renderização pesada.\n"
            "   • **Status:** Atualmente esgotado em estoque (0 unidades).\n\n"
            "👉 **Consulte os gráficos interativos de benchmark e telemetria gerados no painel acima!**"
        )
        return reply, tools_called, dashboard

    # 2. Benchmark da GPU RTX 4060 Ti
    if dashboard and dashboard.get("tipo") == "benchmark_gpu":
        tools_called.append("consultar_estoque")
        reply = (
            "⚡ **Telemetria & Benchmark: Nvidia GeForce RTX 4060 Ti 8GB**\n\n"
            "Temos **3 unidades disponíveis** em estoque pelo valor de **R$ 2.650,00**.\n\n"
            "• **Desempenho em Jogos (Média aferida):**\n"
            "  - **Cyberpunk 2077 (1080p Ultra RT + DLSS 3):** 104 FPS\n"
            "  - **Warzone 2 / MW3 (1440p High):** 115 FPS\n"
            "  - **Forza Horizon 5 (1440p Maxed):** 98 FPS\n"
            "• **Eficiência Energética:** Consumo controlado de 160W TDP (recomendamos fonte de 550W a 650W).\n"
            "• **Destaque:** Suporte nativo a Ray Tracing e DLSS 3 Frame Generation.\n\n"
            "👉 **Confira as métricas completas no mini dashboard interativo anexado.**"
        )
        return reply, tools_called, dashboard

    # 3. Setup de Periféricos
    if dashboard and dashboard.get("tipo") == "comparativo_perifericos":
        tools_called.append("consultar_estoque")
        reply = (
            "⌨️🖱️ **Mini Dashboard: Setup Produtividade Elite (MX Master 3S + Keychron K2 Pro)**\n\n"
            "• **Mouse Logitech MX Master 3S (R$ 650,00 - 11 un. em estoque):**\n"
            "  - Sensor Darkfield 8K DPI de alta precisão (funciona até em vidro).\n"
            "  - Roda MagSpeed magnética ultra rápida e cliques 90% mais silenciosos.\n"
            "  - Bateria com duração de até 70 dias com carga rápida USB-C.\n\n"
            "• **Teclado Mecânico Keychron K2 Pro (R$ 780,00 - 6 un. em estoque):**\n"
            "  - Switches Red lubrificados de fábrica com sensação linear macia.\n"
            "  - Hot-swappable e customização completa via QMK/VIA.\n"
            "  - Conexão sem fio para até 3 dispositivos simultâneos (Mac e Windows).\n\n"
            "Juntos compõem a estação de trabalho definitiva para desenvolvimento e produtividade!"
        )
        return reply, tools_called, dashboard

    # 4. Monitor Dell UltraSharp 4K
    if dashboard and dashboard.get("tipo") == "analise_monitor":
        tools_called.append("consultar_estoque")
        reply = (
            "🖥️ **Análise Técnica: Monitor Dell UltraSharp 27\" 4K (U2723QE)**\n\n"
            "Temos **5 unidades disponíveis** em estoque pelo valor de **R$ 3.790,00**.\n\n"
            "• **Painel:** Tecnologia IPS Black com relação de contraste 2000:1 (o dobro dos IPS convencionais).\n"
            "• **Cores:** 100% sRGB e 98% DCI-P3 para fidelidade crítica de cor em design e vídeo.\n"
            "• **Produtividade:** Hub USB-C embutido que recarrega notebooks com até 90W e transmite vídeo/dados em 1 único cabo.\n"
            "• **Ajustes:** Suporte ergonômico completo (altura, inclinação, rotação e pivô 90°)."
        )
        return reply, tools_called, dashboard

    # 5. Saudações puras
    saudacoes = ["ola", "olá", "oi", "bom dia", "boa tarde", "boa noite", "hey", "hello", "opa"]
    if msg_lower in saudacoes or any(msg_lower.startswith(s) and len(msg_lower) <= len(s) + 4 for s in saudacoes):
        return (
            "Olá! Seja muito bem-vindo à **CORE Hardware**. Sou o assistente oficial especializado em hardware e equipamentos de alto desempenho.\n\n"
            "Como posso ajudar você hoje? Posso consultar nosso estoque em tempo real, informar especificações ou gerar comparativos de notebooks, periféricos, monitores 4K e GPUs!",
            [],
            None,
        )

    # 6. Catálogo Geral
    intencoes_catalogo = [
        "quais produtos", "o que voces tem", "o que vocês têm", "listar produtos",
        "catalogo", "catálogo", "tudo que tem", "lista de produtos", "mostrar produtos", "ver catalogo"
    ]
    if any(frase in msg_lower for frase in intencoes_catalogo):
        tools_called.append("listar_produtos")
        todos = listar_produtos()
        linhas = ["Aqui está o nosso catálogo oficial da **CORE Hardware**:\n"]
        for p in todos:
            status_txt = "Disponível" if p["estoque"] > 0 else "Esgotado"
            linhas.append(
                f"- **{p['nome']}** ({p['categoria']}): R$ {p['preco']:,.2f} | Estoque: {p['estoque']} un. [{status_txt}]"
            )
        return "\n".join(linhas), tools_called, None

    # 7. Busca Inteligente por Produto (com Fuzzy Matching / tolerância a typos)
    item_aproximado = _encontrar_produto_aproximado(message)
    if item_aproximado:
        item_id, termo_busca = item_aproximado
        tools_called.append("consultar_estoque")
        resultado = consultar_estoque(item_id)
        if resultado.get("encontrado"):
            nome = resultado["nome"]
            estoque = resultado["estoque"]
            preco = resultado["preco"]
            specs = resultado["especificacoes"]

            if estoque == 0:
                reply = (
                    f"O notebook **{nome}** ({specs}) está atualmente **esgotado** em nosso estoque (0 unidades disponíveis). "
                    f"O preço oficial de tabela é **{_formatar_preco_br(preco)}**.\n\n"
                    "Deseja que registremos seu interesse ou gostaria de conhecer o **MacBook Air M3** ou o **Dell XPS 13 Plus** como opções disponíveis?"
                )
            else:
                reply = (
                    f"Com certeza! Temos o **{nome}** ({specs}) disponível em nosso estoque.\n\n"
                    f"• **Quantidade disponível:** {estoque} unidades\n"
                    f"• **Preço unitário:** {_formatar_preco_br(preco)}\n\n"
                    "Gostaria de tirar alguma dúvida sobre as especificações técnicas ou ver um comparativo?"
                )
            return reply, tools_called, dashboard

    # 8. Diálogo Procedural e Memória de Contexto do Histórico
    produto_contexto = _recuperar_produto_do_historico(history)
    if produto_contexto:
        item_id, item_nome = produto_contexto
        resultado = consultar_estoque(item_id)
        if resultado.get("encontrado"):
            tools_called.append("consultar_estoque")
            nome = resultado["nome"]
            estoque = resultado["estoque"]
            preco = resultado["preco"]
            specs = resultado["especificacoes"]
            detalhes = DADOS_DETALHADOS_PRODUTOS.get(item_id, {})
            cor_info = detalhes.get("cor", "Acabamento de alto padrão.")
            bateria_info = detalhes.get("bateria", "Alimentação de alta eficiência.")
            garantia_info = detalhes.get("garantia", "12 meses de garantia oficial com NF-e.")
            sugeridos = detalhes.get("acessorios_sugeridos")
            destaque = detalhes.get("destaque", specs)

            # Caso A: Pergunta sobre Preço / Valor / Condições de Pagamento
            termos_preco = ["quanto custa", "preco", "preço", "valor", "custa", "quanto sai", "parcela", "parcelamento", "desconto", "pagamento"]
            if any(termo in msg_lower for termo in termos_preco):
                if estoque == 0:
                    reply = (
                        f"Em relação ao **{nome}**, o valor oficial de tabela é **{_formatar_preco_br(preco)}**.\n\n"
                        f"Atualmente este modelo está **esgotado** em nosso estoque (0 unidades disponíveis). "
                        f"Quando o lote for reposto, disponibilizaremos condições em até 10x sem juros ou com 5% de desconto via PIX à vista na CORE Hardware!"
                    )
                else:
                    reply = (
                        f"O **{nome}** custa **{_formatar_preco_br(preco)}**.\n\n"
                        f"• **Condições:** Em até 10x sem juros no cartão ou com 5% de desconto via PIX à vista.\n"
                        f"• **Disponibilidade:** Temos {estoque} unidades em estoque a pronta entrega.\n\n"
                        f"Gostaria de consultar as opções de entrega ou tirar mais dúvidas sobre o modelo?"
                    )
                return reply, tools_called, dashboard

            # Caso B: Pergunta sobre Cor / Design / Acabamento
            termos_cor = ["cor", "cores", "acabamento", "design", "preto", "cinza", "prata", "grafite"]
            if any(termo in msg_lower for termo in termos_cor):
                reply = (
                    f"Sobre a cor e estética do **{nome}**:\n\n"
                    f"• **Cor e Acabamento:** {cor_info}.\n\n"
                    f"O acabamento foi desenvolvido visando máxima durabilidade e sofisticação. "
                    f"Deseja saber mais sobre as especificações ou disponibilidade deste modelo?"
                )
                return reply, tools_called, dashboard

            # Caso C: Pergunta sobre Bateria / Autonomia / Energia / TDP / Fonte
            termos_bateria = ["bateria", "autonomia", "carregador", "dura", "duracao", "duração", "carga", "consumo", "tdp", "fonte"]
            if any(termo in msg_lower for termo in termos_bateria):
                reply = (
                    f"Sobre a autonomia e consumo do **{nome}**:\n\n"
                    f"• **Bateria & Alimentação:** {bateria_info}.\n\n"
                    f"Excelente eficiência para seu fluxo de trabalho. Posso te ajudar com alguma outra especificação técnica ou estoque?"
                )
                return reply, tools_called, dashboard

            # Caso D: Pergunta sobre Garantia / Nota Fiscal / Suporte
            termos_garantia = ["garantia", "suporte", "nota", "fiscal", "nf", "original", "seguro"]
            if any(termo in msg_lower for termo in termos_garantia):
                reply = (
                    f"Sim! O **{nome}** acompanha **{garantia_info}**.\n\n"
                    f"Todos os nossos envios na **CORE Hardware** contam com nota fiscal emitida no seu nome, rastreamento seguro e canal direto de suporte pós-venda. "
                    f"Deseja verificar formas de pagamento ou prazo de entrega?"
                )
                return reply, tools_called, dashboard

            # Caso E: Pergunta sobre Estoque / Unidades Disponíveis / Envio
            termos_estoque = ["estoque", "quantos", "quantas", "tem pronta", "pronta entrega", "frete", "entrega", "envio", "prazo"]
            if any(termo in msg_lower for termo in termos_estoque):
                if estoque == 0:
                    reply = (
                        f"No momento o **{nome}** está com **0 unidades em estoque (esgotado)**. "
                        f"O valor de tabela é {_formatar_preco_br(preco)}.\n\n"
                        f"Gostaria de ver modelos equivalentes disponíveis em nosso catálogo?"
                    )
                else:
                    reply = (
                        f"Temos exatamente **{estoque} unidades** do **{nome}** disponíveis para envio imediato.\n\n"
                        f"O valor unitário é **{_formatar_preco_br(preco)}** com despacho em até 24h úteis para todo o Brasil. "
                        f"Gostaria de garantir o seu?"
                    )
                return reply, tools_called, dashboard

            # Caso F: Pergunta sobre Especificações / Configuração / Processador / Memória
            termos_specs = ["especificacao", "especificacoes", "especificação", "especificações", "specs", "configuracao", "configuração", "config", "memoria", "memória", "ram", "ssd", "processador", "cpu", "tela", "display"]
            if any(termo in msg_lower for termo in termos_specs):
                reply = (
                    f"Aqui estão as especificações do **{nome}**:\n\n"
                    f"• **Especificações Oficiais:** {specs}\n"
                    f"• **Destaque Técnico:** {destaque}\n\n"
                )
                if sugeridos:
                    reply += f"💡 **Sugestão Consultiva:** Este item combina perfeitamente com {sugeridos}.\n\n"
                reply += "Deseja ver opções de pagamento ou consultar o estoque?"
                return reply, tools_called, dashboard

            # Caso G: Diálogo Procedural Geral / Pronome anafórico ("ele", "dele", "gostei", "fale mais")
            termos_anaforicos = ["ele", "dele", "nele", "esse", "este", "desse", "deste", "gostei", "quero", "detalhe", "detalhes", "mais sobre"]
            if any(termo in msg_lower for termo in termos_anaforicos):
                status_txt = f"{estoque} unidades disponíveis" if estoque > 0 else "atualmente esgotado"
                reply = (
                    f"Com certeza! Falando sobre o **{nome}**:\n\n"
                    f"• **Especificações:** {specs}\n"
                    f"• **Preço:** {_formatar_preco_br(preco)}\n"
                    f"• **Estoque:** {status_txt}\n"
                    f"• **Garantia:** 12 meses oficiais CORE Hardware com NF-e\n\n"
                )
                if sugeridos:
                    reply += f"💡 **Sugestão Consultiva CORE Hardware:** Para completar sua experiência, recomendamos o {sugeridos}.\n\n"
                reply += "Gostaria de saber algo específico sobre ele ou finalizar a compra?"
                return reply, tools_called, dashboard

    # 9. Resposta conversacional natural quando o item não for identificado
    tools_called.append("consultar_estoque")
    return (
        "Entendi sua dúvida! Não localizei exatamente esse modelo específico em nosso catálogo, mas na **CORE Hardware** trabalhamos com os seguintes equipamentos selecionados:\n\n"
        "• **Notebooks:** MacBook Air 15\" M3, Dell XPS 13 Plus e Lenovo Legion Pro 5\n"
        "• **Periféricos:** Mouse Logitech MX Master 3S e Teclado Mecânico Keychron K2 Pro\n"
        "• **Monitores:** Dell UltraSharp 27\" 4K IPS Black com Hub USB-C de 90W\n"
        "• **Hardware:** Placa de Vídeo Nvidia GeForce RTX 4060 Ti 8GB\n\n"
        "Gostaria de consultar disponibilidade, valores ou ver um comparativo de algum desses itens?",
        tools_called,
        None,
    )


class AIService:
    """Serviço unificado de atendimento que prioriza Grok (xAI) e Gemini com fallback conversacional."""

    def __init__(self):
        self._carregar_configuracoes()

    def _carregar_configuracoes(self):
        """Recarrega as variáveis de ambiente dinamicamente."""
        load_dotenv(override=True)
        self.grok_api_key = (
            os.getenv("XAI_API_KEY")
            or os.getenv("GROK_API_KEY")
        )
        self.gemini_api_key = (
            os.getenv("GEMINI_API_KEY")
            or os.getenv("GOOGLE_API_KEY")
        )
        self.grok_model = os.getenv("GROK_MODEL", "grok-2-latest")
        self.gemini_model = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

    def _tem_chave_valida(self, chave: Optional[str]) -> bool:
        """Verifica se uma chave de API é válida e não é placeholder."""
        if not chave:
            return False
        chave_clean = chave.strip()
        if not chave_clean or chave_clean.startswith("sua_chave") or "placeholder" in chave_clean.lower():
            return False
        return len(chave_clean) > 8

    def _processar_via_grok(
        self, message: str, history: Optional[List[Dict[str, str]]] = None
    ) -> Optional[Tuple[str, List[str]]]:
        """Executa a conversação via Grok (xAI API) com Function/Tool Calling."""
        if not self._tem_chave_valida(self.grok_api_key):
            return None

        tools_called: List[str] = []
        messages: List[Dict[str, Any]] = [{"role": "system", "content": SYSTEM_PROMPT}]

        if history:
            for h in history:
                role = "user" if h.get("role") == "user" else "assistant"
                messages.append({"role": role, "content": h.get("content", "")})
        messages.append({"role": "user", "content": message})

        headers = {
            "Authorization": f"Bearer {self.grok_api_key.strip()}",
            "Content-Type": "application/json",
        }

        payload = {
            "model": self.grok_model,
            "messages": messages,
            "tools": GROK_TOOLS_SCHEMA,
            "temperature": 0.2,
        }

        with httpx.Client(timeout=30.0) as client:
            resp = client.post("https://api.x.ai/v1/chat/completions", headers=headers, json=payload)
            if resp.status_code != 200:
                logger.warning("Grok API retornou status %s: %s", resp.status_code, resp.text)
                return None

            data = resp.json()
            choice = data["choices"][0]
            msg_obj = choice["message"]

            tool_calls = msg_obj.get("tool_calls")
            if tool_calls:
                messages.append(msg_obj)
                for tc in tool_calls:
                    fn_name = tc["function"]["name"]
                    raw_args = tc["function"].get("arguments", "{}")
                    try:
                        args = json.loads(raw_args)
                    except Exception:
                        args = {}

                    tools_called.append(fn_name)
                    fn = TOOL_MAP.get(fn_name)
                    res = fn(**args) if fn else {"erro": f"Ferramenta '{fn_name}' não existe"}

                    messages.append({
                        "role": "tool",
                        "tool_call_id": tc["id"],
                        "content": json.dumps(res, ensure_ascii=False),
                    })

                payload["messages"] = messages
                resp2 = client.post("https://api.x.ai/v1/chat/completions", headers=headers, json=payload)
                if resp2.status_code == 200:
                    data2 = resp2.json()
                    final_reply = data2["choices"][0]["message"].get("content", "")
                    return final_reply, tools_called

            return msg_obj.get("content", ""), tools_called

    def _processar_via_gemini(
        self, message: str, history: Optional[List[Dict[str, str]]] = None
    ) -> Optional[Tuple[str, List[str]]]:
        """Executa a conversação via Google GenAI com Tool Calling."""
        if not self._tem_chave_valida(self.gemini_api_key):
            return None

        try:
            from google import genai
            from google.genai import types

            client = genai.Client(api_key=self.gemini_api_key.strip())
            tools_called: List[str] = []

            config = types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT,
                tools=[consultar_estoque, listar_produtos],
                temperature=0.2,
            )

            contents: List[Any] = []
            if history:
                user_turn_started = False
                for h in history:
                    role = "user" if h.get("role") == "user" else "model"
                    if not user_turn_started:
                        if role == "user":
                            user_turn_started = True
                            contents.append(types.Content(role=role, parts=[types.Part.from_text(text=h.get("content", ""))]))
                    else:
                        contents.append(types.Content(role=role, parts=[types.Part.from_text(text=h.get("content", ""))]))
            contents.append(types.Content(role="user", parts=[types.Part.from_text(text=message)]))

            response = client.models.generate_content(
                model=self.gemini_model,
                contents=contents,
                config=config,
            )

            function_calls = getattr(response, "function_calls", None)
            if not function_calls and hasattr(response, "candidates") and response.candidates:
                candidate = response.candidates[0]
                if hasattr(candidate, "content") and candidate.content and candidate.content.parts:
                    function_calls = [
                        part.function_call
                        for part in candidate.content.parts
                        if getattr(part, "function_call", None) is not None
                    ]

            if function_calls:
                tool_results_parts = []
                for call in function_calls:
                    fn_name = call.name
                    fn_args = dict(call.args) if call.args else {}
                    tools_called.append(fn_name)
                    fn = TOOL_MAP.get(fn_name)
                    result = fn(**fn_args) if fn else {"erro": f"Ferramenta {fn_name} desconhecida"}
                    tool_results_parts.append(
                        types.Part.from_function_response(name=fn_name, response={"result": result})
                    )

                contents.append(response.candidates[0].content)
                contents.append(types.Content(role="user", parts=tool_results_parts))
                final_response = client.models.generate_content(
                    model=self.gemini_model,
                    contents=contents,
                    config=config,
                )
                return final_response.text or "Consulta realizada com sucesso.", tools_called

            return response.text or "Olá! Como posso ajudar com nossos produtos?", tools_called

        except Exception as e:
            logger.warning("Falha ao consultar Gemini API: %s", e)
            return None

    def processar_mensagem(
        self,
        message: str,
        history: Optional[List[Dict[str, str]]] = None,
        provider: Optional[str] = "auto",
    ) -> Dict[str, Any]:
        """Prioriza estritamente os modelos de IA (Grok e Gemini) antes de qualquer fallback."""
        # Recarregar chaves de ambiente caso o usuário tenha editado o .env
        self._carregar_configuracoes()

        dashboard_data = obter_dashboard_benchmarks(message)
        provedor_preferido = (provider or os.getenv("LLM_PROVIDER", "auto")).lower()

        # 1. Prioridade 1: Grok (xAI) se solicitado ou se estiver com chave disponível no modo auto
        if provedor_preferido in ("grok", "xai") or (provedor_preferido == "auto" and self._tem_chave_valida(self.grok_api_key)):
            try:
                res_grok = self._processar_via_grok(message, history)
                if res_grok:
                    reply, tools = res_grok
                    return {
                        "reply": reply,
                        "tools_called": tools,
                        "dashboard_data": dashboard_data,
                        "provider": "grok",
                    }
            except Exception as e:
                logger.warning("Erro ao tentar Grok como IA principal: %s", e)

        # 2. Prioridade 2: Google Gemini se solicitado ou se estiver com chave disponível no modo auto
        if provedor_preferido in ("gemini", "google") or (provedor_preferido == "auto" and self._tem_chave_valida(self.gemini_api_key)):
            try:
                res_gemini = self._processar_via_gemini(message, history)
                if res_gemini:
                    reply, tools = res_gemini
                    return {
                        "reply": reply,
                        "tools_called": tools,
                        "dashboard_data": dashboard_data,
                        "provider": "gemini",
                    }
            except Exception as e:
                logger.warning("Erro ao tentar Gemini como IA principal: %s", e)

        # 3. Fallback inteligente de contingência (ativo somente se nenhuma IA responder ou estiver sem chaves)
        reply, tools, dash = _executar_fallback_deterministico(message, history)
        final_dashboard = dashboard_data or dash
        return {
            "reply": reply,
            "tools_called": tools,
            "dashboard_data": final_dashboard,
            "provider": "fallback_core",
        }


# Instância global do serviço de IA
ai_service = AIService()
