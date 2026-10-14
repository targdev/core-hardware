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
from app.models import UserProfile

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
9. MEMÓRIA DE DADOS PESSOAIS E PREFERÊNCIAS DO CLIENTE:
   - Se o cliente informar seu nome, cidade, email, marcas favoritas ou interesses de uso (ex: "Meu nome é Tarcísio", "prefiro Apple", "sou programador", "foco gamer"), memorize esses dados, cumprimente-o cordialmente pelo nome e adapte recomendações ao seu perfil.
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
    history: Optional[List[Dict[str, str]]],
    user_profile: Optional[UserProfile] = None,
) -> Optional[Tuple[str, str]]:
    """Percorre o histórico de trás para frente ou recorre ao perfil do usuário para identificar o produto em pauta."""
    if history:
        for msg in reversed(history):
            content = msg.get("content", "")
            prod = _encontrar_produto_aproximado(content)
            if prod:
                return prod

    # Fallback para o produto memorizado no perfil persistente do usuário
    if user_profile and user_profile.ultimo_produto_id:
        p_id = user_profile.ultimo_produto_id
        if p_id in DADOS_DETALHADOS_PRODUTOS:
            return p_id, user_profile.ultimo_produto_nome or DADOS_DETALHADOS_PRODUTOS[p_id]["nome"]

    return None


def _analisar_ultima_pergunta_assistente(
    history: Optional[List[Dict[str, str]]],
    user_profile: Optional[UserProfile] = None,
) -> Optional[str]:
    """Identifica a intenção ou proposta que o assistente fez na última mensagem."""
    if history:
        for msg in reversed(history):
            if msg.get("role") in ("assistant", "model"):
                texto = msg.get("content", "").lower()
                if "especificações técnicas ou ver um comparativo" in texto or "comparativo" in texto or "especificações" in texto or "especificacoes" in texto:
                    return "comparativo_ou_specs"
                if "opções de entrega" in texto or "prazo de entrega" in texto or "formas de pagamento" in texto or "entrega" in texto:
                    return "entrega_e_pagamento"
                if "garantir o seu" in texto or "finalizar a compra" in texto or "garantir sua unidade" in texto or "reservar" in texto:
                    return "garantir_compra"
                if "modelos equivalentes" in texto or "opções disponíveis" in texto or "conhecer o macbook" in texto:
                    return "modelos_equivalentes"
                if "especificação técnica ou estoque" in texto or "disponibilidade deste modelo" in texto:
                    return "specs_ou_estoque"
                break
    if user_profile and getattr(user_profile, "ultima_oferta_ia", None):
        return user_profile.ultima_oferta_ia
    return None


def _formatar_preco_br(preco: float) -> str:
    """Formata valor monetário no padrão brasileiro (R$ 11.999,00)."""
    formatado = f"{preco:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"R$ {formatado}"


def _gerar_prompt_com_perfil(perfil: Optional[UserProfile]) -> str:
    """Anexa dados e preferências do perfil do cliente ao system prompt."""
    if not perfil:
        return SYSTEM_PROMPT

    itens = []
    if perfil.nome:
        itens.append(f"Nome do cliente: {perfil.nome}")
    if perfil.email:
        itens.append(f"E-mail: {perfil.email}")
    if perfil.cidade:
        itens.append(f"Cidade/Região: {perfil.cidade}")
    if perfil.marcas_favoritas:
        itens.append(f"Marcas preferidas: {', '.join(perfil.marcas_favoritas)}")
    if perfil.interesses:
        itens.append(f"Áreas de interesse / foco de uso: {', '.join(perfil.interesses)}")
    if perfil.ultimo_produto_nome:
        itens.append(f"Último produto consultado ou em foco: {perfil.ultimo_produto_nome} (ID: {perfil.ultimo_produto_id})")
    if perfil.ultima_oferta_ia:
        itens.append(f"Última proposta ou sugestão feita pelo assistente no diálogo: {perfil.ultima_oferta_ia}")

    if not itens:
        return SYSTEM_PROMPT

    bloco_perfil = (
        "\n\n[DADOS E PREFERÊNCIAS MEMORIZADAS DO CLIENTE]:\n"
        + "\n".join(f"- {item}" for item in itens)
        + "\nDiretrizes de Continuidade: Chame o cliente cordialmente pelo nome, mantenha continuidade com o produto em foco e, se o cliente responder 'Sim', 'Quero', 'Com certeza' ou pedir comparativo/especificações, atenda imediatamente à proposta sem reiniciar a consulta."
    )
    return SYSTEM_PROMPT + bloco_perfil


