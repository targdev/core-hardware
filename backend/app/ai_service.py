"""Serviço de Inteligência Artificial integrado ao Google Gemini com Tool Calling.

Configura ferramentas de consulta de estoque, system prompt oficial da
CORE Hardware e fallback determinístico inteligente para resiliência total.
"""

import logging
import os
import re
from typing import Any, Dict, List, Optional, Tuple

from dotenv import load_dotenv

from app.inventory import (
    CATALOGO_PRODUTOS,
    consultar_estoque,
    listar_produtos,
)

load_dotenv()
logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """Você é o Assistente Virtual Oficial da CORE Hardware, uma loja especializada em computadores, notebooks e periféricos de alta performance.

Suas diretrizes fundamentais:
1. NUNCA invente ou alucine informações sobre estoque, quantidades disponíveis, preços ou especificações técnicas de produtos.
2. SEMPRE consulte as ferramentas disponíveis (`consultar_estoque` ou `listar_produtos`) antes de responder a qualquer pergunta sobre produtos, disponibilidade ou preços.
3. Se o produto estiver com estoque zerado (como o Lenovo Legion Pro 5), informe educadamente que ele está esgotado (0 unidades em estoque) e mencione o preço de referência.
4. Mantenha um tom profissional, moderno, tecnológico e prestativo.
5. Formate os preços em Reais (R$).
6. Responda de forma direta e concisa às perguntas dos clientes.
"""

TOOL_MAP = {
    "consultar_estoque": consultar_estoque,
    "listar_produtos": listar_produtos,
}


