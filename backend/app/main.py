"""Aplicação FastAPI da CORE Hardware.

Disponibiliza o endpoint de chat e CORS para comunicação com a SPA.
"""

import logging
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware

from app.ai_service import ai_service
from app.models import ChatRequest, ChatResponse

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("core-hardware")

app = FastAPI(
    title="CORE Hardware - API de Atendimento Inteligente",
    description="Backend oficial da CORE Hardware integrado ao catálogo de hardware e IA com Tool Calling.",
    version="1.0.0",
)

# Configuração de CORS para permitir acesso do frontend React/Vite
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def read_root():
    """Rota raiz para verificação de status da API."""
    return {
        "status": "online",
        "service": "CORE Hardware API",
        "docs": "/docs",
    }


@app.get("/api/health")
def health_check():
    """Health check endpoint para monitoramento de disponibilidade."""
    return {"status": "healthy"}


@app.post(
    "/api/chat",
    response_model=ChatResponse,
    status_code=status.HTTP_200_OK,
    summary="Atendimento conversacional inteligente",
    description="Processa mensagens de clientes, consulta o estoque via Tool Calling e retorna a resposta formatada.",
)
def chat_endpoint(request: ChatRequest) -> ChatResponse:
    """Endpoint principal de chat da CORE Hardware."""
    try:
        # Converter histórico para formato dict compatível
        history_dicts = [msg.model_dump() for msg in (request.history or [])]

        resultado = ai_service.processar_mensagem(
            message=request.message,
            history=history_dicts,
        )

        return ChatResponse(
            reply=resultado["reply"],
            tools_called=resultado.get("tools_called", []),
        )
    except Exception as exc:
        logger.error("Erro interno ao processar chat: %s", exc, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao processar atendimento: {str(exc)}",
        )