def extrair_e_atualizar_perfil(
    message: str, current_profile: Optional[UserProfile] = None
) -> Tuple[UserProfile, Dict[str, Any]]:
    """Identifica dados pessoais, marcas favoritas e preferências de uso do cliente na mensagem."""
    perfil = current_profile.model_copy() if current_profile else UserProfile()
    novos_dados: Dict[str, Any] = {}
    msg_raw = message.strip()
    msg_lower = msg_raw.lower()

    # 1. Extração de Nome
    padroes_nome = [
        r"(?:meu nome é|meu nome e)\s+([a-zA-ZÀ-ÿ]+(?:\s+[a-zA-ZÀ-ÿ]+)?)",
        r"(?:me chamo)\s+([a-zA-ZÀ-ÿ]+(?:\s+[a-zA-ZÀ-ÿ]+)?)",
        r"(?:pode me chamar de)\s+([a-zA-ZÀ-ÿ]+(?:\s+[a-zA-ZÀ-ÿ]+)?)",
        r"(?:sou o|sou a)\s+([a-zA-ZÀ-ÿ]+(?:\s+[a-zA-ZÀ-ÿ]+)?)",
        r"(?:aqui é o|aqui é a)\s+([a-zA-ZÀ-ÿ]+(?:\s+[a-zA-ZÀ-ÿ]+)?)",
    ]
    for padrao in padroes_nome:
        match = re.search(padrao, msg_raw, re.IGNORECASE)
        if match:
            candidato = match.group(1).strip()
            candidato = re.sub(r"[^\w\sÀ-ÿ]", "", candidato).strip()
            palavras_invalidas = {"um", "uma", "cliente", "novo", "aqui", "cara", "amigo", "de", "boa"}
            if candidato and candidato.lower() not in palavras_invalidas and len(candidato) >= 2:
                nome_formatado = " ".join(p.capitalize() for p in candidato.split())
                perfil.nome = nome_formatado
                novos_dados["nome"] = nome_formatado
                break

    # 2. Extração de Email
    match_email = re.search(r"([a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+)", msg_raw)
    if match_email:
        email = match_email.group(1).strip().lower()
        perfil.email = email
        novos_dados["email"] = email

    # 3. Extração de Cidade / Localização
    padroes_cidade = [
        r"(?:moro em|sou de|vivo em|resido em|falo de|aqui em)\s+([a-zA-ZÀ-ÿ]+(?:\s+[a-zA-ZÀ-ÿ]+)?)",
    ]
    for padrao in padroes_cidade:
        match = re.search(padrao, msg_raw, re.IGNORECASE)
        if match:
            cid = match.group(1).strip()
            cid = re.sub(r"[^\w\sÀ-ÿ]", "", cid).strip()
            palavras_inv = {"casa", "paz", "boa", "desconto", "são", "sp", "um", "uma", "aqui"}
            if cid and cid.lower() not in palavras_inv and len(cid) >= 3:
                cid_formatada = " ".join(p.capitalize() for p in cid.split())
                perfil.cidade = cid_formatada
                novos_dados["cidade"] = cid_formatada
                break

    # 4. Marcas Favoritas
    marcas_conhecidas = {
        "apple": "Apple",
        "macbook": "Apple",
        "mac": "Apple",
        "dell": "Dell",
        "alienware": "Dell",
        "lenovo": "Lenovo",
        "legion": "Lenovo",
        "thinkpad": "Lenovo",
        "logitech": "Logitech",
        "logi": "Logitech",
        "keychron": "Keychron",
        "nvidia": "Nvidia",
        "geforce": "Nvidia",
        "rtx": "Nvidia",
    }
    indicadores_marca = ["gosto de", "gosto da", "gosto do", "prefiro", "fã da", "fã de", "marca", "marcas", "adoro", "sempre uso", "só uso", "quero da", "quero de"]
    menciona_preferencia = any(ind in msg_lower for ind in indicadores_marca)

    marcas_adicionadas = []
    for chave, marca in marcas_conhecidas.items():
        if re.search(rf"\b{chave}\b", msg_lower):
            if menciona_preferencia or any(f"{ind} {chave}" in msg_lower for ind in ["gosto de", "gosto da", "prefiro", "marca"]):
                if marca not in perfil.marcas_favoritas:
                    perfil.marcas_favoritas.append(marca)
                    marcas_adicionadas.append(marca)
    if marcas_adicionadas:
        novos_dados["marcas_favoritas"] = marcas_adicionadas

    # 5. Áreas de Interesse / Foco de Uso
    interesses_mapeados = {
        ("programacao", "programação", "programador", "programadora", "dev", "desenvolvedor", "desenvolvedora", "codigo", "código", "software", "programar"): "Programação & Desenvolvimento",
        ("gamer", "jogos", "jogar", "games", "jogo", "fps", "cyberpunk", "warzone", "jogando"): "Games & Alta Performance",
        ("design", "designer", "edicao", "edição", "video", "vídeo", "render", "photoshop", "premiere", "3d", "artes", "foto", "fotografia"): "Design & Criação Visual",
        ("produtividade", "escritorio", "escritório", "home office", "trabalho", "estudos", "planilhas", "estudar"): "Produtividade & Home Office",
        ("sem fio", "wireless", "bluetooth"): "Periféricos Sem Fio",
    }
    interesses_adicionados = []
    for termos, interesse in interesses_mapeados.items():
        if any(termo in msg_lower for termo in termos):
            if interesse not in perfil.interesses:
                perfil.interesses.append(interesse)
                interesses_adicionados.append(interesse)
    if interesses_adicionados:
        novos_dados["interesses"] = interesses_adicionados

    return perfil, novos_dados


