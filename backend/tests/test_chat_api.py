"""Testes de integração HTTP para a API FastAPI com TestClient e mock de IA."""

from unittest.mock import patch
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_chat_api_success_with_mocked_ai():
    """Valida POST /api/chat com resposta 200 OK e estrutura esperada usando mock."""
    mocked_return = {
        "reply": 'Sim! Temos o MacBook Air 15" M3 disponível. Atualmente temos 4 unidades em estoque por R$ 11.999,00 cada.',
        "tools_called": ["consultar_estoque"],
    }

    with patch("app.main.ai_service.processar_mensagem", return_value=mocked_return) as mock_ai:
        payload = {
            "message": "Vocês têm o MacBook Air M3? Tem quantos?",
            "history": [
                {"role": "user", "content": "Olá"},
                {"role": "assistant", "content": "Olá! Bem-vindo à CORE Hardware."},
            ],
        }
        response = client.post("/api/chat", json=payload)

        assert response.status_code == 200
        data = response.json()
        assert "reply" in data
        assert isinstance(data["reply"], str)
        assert "MacBook Air" in data["reply"]
        assert data["tools_called"] == ["consultar_estoque"]

        # Verifica se o mock foi invocado com a mensagem correta
        mock_ai.assert_called_once()
        args, kwargs = mock_ai.call_args
        assert kwargs["message"] == "Vocês têm o MacBook Air M3? Tem quantos?"
        assert len(kwargs["history"]) == 2


def test_chat_api_fallback_integration_without_mock():
    """Valida o funcionamento do fallback local no endpoint quando sem API Key."""
    payload = {
        "message": "Vocês têm o MacBook Air M3?",
        "history": [],
    }
    response = client.post("/api/chat", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "reply" in data
    assert "tools_called" in data
    assert "MacBook" in data["reply"]
    assert "consultar_estoque" in data["tools_called"]


def test_chat_api_validation_error_empty_payload():
    """Valida que requisições vazias retornam 422 Unprocessable Entity."""
    response = client.post("/api/chat", json={})
    assert response.status_code == 422
    data = response.json()
    assert "detail" in data


def test_chat_api_validation_error_empty_message():
    """Valida que mensagens vazias retornam 422 Unprocessable Entity."""
    response = client.post("/api/chat", json={"message": ""})
    assert response.status_code == 422


def test_health_check_endpoint():
    """Valida o endpoint de verificação de integridade."""
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}
