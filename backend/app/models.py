"""Modelos Pydantic para validação e serialização de dados da API de Chat."""

from typing import List, Literal, Optional
from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    """Mensagem individual do histórico de conversas."""

    role: Literal["user", "assistant", "model", "system"] = Field(
        ..., description="Papel do remetente da mensagem"
    )
    content: str = Field(..., min_length=1, description="Conteúdo textual da mensagem")


class ChatRequest(BaseModel):
    """Payload de entrada para o endpoint de chat."""

    message: str = Field(
        ...,
        min_length=1,
        description="Mensagem enviada pelo cliente",
        examples=["Vocês têm o MacBook Air M3? Tem quantos?"],
    )
    history: Optional[List[ChatMessage]] = Field(
        default_factory=list,
        description="Histórico anterior de mensagens para contexto da conversa",
    )


class ChatResponse(BaseModel):
    """Payload de saída do endpoint de chat."""

    reply: str = Field(
        ...,
        description="Resposta gerada pelo assistente inteligente da CORE Hardware",
    )
    tools_called: List[str] = Field(
        default_factory=list,
        description="Lista de ferramentas de estoque invocadas pelo modelo",
        examples=[["consultar_estoque"]],
    )