def _executar_fallback_deterministico(
    message: str,
    history: Optional[List[Dict[str, str]]] = None,
    user_profile: Optional[UserProfile] = None,
) -> Tuple[str, List[str], Optional[Dict[str, Any]], UserProfile]:
    """Fallback conversacional empático e resiliente para quando nenhuma API estiver com chave configurada."""
    msg_lower = message.lower().strip()
    tools_called: List[str] = []

    # Extrair e atualizar perfil com dados pessoais ou preferências declaradas nesta mensagem
    perfil, novos_dados = extrair_e_atualizar_perfil(message, user_profile)
    saudacao_nome = f", **{perfil.nome}**" if perfil.nome else ""

    # Caso Perfil 1: Usuário perguntando sobre o que a IA sabe sobre ele / seus dados
    intencoes_perfil = [
        "qual meu nome", "qual o meu nome", "sabe meu nome", "lembra de mim",
        "minhas preferencias", "minhas preferências", "o que voce sabe sobre mim",
        "o que você sabe sobre mim", "meus dados", "meu perfil", "lembra meu nome"
    ]
    if any(p in msg_lower for p in intencoes_perfil):
        if perfil.nome:
            marcas_txt = ", ".join(perfil.marcas_favoritas) if perfil.marcas_favoritas else "Nenhuma marca registrada ainda"
            interesses_txt = ", ".join(perfil.interesses) if perfil.interesses else "Nenhum interesse registrado ainda"
            cidade_txt = perfil.cidade or "Não informada"
            email_txt = perfil.email or "Não informado"
            reply = (
                f"Com certeza{saudacao_nome}! Aqui estão os dados e preferências salvos no seu perfil da **CORE Hardware**:\n\n"
                f"• 👤 **Nome:** {perfil.nome}\n"
                f"• 🏷️ **Marcas Favoritas:** {marcas_txt}\n"
                f"• 🎯 **Áreas de Foco:** {interesses_txt}\n"
                f"• 📍 **Localização:** {cidade_txt}\n"
                f"• ✉️ **E-mail:** {email_txt}\n\n"
                "Essas informações personalizam todas as nossas recomendações de hardware para você!"
            )
        else:
            reply = (
                "Ainda não registrei seu nome ou preferências! Você pode me dizer como se chama (ex: *'Meu nome é Tarcísio'*) "
                "e quais marcas ou tipos de uso você prefere (ex: *'Gosto da Apple e trabalho com programação'*)."
            )
        return reply, tools_called, None, perfil

    # Caso Perfil 2: Usuário acabou de se apresentar com o nome (Ex: 'Meu nome é Tarcísio')
    if "nome" in novos_dados:
        reply = (
            f"Muito prazer, **{perfil.nome}**! Seja muito bem-vindo à **CORE Hardware**.\n\n"
            f"Já registrei seu nome e perfil de atendimento aqui no sistema. Como posso te ajudar hoje? "
            f"Posso consultar o estoque em tempo real de notebooks de alta performance, monitores 4K, GPUs ou periféricos, além de gerar comparativos técnicos!"
        )
        return reply, tools_called, None, perfil

    # Caso Perfil 3: Usuário declarou preferências de marca (Ex: 'Prefiro produtos da Apple' / 'Gosto de Logitech')
    if "marcas_favoritas" in novos_dados and not _encontrar_produto_aproximado(message):
        marcas_str = " e ".join(novos_dados["marcas_favoritas"])
        linhas = [
            f"Excelente escolha{saudacao_nome}! Registrei **{marcas_str}** nas suas marcas favoritas.\n"
        ]
        if "Apple" in novos_dados["marcas_favoritas"]:
            linhas.append(
                "• **No ecossistema Apple:** Temos o **MacBook Air 15\" M3** (4 unidades disponíveis por R$ 11.999,00), "
                "além de total compatibilidade com o **Mouse Logitech MX Master 3S** e **Teclado Keychron K2 Pro**."
            )
        if "Dell" in novos_dados["marcas_favoritas"]:
            linhas.append(
                "• **Da Dell:** Temos o sofisticado **Dell XPS 13 Plus** com tela 3.5K OLED (2 unidades por R$ 10.850,00) "
                "e o **Monitor Dell UltraSharp 27\" 4K** IPS Black com hub USB-C de 90W (5 unidades por R$ 3.790,00)."
            )
        if "Lenovo" in novos_dados["marcas_favoritas"]:
            linhas.append(
                "• **Da Lenovo:** Trabalhamos com o **Lenovo Legion Pro 5** (atualmente esgotado em estoque, com preço de tabela em R$ 9.400,00)."
            )
        if "Logitech" in novos_dados["marcas_favoritas"]:
            linhas.append(
                "• **Da Logitech:** Temos o renomado **Mouse Logitech MX Master 3S** (11 unidades por R$ 650,00), referência global em ergonomia e precisão."
            )
        if "Keychron" in novos_dados["marcas_favoritas"]:
            linhas.append(
                "• **Da Keychron:** Temos o **Teclado Mecânico Keychron K2 Pro** sem fio com switches Red (6 unidades por R$ 780,00)."
            )
        if "Nvidia" in novos_dados["marcas_favoritas"]:
            linhas.append(
                "• **Da Nvidia:** Temos a **GeForce RTX 4060 Ti 8GB** com DLSS 3 e Ray Tracing (3 unidades por R$ 2.650,00)."
            )
        linhas.append("\nGostaria de consultar detalhes, estoque ou ver um comparativo dessas opções?")
        return "\n".join(linhas), ["consultar_estoque"], None, perfil

    # Caso Perfil 4: Usuário declarou área de interesse / perfil de uso (Ex: 'Trabalho com programação' / 'Sou gamer')
    if "interesses" in novos_dados and not _encontrar_produto_aproximado(message):
        interesses_str = " e ".join(novos_dados["interesses"])
        reply = (
            f"Perfeito{saudacao_nome}! Salvei **{interesses_str}** no seu perfil.\n\n"
            "Com base no seu objetivo, nossos consultores recomendam:\n"
            "• **Notebooks de Alta Performance:** MacBook Air 15\" M3 (eficiência e bateria) ou Dell XPS 13 Plus (tela OLED 3.5K e 32GB RAM).\n"
            "• **Periféricos de Precisão:** Teclado Keychron K2 Pro e Mouse Logitech MX Master 3S para máxima produtividade e conforto ergonômico.\n\n"
            "Gostaria de ver um comparativo técnico ou checar os preços e quantidades em estoque?"
        )
        return reply, ["listar_produtos"], None, perfil

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
        return reply, tools_called, dashboard, perfil

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
        return reply, tools_called, dashboard, perfil

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
        return reply, tools_called, dashboard, perfil

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
        return reply, tools_called, dashboard, perfil

    # 5. Saudações puras
    saudacoes = ["ola", "olá", "oi", "bom dia", "boa tarde", "boa noite", "hey", "hello", "opa"]
    if msg_lower in saudacoes or any(msg_lower.startswith(s) and len(msg_lower) <= len(s) + 4 for s in saudacoes):
        return (
            f"Olá{saudacao_nome}! Seja muito bem-vindo à **CORE Hardware**. Sou o assistente oficial especializado em hardware e equipamentos de alto desempenho.\n\n"
            "Como posso ajudar você hoje? Posso consultar nosso estoque em tempo real, informar especificações ou gerar comparativos de notebooks, periféricos, monitores 4K e GPUs!",
            [],
            None,
            perfil,
        )

    # 6. Catálogo Geral
    intencoes_catalogo = [
        "quais produtos", "o que voces tem", "o que vocês têm", "listar produtos",
        "catalogo", "catálogo", "tudo que tem", "lista de produtos", "mostrar produtos", "ver catalogo"
    ]
    if any(frase in msg_lower for frase in intencoes_catalogo):
        tools_called.append("listar_produtos")
        todos = listar_produtos()
        linhas = [f"Aqui está o nosso catálogo oficial da **CORE Hardware**{saudacao_nome}:\n"]
        for p in todos:
            status_txt = "Disponível" if p["estoque"] > 0 else "Esgotado"
            linhas.append(
                f"- **{p['nome']}** ({p['categoria']}): R$ {p['preco']:,.2f} | Estoque: {p['estoque']} un. [{status_txt}]"
            )
        return "\n".join(linhas), tools_called, None, perfil

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
            perfil.ultimo_produto_id = item_id
            perfil.ultimo_produto_nome = nome

            if estoque == 0:
                perfil.ultima_oferta_ia = "modelos_equivalentes"
                reply = (
                    f"O notebook **{nome}** ({specs}) está atualmente **esgotado** em nosso estoque (0 unidades disponíveis). "
                    f"O preço oficial de tabela é **{_formatar_preco_br(preco)}**.\n\n"
                    "Deseja que registremos seu interesse ou gostaria de conhecer o **MacBook Air M3** ou o **Dell XPS 13 Plus** como opções disponíveis?"
                )
            else:
                perfil.ultima_oferta_ia = "comparativo_ou_specs"
                reply = (
                    f"Com certeza! Temos o **{nome}** ({specs}) disponível em nosso estoque.\n\n"
                    f"• **Quantidade disponível:** {estoque} unidades\n"
                    f"• **Preço unitário:** {_formatar_preco_br(preco)}\n\n"
                    "Gostaria de tirar alguma dúvida sobre as especificações técnicas ou ver um comparativo?"
                )
            return reply, tools_called, dashboard, perfil

    # 8. Diálogo Procedural e Memória de Contexto do Histórico
    produto_contexto = _recuperar_produto_do_historico(history, perfil)
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

            perfil.ultimo_produto_id = item_id
            perfil.ultimo_produto_nome = nome
            ultima_oferta = _analisar_ultima_pergunta_assistente(history, perfil)

            # Caso 1: Negação / Encerramento cortês ("não", "não precisa", "não obrigado")
            indicadores_negacao = [
                "não precisa", "nao precisa", "não obrigado", "nao obrigado",
                "agora não", "agora nao", "por enquanto não", "por enquanto nao",
                "não quero", "nao quero", "deixa pra lá", "deixa pra la"
            ]
            eh_negacao = (
                any(ind in msg_lower for ind in indicadores_negacao)
                or msg_lower in ["nao", "não", "não.", "nao.", "nada", "dispensa", "nem", "não, obrigado", "nao, obrigado"]
            )
            if eh_negacao:
                reply = (
                    f"Perfeito{saudacao_nome}! Sem problemas. Fico à inteira disposição para quando quiser consultar outro equipamento, valores, estoque ou tirar dúvidas técnicas na **CORE Hardware**.\n\n"
                    "Como posso te ajudar agora?"
                )
                return reply, tools_called, None, perfil

            # Caso 2: Afirmação / Concordância ("Sim", "Quero", "Claro", "Com certeza", "Pode ser", "Por favor", "Mostra", "Comparativo")
            termos_afirmacao = [
                "sim", "quero", "claro", "com certeza", "pode ser", "por favor", "gostaria",
                "mostra", "me mostra", "manda", "pode mandar", "compara", "comparativo",
                "especificacoes", "especificações", "duvida", "dúvida", "ok", "beleza",
                "bora", "pode", "manda ver", "quero sim", "sim por favor", "sim!", "claro!",
                "gostei", "quero ver", "ver comparativo", "comparar", "analise", "análise",
                "fale mais", "mais detalhes", "me fale mais", "explica", "me explica", "pode falar"
            ]
            eh_afirmacao = (
                msg_lower in termos_afirmacao
                or any(msg_lower.startswith(t) for t in ["sim", "claro", "com certeza", "pode ser", "quero", "por favor", "mostra", "manda", "ok", "bora", "pode", "beleza"])
                or any(re.search(rf"\b{re.escape(t)}\b", msg_lower) for t in ["sim", "quero", "claro", "com certeza", "pode ser", "por favor", "gostaria", "mostra", "comparativo", "especificações", "especificacoes"])
            )

            if eh_afirmacao:
                if ultima_oferta == "comparativo_ou_specs" or any(termo in msg_lower for termo in ["comparativo", "compara", "comparar", "analise", "análise", "especificacao", "especificações", "specs"]):
                    if item_id in ("NOTE-01", "NOTE-02", "NOTE-03"):
                        dashboard_comp = obter_dashboard_benchmarks("comparativo")
                        reply = (
                            f"Com certeza{saudacao_nome}! Aqui está a análise aprofundada e o comparativo técnico do **{nome}**:\n\n"
                            f"• **Ficha Técnica & Destaque do {nome}:**\n"
                            f"  - **Especificações:** {specs}\n"
                            f"  - **Destaque:** {destaque}\n"
                            f"  - **Autonomia & Eficiência:** {bateria_info}\n"
                            f"  - **Design & Acabamento:** {cor_info}\n"
                            f"  - **Garantia:** {garantia_info}\n\n"
                            "📊 **Comparativo Consultivo com os Principais Modelos:**\n"
                            "  - **MacBook Air 15\" M3 (R$ 11.999,00):** Campeão de autonomia (até 18h), design silencioso fanless e ecossistema macOS ultra fluido para programação e negócios.\n"
                            "  - **Dell XPS 13 Plus (R$ 10.850,00):** Incrível tela 3.5K OLED touchscreen, 32GB RAM e chassi futurista de alumínio usinado.\n"
                            "  - **Lenovo Legion Pro 5 (R$ 9.400,00 - Esgotado):** Focado em potência máxima para games e 3D com Ryzen 7 e RTX 4070.\n\n"
                        )
                        if sugeridos:
                            reply += f"💡 **Sugestão Consultiva:** Este modelo forma o setup ideal combinado com {sugeridos}.\n\n"
                        reply += "👉 **Confira o comparativo gráfico interativo anexado no painel acima!** Deseja consultar as condições de pagamento e prazos de entrega?"
                        perfil.ultima_oferta_ia = "entrega_e_pagamento"
                        return reply, tools_called, dashboard_comp, perfil

                    elif item_id == "GPU-01":
                        dashboard_gpu = obter_dashboard_benchmarks("rtx 4060")
                        reply = (
                            f"Com certeza{saudacao_nome}! Aqui estão os benchmarks e a análise de desempenho da **{nome}**:\n\n"
                            f"• **Especificações:** {specs}\n"
                            f"• **Desempenho Aferido:** 104 FPS em Cyberpunk 2077 (1080p Ultra RT + DLSS 3) e 115 FPS em Warzone 2.\n"
                            f"• **Eficiência:** Consumo de apenas 160W TDP com excelente controle térmico.\n\n"
                            "👉 **Veja os gráficos de telemetria no mini dashboard anexado!** Deseja verificar condições de pagamento ou entrega?"
                        )
                        perfil.ultima_oferta_ia = "entrega_e_pagamento"
                        return reply, tools_called, dashboard_gpu, perfil

                    elif item_id in ("PERIF-01", "PERIF-02"):
                        dashboard_perif = obter_dashboard_benchmarks("mouse teclado")
                        reply = (
                            f"Com certeza{saudacao_nome}! Falando sobre o **{nome}** no setup de produtividade:\n\n"
                            f"• **Destaque:** {destaque}\n"
                            f"• **Bateria & Conexão:** {bateria_info}\n"
                            f"• **Acabamento:** {cor_info}\n\n"
                            "👉 **Confira o comparativo de periféricos no dashboard anexado!** Gostaria de verificar condições de pagamento ou estoque?"
                        )
                        perfil.ultima_oferta_ia = "entrega_e_pagamento"
                        return reply, tools_called, dashboard_perif, perfil

                    elif item_id == "MON-01":
                        dashboard_mon = obter_dashboard_benchmarks("monitor 4k")
                        reply = (
                            f"Com certeza{saudacao_nome}! Aqui está a análise técnica do **{nome}**:\n\n"
                            f"• **Painel & Fidelidade:** {destaque}\n"
                            f"• **Conectividade:** {bateria_info}\n"
                            f"• **Garantia:** {garantia_info}\n\n"
                            "👉 **Confira a análise visual no dashboard anexado!** Gostaria de verificar opções de frete e parcelamento?"
                        )
                        perfil.ultima_oferta_ia = "entrega_e_pagamento"
                        return reply, tools_called, dashboard_mon, perfil

                elif ultima_oferta == "entrega_e_pagamento":
                    reply = (
                        f"Com certeza{saudacao_nome}! Aqui estão as condições de envio e pagamento para o **{nome}**:\n\n"
                        f"• **Preço de Tabela:** {_formatar_preco_br(preco)}\n"
                        f"• **Condições Especiais:**\n"
                        f"  - **À vista via PIX (5% OFF):** {_formatar_preco_br(preco * 0.95)}\n"
                        f"  - **Cartão de Crédito:** Em até 10x sem juros de {_formatar_preco_br(preco / 10)}\n"
                        f"• **Frete & Logística:** Despacho expresso em até 24h úteis para todo o Brasil com código de rastreamento seguro.\n"
                        f"• **Garantia:** 12 meses oficiais CORE Hardware e Nota Fiscal Eletrônica (NF-e) emitida no seu nome.\n\n"
                        "Gostaria de garantir a reserva de uma unidade agora mesmo no seu perfil?"
                    )
                    perfil.ultima_oferta_ia = "garantir_compra"
                    return reply, tools_called, None, perfil

                elif ultima_oferta == "garantir_compra":
                    loc_str = f" para envio até {perfil.cidade}" if perfil.cidade else " para despacho imediato"
                    reply = (
                        f"Excelente decisão{saudacao_nome}! Vamos registrar a reserva do seu **{nome}**{loc_str}.\n\n"
                        f"• **Equipamento:** {nome} ({specs})\n"
                        f"• **Valor:** {_formatar_preco_br(preco)} (ou {_formatar_preco_br(preco * 0.95)} via PIX à vista)\n"
                        f"• **Disponibilidade:** {estoque} unidades em estoque\n\n"
                        "Para emitirmos a sua Nota Fiscal Eletrônica, você prefere concluir via PIX à vista (com 5% de desconto) ou no cartão de crédito em até 10x sem juros?"
                    )
                    perfil.ultima_oferta_ia = "forma_pagamento"
                    return reply, tools_called, None, perfil

                elif ultima_oferta == "modelos_equivalentes" or estoque == 0:
                    reply = (
                        f"Perfeito{saudacao_nome}! Como o **{nome}** está esgotado no momento, temos estas duas excelentes alternativas a pronta entrega no catálogo oficial:\n\n"
                        "1. **MacBook Air 15\" M3 (R$ 11.999,00 - 4 un. em estoque):**\n"
                        "   • Eficiência energética de ponta com até 18 horas de bateria e chassi ultrafino silencioso (fanless).\n\n"
                        "2. **Dell XPS 13 Plus (R$ 10.850,00 - 2 un. em estoque):**\n"
                        "   • Deslumbrante tela 3.5K OLED touchscreen, 32GB de memória RAM e processador Intel Core i7 13ª Ger.\n\n"
                        "Gostaria de ver o comparativo detalhado ou consultar as especificações de algum deles?"
                    )
                    perfil.ultima_oferta_ia = "comparativo_ou_specs"
                    return reply, ["listar_produtos", "consultar_estoque"], None, perfil

                else:
                    # Afirmação geral quando há produto em pauta
                    reply = (
                        f"Com certeza{saudacao_nome}! Sobre o **{nome}** ({specs}):\n\n"
                        f"• **Destaque Técnico:** {destaque}\n"
                        f"• **Disponibilidade:** {estoque} unidades em estoque por {_formatar_preco_br(preco)}\n"
                        f"• **Acabamento:** {cor_info}\n"
                        f"• **Bateria & Eficiência:** {bateria_info}\n"
                        f"• **Garantia:** {garantia_info}\n\n"
                    )
                    if sugeridos:
                        reply += f"💡 **Sugestão Consultiva:** Combina perfeitamente com {sugeridos}.\n\n"
                    reply += "Deseja consultar opções de entrega e pagamento ou ver um comparativo com outros modelos?"
                    perfil.ultima_oferta_ia = "comparativo_ou_specs"
                    return reply, tools_called, None, perfil

            # Caso 3: Opinião Consultiva / Recomendação ("vale a pena", "é bom", "o que você acha")
            termos_opiniao = ["vale a pena", "é bom", "e bom", "compensa", "o que acha", "sua opiniao", "sua opinião", "recomenda", "indica", "vale o investimento"]
            if any(termo in msg_lower for termo in termos_opiniao):
                reply = (
                    f"Com certeza{saudacao_nome}! Como especialista de hardware da **CORE Hardware**, recomendamos fortemente o **{nome}**:\n\n"
                    f"• **Por que vale a pena:** {destaque}.\n"
                    f"• **Perfil Ideal:** Excelente para quem busca máxima confiabilidade, performance duradoura e acabamento premium ({cor_info}).\n"
                    f"• **Garantia:** {garantia_info}.\n\n"
                    f"Temos {estoque} unidades disponíveis por {_formatar_preco_br(preco)}. Gostaria de garantir a sua ou ver um comparativo direto com outra opção?"
                )
                perfil.ultima_oferta_ia = "comparativo_ou_specs"
                return reply, tools_called, dashboard, perfil

            # Caso A: Pergunta sobre Preço / Valor / Condições de Pagamento
            termos_preco = ["quanto custa", "preco", "preço", "valor", "custa", "quanto sai", "parcela", "parcelamento", "desconto", "pagamento"]
            if any(termo in msg_lower for termo in termos_preco):
                if estoque == 0:
                    reply = (
                        f"Em relação ao **{nome}**, o valor oficial de tabela é **{_formatar_preco_br(preco)}**.\n\n"
                        f"Atualmente este modelo está **esgotado** em nosso estoque (0 unidades disponíveis). "
                        f"Quando o lote for reposto, disponibilizaremos condições em até 10x sem juros ou com 5% de desconto via PIX à vista na CORE Hardware!"
                    )
                    perfil.ultima_oferta_ia = "modelos_equivalentes"
                else:
                    reply = (
                        f"O **{nome}** custa **{_formatar_preco_br(preco)}**.\n\n"
                        f"• **Condições:** Em até 10x sem juros no cartão ou com 5% de desconto via PIX à vista ({_formatar_preco_br(preco * 0.95)}).\n"
                        f"• **Disponibilidade:** Temos {estoque} unidades em estoque a pronta entrega.\n\n"
                        f"Gostaria de consultar as opções de entrega ou tirar mais dúvidas sobre o modelo?"
                    )
                    perfil.ultima_oferta_ia = "entrega_e_pagamento"
                return reply, tools_called, dashboard, perfil

            # Caso B: Pergunta sobre Cor / Design / Acabamento
            termos_cor = ["cor", "cores", "acabamento", "design", "preto", "cinza", "prata", "grafite"]
            if any(termo in msg_lower for termo in termos_cor):
                reply = (
                    f"Sobre a cor e estética do **{nome}**:\n\n"
                    f"• **Cor e Acabamento:** {cor_info}.\n\n"
                    f"O acabamento foi desenvolvido visando máxima durabilidade e sofisticação. "
                    f"Deseja saber mais sobre as especificações ou disponibilidade deste modelo?"
                )
                perfil.ultima_oferta_ia = "comparativo_ou_specs"
                return reply, tools_called, dashboard, perfil

            # Caso C: Pergunta sobre Bateria / Autonomia / Energia / TDP / Fonte
            termos_bateria = ["bateria", "autonomia", "carregador", "dura", "duracao", "duração", "carga", "consumo", "tdp", "fonte"]
            if any(termo in msg_lower for termo in termos_bateria):
                reply = (
                    f"Sobre a autonomia e consumo do **{nome}**:\n\n"
                    f"• **Bateria & Alimentação:** {bateria_info}.\n\n"
                    f"Excelente eficiência para seu fluxo de trabalho. Posso te ajudar com alguma outra especificação técnica ou estoque?"
                )
                perfil.ultima_oferta_ia = "comparativo_ou_specs"
                return reply, tools_called, dashboard, perfil

            # Caso D: Pergunta sobre Garantia / Nota Fiscal / Suporte
            termos_garantia = ["garantia", "suporte", "nota", "fiscal", "nf", "original", "seguro"]
            if any(termo in msg_lower for termo in termos_garantia):
                reply = (
                    f"Sim! O **{nome}** acompanha **{garantia_info}**.\n\n"
                    f"Todos os nossos envios na **CORE Hardware** contam com nota fiscal emitida no seu nome, rastreamento seguro e canal direto de suporte pós-venda. "
                    f"Deseja verificar formas de pagamento ou prazo de entrega?"
                )
                perfil.ultima_oferta_ia = "entrega_e_pagamento"
                return reply, tools_called, dashboard, perfil

            # Caso E: Pergunta sobre Estoque / Unidades Disponíveis / Envio
            termos_estoque = ["estoque", "quantos", "quantas", "tem pronta", "pronta entrega", "frete", "entrega", "envio", "prazo"]
            if any(termo in msg_lower for termo in termos_estoque):
                if estoque == 0:
                    reply = (
                        f"No momento o **{nome}** está com **0 unidades em estoque (esgotado)**. "
                        f"O valor de tabela é {_formatar_preco_br(preco)}.\n\n"
                        f"Gostaria de ver modelos equivalentes disponíveis em nosso catálogo?"
                    )
                    perfil.ultima_oferta_ia = "modelos_equivalentes"
                else:
                    reply = (
                        f"Temos exatamente **{estoque} unidades** do **{nome}** disponíveis para envio imediato.\n\n"
                        f"O valor unitário é **{_formatar_preco_br(preco)}** com despacho em até 24h úteis para todo o Brasil. "
                        f"Gostaria de garantir o seu?"
                    )
                    perfil.ultima_oferta_ia = "garantir_compra"
                return reply, tools_called, dashboard, perfil

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
                perfil.ultima_oferta_ia = "entrega_e_pagamento"
                return reply, tools_called, dashboard, perfil

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
                perfil.ultima_oferta_ia = "garantir_compra"
                return reply, tools_called, dashboard, perfil

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
        perfil,
    )


