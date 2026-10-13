"""Modelos Pydantic para validação e serialização de dados da API de Chat."""

from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    """Mensagem individual do histórico de conversas."""

    role: Literal["user", "assistant", "model", "system"] = Field(
        ..., description="Papel do remetente da mensagem"
    )
    content: str = Field(..., min_length=1, description="Conteúdo textual da mensagem")


class UserProfile(BaseModel):
    """Dados cadastrais e preferências identificadas do cliente."""

    nome: Optional[str] = Field(default=None, description="Nome do cliente")
    email: Optional[str] = Field(default=None, description="E-mail de contato")
    cidade: Optional[str] = Field(default=None, description="Cidade ou estado do cliente")
    marcas_favoritas: List[str] = Field(
        default_factory=list,
        description="Marcas de preferência (ex: Apple, Dell, Lenovo, Logitech, Keychron, Nvidia)",
    )
    interesses: List[str] = Field(
        default_factory=list,
        description="Áreas de interesse e foco de uso (ex: Programação, Games, Produtividade)",
    )
    ultimo_produto_id: Optional[str] = Field(
        default=None,
        description="ID do último produto consultado ou em discussão (ex: NOTE-01)",
    )
    ultimo_produto_nome: Optional[str] = Field(
        default=None,
        description="Nome do último produto consultado ou em discussão (ex: MacBook Air 15\" M3)",
    )
    ultima_oferta_ia: Optional[str] = Field(
        default=None,
        description="Última sugestão ou pergunta feita pelo assistente (ex: comparativo_ou_specs, entrega_e_pagamento)",
    )
    notas: List[str] = Field(
        default_factory=list,
        description="Outras preferências e dados capturados durante o atendimento",
    )


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
    provider: Optional[str] = Field(
        default="auto",
        description="Provedor de IA desejado: 'grok', 'gemini' ou 'auto'",
    )
    user_profile: Optional[UserProfile] = Field(
        default=None,
        description="Perfil e preferências do cliente previamente salvos",
    )


class ChatResponse(BaseModel):
    """Payload de saída do endpoint de chat com dados de dashboard e perfil do cliente."""

    reply: str = Field(
        ...,
        description="Resposta gerada pelo assistente inteligente da CORE Hardware",
    )
    tools_called: List[str] = Field(
        default_factory=list,
        description="Lista de ferramentas de estoque invocadas pelo modelo",
        examples=[["consultar_estoque"]],
    )
    dashboard_data: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Dados de telemetria, benchmark e mini dashboard de comparação pré-montados",
    )
    provider: str = Field(
        default="fallback_core",
        description="Provedor de inteligência artificial que atendeu a requisição ('grok', 'gemini' ou 'fallback_core')",
    )
    user_profile: Optional[UserProfile] = Field(
        default=None,
        description="Perfil e preferências atualizados do cliente",
    )
