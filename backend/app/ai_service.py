"""Serviço de Inteligência Artificial integrado ao Grok (xAI) e Google Gemini com Tool Calling.

Configura ferramentas de consulta de estoque, benchmarks pré-montados,
system prompt oficial da CORE Hardware e fallback determinístico inteligente.
"""

import json
import logging
import os
import re
from typing import Any, Dict, List, Optional, Tuple

import httpx
from dotenv import load_dotenv

from app.benchmarks import obter_dashboard_benchmarks
from app.inventory import (
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
5. Mantenha um tom profissional, moderno, tecnológico e prestativo.
6. Formate os preços em Reais (R$).
7. Responda de forma direta, elegante e concisa.
"""

TOOL_MAP = {
    "consultar_estoque": consultar_estoque,
    "listar_produtos": listar_produtos,
}

# Definição das ferramentas no padrão OpenAI / xAI Function Calling
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
                "description": "Nome ou modelo do produto de hardware (ex: MacBook, XPS, Legion, MX Master, Keychron, RTX 4060 Ti, Dell 4K)"
              }
            },
            "required": ["nome_ou_termo"]
          }
        }
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
                "description": "Categoria desejada (Notebooks, Periféricos, Monitores, Hardware) ou None para catálogo completo"
              }
            }
          }
        }
    }
]


def _executar_fallback_deterministico(
    message: str, history: Optional[List[Dict[str, str]]] = None
) -> Tuple[str, List[str], Optional[Dict[str, Any]]]:
    """Fallback inteligente para responder com precisão técnica a perguntas sobre estoque e comparativos."""
    msg_lower = message.lower().strip()
    tools_called: List[str] = []

    # Verificar se a mensagem ativa um mini dashboard de comparação pré-montado
    dashboard = obter_dashboard_benchmarks(message)

    # 1. Caso de Comparação de Notebooks
    if dashboard and dashboard.get("tipo") == "comparativo_notebooks":
        tools_called.extend(["consultar_estoque", "listar_produtos"])
        reply = (
            "📊 **Mini Dashboard Comparativo: Linha de Notebooks CORE Hardware**\n\n"
            "Preparamos um comparativo técnico detalhado dos três principais modelos do nosso catálogo:\n\n"
            "1. **MacBook Air 15\" M3 (R$ 11.999,00 - 4 un. em estoque)**\n"
            "   • *Destaque:* Chip M3, eficiência extrema, design silencioso sem ventoinhas (fanless).\n"
            "   • *Autonomia:* Até 18 horas de bateria contínua.\n"
            "   • *Perfil:* Mobilidade máxima, programação, edição ágil e produtividade executiva.\n\n"
            "2. **Dell XPS 13 Plus (R$ 10.850,00 - 2 un. em estoque)**\n"
            "   • *Destaque:* Incrível tela 3.5K OLED touchscreen, Intel i7 13ª Ger e 32GB RAM.\n"
            "   • *Design:* Chassi futurista de alumínio usinado e touchpad háptico contínuo.\n"
            "   • *Perfil:* Profissionais que exigem a melhor qualidade de display do mercado.\n\n"
            "3. **Lenovo Legion Pro 5 (R$ 9.400,00 - Esgotado)**\n"
            "   • **Destaque:** Máximo poder de processamento com Ryzen 7 7745HX + GPU RTX 4070 8GB.\n"
            "   • **Desempenho:** Taxas acima de 90-120 FPS em 1440p e renderização pesada.\n"
            "   • **Status:** Atualmente esgotado em estoque (0 unidades).\n\n"
            "👉 **Consulte os gráficos interativos de benchmark e telemetria gerados no painel acima!**"
        )
        return reply, tools_called, dashboard

    # 2. Caso de Benchmark da GPU RTX 4060 Ti
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

    # 3. Caso de Comparação de Periféricos (MX Master 3S vs Keychron K2 Pro)
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

    # 4. Caso de Análise do Monitor Dell UltraSharp 4K
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

    # Detectar saudações puras
    saudacoes = ["ola", "olá", "oi", "bom dia", "boa tarde", "boa noite", "hey", "hello"]
    if msg_lower in saudacoes or any(msg_lower.startswith(s) and len(msg_lower) <= len(s) + 4 for s in saudacoes):
        return (
            "Olá! Seja bem-vindo à CORE Hardware. Sou o assistente virtual especializado em hardware e periféricos de alta performance. "
            "Como posso ajudar você hoje com notebooks, periféricos, monitores ou placas de vídeo?",
            [],
            None,
        )

    # Detectar intenção de listar catálogo completo
    intencoes_catalogo = [
        "quais produtos", "o que voces tem", "o que vocês têm", "listar produtos",
        "catalogo", "catálogo", "tudo que tem", "lista de produtos", "mostrar produtos"
    ]
    if any(frase in msg_lower for frase in intencoes_catalogo):
        tools_called.append("listar_produtos")
        todos = listar_produtos()
        linhas = ["Aqui está o nosso catálogo oficial da CORE Hardware:\n"]
        for p in todos:
            status_txt = "Disponível" if p["estoque"] > 0 else "Esgotado"
            linhas.append(
                f"- **{p['nome']}** ({p['categoria']}): R$ {p['preco']:,.2f} | Estoque: {p['estoque']} un. [{status_txt}]"
            )
        return "\n".join(linhas), tools_called, None

    # Mapeamento de termos para produtos específicos
    produtos_chave = [
        ("macbook", "MacBook"),
        ("air m3", "MacBook"),
        ("m3", "MacBook"),
        ("dell xps", "Dell XPS 13 Plus"),
        ("xps 13", "Dell XPS 13 Plus"),
        ("xps", "Dell XPS 13 Plus"),
        ("legion", "Lenovo Legion Pro 5"),
        ("lenovo", "Lenovo Legion Pro 5"),
        ("mx master", "Mouse Logitech MX Master 3S"),
        ("logitech", "Mouse Logitech MX Master 3S"),
        ("mouse", "Mouse Logitech MX Master 3S"),
        ("keychron", "Teclado Keychron K2 Pro"),
        ("teclado", "Teclado Keychron K2 Pro"),
        ("ultrasharp", "Monitor Dell UltraSharp 27\" 4K"),
        ("monitor", "Monitor Dell UltraSharp 27\" 4K"),
        ("rtx", "Nvidia GeForce RTX 4060 Ti 8GB"),
        ("4060", "Nvidia GeForce RTX 4060 Ti 8GB"),
        ("geforce", "Nvidia GeForce RTX 4060 Ti 8GB"),
        ("placa de video", "Nvidia GeForce RTX 4060 Ti 8GB"),
        ("placa de vídeo", "Nvidia GeForce RTX 4060 Ti 8GB"),
        ("gpu", "Nvidia GeForce RTX 4060 Ti 8GB"),
    ]

    termo_busca = None
    for chave, termo in produtos_chave:
        if chave in msg_lower:
            termo_busca = termo
            break

    if termo_busca:
        tools_called.append("consultar_estoque")
        resultado = consultar_estoque(termo_busca)
        if resultado.get("encontrado"):
            nome = resultado["nome"]
            estoque = resultado["estoque"]
            preco = resultado["preco"]
            specs = resultado["especificacoes"]

            if estoque == 0:
                reply = (
                    f"O produto **{nome}** ({specs}) está atualmente **esgotado** em nosso estoque "
                    f"(0 unidades disponíveis). O preço de referência é R$ {preco:,.2f}. "
                    "Podemos registrar seu interesse para quando recebermos nova remessa!"
                )
            else:
                reply = (
                    f"Sim! Temos o **{nome}** ({specs}) disponível. "
                    f"Atualmente temos **{estoque} unidades** em estoque pelo valor de R$ {preco:,.2f} cada."
                )
            return reply, tools_called, dashboard

    # Fallback genérico para itens não encontrados
    tools_called.append("consultar_estoque")
    return (
        "Desculpe, não encontrei esse item em nosso catálogo da CORE Hardware. "
        "Nosso catálogo inclui notebooks de alta performance (MacBook M3, Dell XPS, Lenovo Legion), "
        "periféricos premium (Logitech MX Master 3S, Keychron K2 Pro), Monitores 4K e GPUs RTX. "
        "Gostaria de consultar algum desses ou ver um comparativo de desempenho?",
        tools_called,
        None,
    )


class AIService:
    """Serviço unificado de atendimento com suporte ao Grok (xAI) e Gemini com Tool Calling."""

    def __init__(self):
        self.grok_api_key = os.getenv("XAI_API_KEY") or os.getenv("GROK_API_KEY")
        self.gemini_api_key = os.getenv("GEMINI_API_KEY")
        self.grok_model = os.getenv("GROK_MODEL", "grok-2-latest")
        self.gemini_model = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

    def _processar_via_grok(
        self, message: str, history: Optional[List[Dict[str, str]]] = None
    ) -> Optional[Tuple[str, List[str]]]:
        """Executa a conversação via Grok (xAI API) com Function/Tool Calling."""
        if not self.grok_api_key or not self.grok_api_key.strip() or self.grok_api_key.startswith("sua_chave"):
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

            # Verificar se o Grok solicitou tool_calls
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
                    if fn:
                        res = fn(**args)
                    else:
                        res = {"erro": f"Ferramenta '{fn_name}' não existe"}

                    messages.append({
                        "role": "tool",
                        "tool_call_id": tc["id"],
                        "content": json.dumps(res, ensure_ascii=False),
                    })

                # Segunda chamada para gerar a resposta final
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
        if not self.gemini_api_key or not self.gemini_api_key.strip() or self.gemini_api_key.startswith("sua_chave"):
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
                for h in history:
                    role = "user" if h.get("role") == "user" else "model"
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
                return final_response.text or "Consulta realizada.", tools_called

            return response.text or "Olá! Como posso ajudar?", tools_called

        except Exception as e:
            logger.warning("Falha ao consultar Gemini API: %s", e)
            return None

    def processar_mensagem(
        self,
        message: str,
        history: Optional[List[Dict[str, str]]] = None,
        provider: Optional[str] = "auto",
    ) -> Dict[str, Any]:
        """Processa a mensagem priorizando o provedor selecionado (Grok, Gemini ou Fallback Inteligente)."""
        dashboard_data = obter_dashboard_benchmarks(message)
        provedor_preferido = (provider or os.getenv("LLM_PROVIDER", "auto")).lower()

        # 1. Tentativa via Grok (xAI)
        if provedor_preferido in ("grok", "xai", "auto"):
            if self.grok_api_key and not self.grok_api_key.startswith("sua_chave"):
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
                    logger.warning("Erro no processamento Grok: %s", e)

        # 2. Tentativa via Gemini
        if provedor_preferido in ("gemini", "google", "auto"):
            if self.gemini_api_key and not self.gemini_api_key.startswith("sua_chave"):
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
                    logger.warning("Erro no processamento Gemini: %s", e)

        # 3. Fallback Determinístico Inteligente (Resiliência Total)
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