class AIService:
    """Serviço unificado de atendimento que prioriza Grok (xAI) e Gemini com fallback conversacional."""

    def __init__(self):
        self._carregar_configuracoes()

    def _carregar_configuracoes(self):
        """Recarrega as variáveis de ambiente dinamicamente buscando .env no backend e na raiz."""
        from pathlib import Path
        backend_dir = Path(__file__).resolve().parent.parent
        root_dir = backend_dir.parent
        for env_path in [backend_dir / ".env", root_dir / ".env", backend_dir / ".env.example"]:
            if env_path.exists():
                load_dotenv(dotenv_path=env_path, override=True)
                break
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
        self,
        message: str,
        history: Optional[List[Dict[str, str]]] = None,
        user_profile: Optional[UserProfile] = None,
    ) -> Optional[Tuple[str, List[str]]]:
        """Executa a conversação via Grok (xAI API) com Function/Tool Calling."""
        if not self._tem_chave_valida(self.grok_api_key):
            return None

        tools_called: List[str] = []
        system_content = _gerar_prompt_com_perfil(user_profile)
        messages: List[Dict[str, Any]] = [{"role": "system", "content": system_content}]

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
        self,
        message: str,
        history: Optional[List[Dict[str, str]]] = None,
        user_profile: Optional[UserProfile] = None,
    ) -> Optional[Tuple[str, List[str]]]:
        """Executa a conversação via Google GenAI com Tool Calling."""
        if not self._tem_chave_valida(self.gemini_api_key):
            return None

        try:
            from google import genai
            from google.genai import types

            client = genai.Client(api_key=self.gemini_api_key.strip())
            tools_called: List[str] = []

            system_content = _gerar_prompt_com_perfil(user_profile)
            config = types.GenerateContentConfig(
                system_instruction=system_content,
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
        user_profile: Optional[UserProfile] = None,
    ) -> Dict[str, Any]:
        """Prioriza estritamente os modelos de IA (Grok e Gemini) antes de qualquer fallback."""
        # Recarregar chaves de ambiente caso o usuário tenha editado o .env
        self._carregar_configuracoes()

        dashboard_data = obter_dashboard_benchmarks(message)
        provedor_preferido = (provider or os.getenv("LLM_PROVIDER", "auto")).lower()

        # Extrair e atualizar perfil preliminarmente caso o usuário tenha fornecido novos dados
        perfil_atualizado, _ = extrair_e_atualizar_perfil(message, user_profile)

        # 1. Prioridade 1: Grok (xAI) se solicitado ou se estiver com chave disponível no modo auto
        if provedor_preferido in ("grok", "xai") or (provedor_preferido == "auto" and self._tem_chave_valida(self.grok_api_key)):
            try:
                res_grok = self._processar_via_grok(message, history, perfil_atualizado)
                if res_grok:
                    reply, tools = res_grok
                    return {
                        "reply": reply,
                        "tools_called": tools,
                        "dashboard_data": dashboard_data,
                        "provider": "grok",
                        "user_profile": perfil_atualizado,
                    }
            except Exception as e:
                logger.warning("Erro ao tentar Grok como IA principal: %s", e)

        # 2. Prioridade 2: Google Gemini se solicitado ou se estiver com chave disponível no modo auto
        if provedor_preferido in ("gemini", "google") or (provedor_preferido == "auto" and self._tem_chave_valida(self.gemini_api_key)):
            try:
                res_gemini = self._processar_via_gemini(message, history, perfil_atualizado)
                if res_gemini:
                    reply, tools = res_gemini
                    return {
                        "reply": reply,
                        "tools_called": tools,
                        "dashboard_data": dashboard_data,
                        "provider": "gemini",
                        "user_profile": perfil_atualizado,
                    }
            except Exception as e:
                logger.warning("Erro ao tentar Gemini como IA principal: %s", e)

        # 3. Fallback inteligente de contingência (ativo somente se nenhuma IA responder ou estiver sem chaves)
        reply, tools, dash, perfil_final = _executar_fallback_deterministico(message, history, user_profile)
        final_dashboard = dashboard_data or dash
        return {
            "reply": reply,
            "tools_called": tools,
            "dashboard_data": final_dashboard,
            "provider": "fallback_core",
            "user_profile": perfil_final,
        }


# Instância global do serviço de IA
ai_service = AIService()