def _executar_fallback_deterministico(
    message: str, history: Optional[List[Dict[str, str]]] = None
) -> Tuple[str, List[str]]:
    """Fallback inteligente para responder a perguntas de clientes sobre hardware

    mesmo quando a chave da API do Gemini não estiver configurada ou houver falha de rede.
    """
    msg_lower = message.lower().strip()
    tools_called: List[str] = []

    # Detectar saudações puras
    saudacoes = ["ola", "olá", "oi", "bom dia", "boa tarde", "boa noite", "hey", "hello"]
    if msg_lower in saudacoes or any(msg_lower.startswith(s) and len(msg_lower) <= len(s) + 4 for s in saudacoes):
        return (
            "Olá! Seja bem-vindo à CORE Hardware. Sou o assistente virtual especializado em hardware e periféricos de alta performance. "
            "Como posso ajudar você hoje com notebooks, periféricos, monitores ou placas de vídeo?",
            [],
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
        return "\n".join(linhas), tools_called

    # Detectar categorias
    if "notebook" in msg_lower or "laptops" in msg_lower or "laptop" in msg_lower:
        # Se for uma pergunta ampla sobre notebooks e não sobre modelo específico
        if not any(k in msg_lower for k in ["macbook", "xps", "legion", "lenovo", "dell"]):
            tools_called.append("listar_produtos")
            notebooks = listar_produtos("Notebooks")
            linhas = ["Temos os seguintes notebooks em nosso catálogo:\n"]
            for p in notebooks:
                status_txt = f"{p['estoque']} unidades disponíveis" if p["estoque"] > 0 else "Esgotado (0 un)"
                linhas.append(
                    f"- **{p['nome']}**: {p['especificacoes']} - R$ {p['preco']:,.2f} ({status_txt})"
                )
            return "\n".join(linhas), tools_called

    if "periferico" in msg_lower or "periférico" in msg_lower:
        tools_called.append("listar_produtos")
        perifs = listar_produtos("Periféricos")
        linhas = ["Estes são os periféricos disponíveis na CORE Hardware:\n"]
        for p in perifs:
            linhas.append(
                f"- **{p['nome']}**: R$ {p['preco']:,.2f} (Estoque: {p['estoque']} unidades)"
            )
        return "\n".join(linhas), tools_called

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
            return reply, tools_called

    # Se não identificou termo direto conhecido, tenta buscar com termos da mensagem
    # excluindo stop words
    stop_words = {"tem", "temos", "voces", "vocês", "quantos", "qual", "preco", "preço", "estoque", "de", "o", "a", "os", "as", "em", "para"}
    palavras = [p for p in re.findall(r"\w+", msg_lower) if p not in stop_words and len(p) > 2]
    for pal in palavras:
        res = consultar_estoque(pal)
        if res.get("encontrado"):
            tools_called.append("consultar_estoque")
            nome = res["nome"]
            estoque = res["estoque"]
            preco = res["preco"]
            specs = res["especificacoes"]
            if estoque == 0:
                return (
                    f"O produto **{nome}** ({specs}) está atualmente **esgotado** (0 unidades em estoque). "
                    f"Preço de referência: R$ {preco:,.2f}.",
                    tools_called,
                )
            return (
                f"Temos o **{nome}** ({specs}) em estoque com **{estoque} unidades** disponíveis por R$ {preco:,.2f} cada.",
                tools_called,
            )

    # Caso não seja um produto conhecido ou encontrado
    tools_called.append("consultar_estoque")
    return (
        "Desculpe, não encontrei esse item em nosso catálogo da CORE Hardware. "
        "Nosso catálogo inclui notebooks de alta performance (MacBook M3, Dell XPS, Lenovo Legion), "
        "periféricos premium (Logitech MX Master 3S, Keychron K2 Pro), Monitores 4K e GPUs RTX. "
        "Gostaria de consultar algum desses?",
        tools_called,
    )


class AIService:
    """Serviço de atendimento automatizado via IA para a CORE Hardware."""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        self._client = None
        self._init_client()

    def _init_client(self):
        """Inicializa o cliente do Gemini se a chave for válida."""
        if self.api_key and self.api_key.strip() and not self.api_key.startswith("sua_chave"):
            try:
                from google import genai
                self._client = genai.Client(api_key=self.api_key.strip())
            except Exception as e:
                logger.warning("Falha ao inicializar cliente Google GenAI: %s", e)
                self._client = None
        else:
            self._client = None

    def processar_mensagem(
        self, message: str, history: Optional[List[Dict[str, str]]] = None
    ) -> Dict[str, Any]:
        """Processa a mensagem do usuário usando o Gemini com Tool Calling,

        ou utiliza o fallback inteligente caso a API não esteja acessível.
        """
        # Se não houver cliente configurado, usar fallback determinístico imediatamente
        if not self._client:
            reply, tools_called = _executar_fallback_deterministico(message, history)
            return {"reply": reply, "tools_called": tools_called}

        try:
            from google.genai import types

            tools_called: List[str] = []

            # 1. Configurar as ferramentas disponíveis
            config = types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT,
                tools=[consultar_estoque, listar_produtos],
                temperature=0.2,
            )

            # Montar histórico de conteúdo se existir
            contents: List[Any] = []
            if history:
                for h in history:
                    role = "user" if h.get("role") == "user" else "model"
                    contents.append(
                        types.Content(
                            role=role,
                            parts=[types.Part.from_text(text=h.get("content", ""))],
                        )
                    )
            contents.append(types.Content(role="user", parts=[types.Part.from_text(text=message)]))

            # Chamada ao modelo Gemini 2.5 Flash
            model_name = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
            response = self._client.models.generate_content(
                model=model_name,
                contents=contents,
                config=config,
            )

            # Verificar se o modelo solicitou chamadas de ferramenta
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
                # Executar as ferramentas e montar resposta das funções
                tool_results_parts = []
                for call in function_calls:
                    fn_name = call.name
                    fn_args = dict(call.args) if call.args else {}
                    tools_called.append(fn_name)

                    fn = TOOL_MAP.get(fn_name)
                    if fn:
                        try:
                            result = fn(**fn_args)
                        except Exception as e:
                            result = {"erro": str(e)}
                    else:
                        result = {"erro": f"Ferramenta '{fn_name}' não encontrada"}

                    tool_results_parts.append(
                        types.Part.from_function_response(
                            name=fn_name,
                            response={"result": result},
                        )
                    )

                # Segunda chamada para gerar a resposta final com o resultado das ferramentas
                contents.append(response.candidates[0].content)
                contents.append(types.Content(role="user", parts=tool_results_parts))

                final_response = self._client.models.generate_content(
                    model=model_name,
                    contents=contents,
                    config=config,
                )
                reply_text = final_response.text or "Informações de estoque consultadas com sucesso."
                return {"reply": reply_text, "tools_called": tools_called}

            reply_text = response.text or "Olá, como posso ajudar com os produtos da CORE Hardware?"
            return {"reply": reply_text, "tools_called": tools_called}

        except Exception as e:
            logger.warning("Exceção ao chamar Google Gemini API (%s). Ativando fallback determinístico.", e)
            reply, tools_called = _executar_fallback_deterministico(message, history)
            return {"reply": reply, "tools_called": tools_called}


# Instância global do serviço de IA
ai_service = AIService()
