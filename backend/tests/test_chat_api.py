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


def test_procedural_dialog_follow_up_price():
    """Valida diálogo procedural: pergunta sobre preço usando pronome 'ele' com histórico."""
    payload = {
        "message": "E quanto custa ele?",
        "history": [
            {"role": "user", "content": "Vocês têm o MacBook Air M3?"},
            {"role": "assistant", "content": "Temos sim o MacBook Air 15\" M3 com 4 unidades disponíveis."},
        ],
    }
    response = client.post("/api/chat", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "MacBook Air" in data["reply"]
    assert "11.999" in data["reply"]
    assert "consultar_estoque" in data["tools_called"]


def test_procedural_dialog_follow_up_color():
    """Valida diálogo procedural: pergunta sobre cor e acabamento a partir do histórico."""
    payload = {
        "message": "Qual a cor dele?",
        "history": [
            {"role": "user", "content": "Tem o Dell XPS 13 Plus?"},
            {"role": "assistant", "content": "Temos 2 unidades do Dell XPS 13 Plus em estoque."},
        ],
    }
    response = client.post("/api/chat", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "Dell XPS 13" in data["reply"]
    assert "Grafite" in data["reply"] or "Platina" in data["reply"] or "alumínio" in data["reply"].lower()
    assert "consultar_estoque" in data["tools_called"]


def test_procedural_dialog_follow_up_battery():
    """Valida diálogo procedural: pergunta sobre autonomia de bateria a partir do histórico."""
    payload = {
        "message": "E quanto dura a bateria dele?",
        "history": [
            {"role": "user", "content": "Me fale sobre o MacBook Air M3"},
            {"role": "assistant", "content": "O MacBook Air M3 tem chip Apple M3 e 16GB RAM."},
        ],
    }
    response = client.post("/api/chat", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "MacBook Air" in data["reply"]
    assert "18 horas" in data["reply"]
    assert "consultar_estoque" in data["tools_called"]


def test_procedural_dialog_follow_up_warranty():
    """Valida diálogo procedural: pergunta sobre garantia oficial a partir do histórico."""
    payload = {
        "message": "Tem garantia?",
        "history": [
            {"role": "user", "content": "Tem o Teclado Keychron K2 Pro?"},
            {"role": "assistant", "content": "Sim! O Teclado Keychron K2 Pro custa R$ 780,00."},
        ],
    }
    response = client.post("/api/chat", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "Keychron K2 Pro" in data["reply"]
    assert "12 meses" in data["reply"]
    assert "nota fiscal" in data["reply"].lower()
    assert "consultar_estoque" in data["tools_called"]


def test_user_profile_introduction_greeting():
    """Valida identificação do nome do usuário e persistência no perfil."""
    payload = {
        "message": "Meu nome é Tarcísio",
        "history": [],
    }
    response = client.post("/api/chat", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "Tarcísio" in data["reply"]
    assert "Muito prazer" in data["reply"] or "prazer" in data["reply"].lower()
    assert data["user_profile"] is not None
    assert data["user_profile"]["nome"] == "Tarcísio"


def test_user_profile_brand_preference_and_recommendation():
    """Valida captura de marcas favoritas e recomendação contextual."""
    payload = {
        "message": "Prefiro produtos da Apple",
        "history": [],
        "user_profile": {"nome": "Tarcísio", "marcas_favoritas": [], "interesses": []},
    }
    response = client.post("/api/chat", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "Apple" in data["reply"]
    assert "MacBook Air" in data["reply"]
    assert data["user_profile"] is not None
    assert "Apple" in data["user_profile"]["marcas_favoritas"]
    assert data["user_profile"]["nome"] == "Tarcísio"


def test_user_profile_interests_and_city():
    """Valida captura de interesse em programação e cidade."""
    payload = {
        "message": "Trabalho com programação e moro em Curitiba",
        "history": [],
        "user_profile": {"nome": "Tarcísio", "marcas_favoritas": ["Apple"], "interesses": []},
    }
    response = client.post("/api/chat", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["user_profile"] is not None
    assert data["user_profile"]["cidade"] == "Curitiba"
    assert "Programação & Desenvolvimento" in data["user_profile"]["interesses"]
    assert "Apple" in data["user_profile"]["marcas_favoritas"]


def test_user_profile_query_what_do_you_know_about_me():
    """Valida consulta das preferências e dados memorizados do usuário."""
    payload = {
        "message": "O que você sabe sobre mim?",
        "history": [],
        "user_profile": {
            "nome": "Tarcísio",
            "cidade": "Curitiba",
            "marcas_favoritas": ["Apple", "Logitech"],
            "interesses": ["Programação & Desenvolvimento"],
        },
    }
    response = client.post("/api/chat", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "Curitiba" in data["reply"]


def test_conversational_memory_affirmative_response_macbook():
    """Valida o caso exato da imagem: usuário responde 'Sim' à oferta de comparativo/specs."""
    payload = {
        "message": "Sim",
        "history": [
            {
                "role": "user",
                "content": "Vocês têm o MacBook Air M3? Tem quantos?",
            },
            {
                "role": "assistant",
                "content": (
                    'Com certeza! Temos o MacBook Air 15" M3 (Chip Apple M3, 16GB RAM, 512GB SSD, Cinza-espacial) disponível em nosso estoque.\n\n'
                    "• Quantidade disponível: 4 unidades • Preço unitário: R$ 11.999,00\n\n"
                    "Gostaria de tirar alguma dúvida sobre as especificações técnicas ou ver um comparativo?"
                ),
            },
        ],
    }
    response = client.post("/api/chat", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "Não localizei" not in data["reply"]
    assert "MacBook Air" in data["reply"]
    assert "Comparativo" in data["reply"] or "comparativo" in data["reply"] or "Especificações" in data["reply"]
    assert data["dashboard_data"] is not None
    assert data["dashboard_data"]["tipo"] == "comparativo_notebooks"
    assert data["user_profile"] is not None
    assert data["user_profile"]["ultimo_produto_id"] == "NOTE-01"


def test_conversational_memory_follow_up_without_history_using_profile():
    """Valida que o bot recupera o produto a partir do perfil persistente mesmo sem histórico."""
    payload = {
        "message": "Qual o preço dele?",
        "history": [],
        "user_profile": {
            "ultimo_produto_id": "NOTE-01",
            "ultimo_produto_nome": 'MacBook Air 15" M3',
            "marcas_favoritas": ["Apple"],
            "interesses": [],
        },
    }
    response = client.post("/api/chat", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "MacBook Air" in data["reply"]
    assert "11.999" in data["reply"]


def test_conversational_memory_polite_negation():
    """Valida que respostas como 'Não' ou 'Não precisa' são tratadas com cortesia."""
    payload = {
        "message": "Não precisa, obrigado",
        "history": [
            {
                "role": "user",
                "content": "Tem o Dell XPS 13 Plus?",
            },
            {
                "role": "assistant",
                "content": "Temos 2 unidades em estoque por R$ 10.850,00. Gostaria de tirar dúvidas ou ver comparativo?",
            },
        ],
    }
    response = client.post("/api/chat", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "Não localizei" not in data["reply"]
    assert "Sem problemas" in data["reply"] or "disposição" in data["reply"].lower()



