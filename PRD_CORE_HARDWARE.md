# Documento de Requisitos de Produto (PRD) & Engenharia

**Projeto:** CORE Hardware - Chatbot Inteligente de Atendimento & Estoque  
**Natureza:** Desafio Técnico de Engenharia de Software  
**Arquitetura:** Monorepo Enxuto (Backend Python FastAPI + Frontend React/Vite Chat SPA + Google Gemini / Groq API com Tool Calling)  
**Catálogo:** Computadores, Notebooks e Periféricos de Alta Performance  

---

## 1. SPEC (Especificação Funcional e Técnica)

### 1.1. Objetivo
Criar um assistente conversacional para a **CORE Hardware** capaz de responder a dúvidas de clientes em linguagem natural sobre disponibilidade, estoque e especificações técnicas de produtos ("Tem o produto X?", "Tem quantos em estoque?"), garantindo que as respostas venham de uma IA integrada via API Key e consultem uma base de dados real de estoque via **Function/Tool Calling**.

### 1.2. Catálogo Oficial de Hardware (Módulo de Estoque)
Base estruturada em Python (`app/inventory.py`) com produtos ativos, esgotados e variações:

| ID | Nome do Produto | Categoria | Especificações | Preço | Estoque |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `NOTE-01` | **MacBook Air 15" M3** | Notebooks | Chip Apple M3, 16GB RAM, 512GB SSD, Cinza-espacial | R$ 11.999 | **4 unidades** |
| `NOTE-02` | **Dell XPS 13 Plus** | Notebooks | Intel Core i7 13ª Ger, 32GB RAM, 1TB SSD, Tela 3.5K OLED | R$ 10.850 | **2 unidades** |
| `NOTE-03` | **Lenovo Legion Pro 5** | Notebooks | AMD Ryzen 7 7745HX, RTX 4070 8GB, 32GB RAM, 1TB SSD | R$ 9.400 | **0 unidades (Esgotado)** |
| `PERIF-01` | **Mouse Logitech MX Master 3S** | Periféricos | Sensor 8K DPI, Conexão Bluetooth/Logi Bolt, Grafite | R$ 650 | **11 unidades** |
| `PERIF-02` | **Teclado Keychron K2 Pro** | Periféricos | Switch Red, Layout 75%, Hot-swappable, Conexão Sem Fio | R$ 780 | **6 unidades** |
| `MON-01` | **Monitor Dell UltraSharp 27" 4K** | Monitores | Painel IPS Black (U2723QE), 4K UHD, Hub USB-C 90W | R$ 3.790 | **5 unidades** |
| `GPU-01` | **Nvidia GeForce RTX 4060 Ti 8GB** | Hardware | 8GB GDDR6, Dual Fan, Ray Tracing, DLSS 3 | R$ 2.650 | **3 unidades** |

### 1.3. Contratos de API e Ferramentas (Tool Calling)

#### Ferramentas expostas para o LLM:
1. `consultar_estoque(nome_ou_termo: str)`: Retorna se o item existe, a quantidade exata em estoque, o preço e as especificações.
2. `listar_produtos(categoria: Optional[str] = None)`: Retorna a lista de produtos disponíveis em uma categoria (ou todo o catálogo).

#### Endpoint do Backend (`POST /api/chat`):
* **Payload de Entrada:**
  ```json
  {
    "message": "Vocês têm o MacBook Air M3? Tem quantos?",
    "history": [
      { "role": "user", "content": "Olá" },
      { "role": "assistant", "content": "Olá! Bem-vindo à CORE Hardware. Como posso ajudar você hoje?" }
    ]
  }
  ```
* **Payload de Saída:**
  ```json
  {
    "reply": "Sim! Temos o MacBook Air 15\" M3 (16GB RAM, 512GB SSD) disponível. Atualmente temos 4 unidades em estoque pelo valor de R$ 11.999,00 cada.",
    "tools_called": ["consultar_estoque"]
  }
  ```

---

## 2. Testes Unitários em Python (Obrigatórios do Desafio)

Os testes são executados com **`pytest`** cobrindo tanto as regras de negócio de estoque quanto o endpoint da aplicação.

### 2.1. Teste 1: `tests/test_inventory.py` (Lógica de Estoque e Busca)
* **Cenário A (Produto Existente em Estoque):** Consulta por termo exato ou parcial ("MacBook", "MX Master 3S") deve retornar status disponível e quantidade maior que 0.
* **Cenário B (Produto Esgotado):** Consulta por "Legion Pro 5" deve retornar estoque zero (`stock == 0`), permitindo que a IA informe com precisão que está esgotado.
* **Cenário C (Produto Inexistente):** Consulta por produto inexistente ("PlayStation 5") deve retornar lista vazia ou indicador de não encontrado sem estourar exceção.

### 2.2. Teste 2: `tests/test_chat_api.py` (Integração HTTP / FastAPI)
* Utiliza o `fastapi.testclient.TestClient`.
* Faz mock da chamada externa do LLM (garantindo que os testes rodem em CI/CD sem gastar cota nem depender da rede).
* Valida status code `200 OK`, estrutura de resposta JSON (`{"reply": str}`) e rejeição de payloads inválidos com `422 Unprocessable Entity`.

---

## 3. Estrutura do Repositório

```text
core-hardware-bot/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py              # FastAPI app, CORS e rota POST /api/chat
│   │   ├── inventory.py         # Catálogo de hardware e funções de busca
│   │   ├── ai_service.py        # Integração Gemini SDK com Tool Calling
│   │   └── models.py            # Schemas Pydantic (ChatRequest, ChatResponse)
│   ├── tests/
│   │   ├── __init__.py
│   │   ├── test_inventory.py    # Teste Unitário 1 (Estoque / Busca)
│   │   └── test_chat_api.py     # Teste Unitário 2 (Endpoint /api/chat)
│   ├── requirements.txt         # fastapi, uvicorn, google-genai, pytest, httpx, python-dotenv
│   └── .env.example
├── frontend/                    # Interface de Chat limpa, moderna e responsiva
│   ├── src/
│   │   ├── App.tsx              # Componente de chat com sugestões rápidas
│   │   ├── index.css            # Estilização moderna e refinada
│   │   └── main.tsx
│   ├── package.json
│   └── vite.config.ts
├── .gitignore
└── README.md                    # Instruções claras de setup, execução e testes
```

---

## 4. Estrutura de Git, Fluxo Multi-Dev e Branches no ORCA

Para evidenciar organização de engenharia em equipe, o desenvolvimento será focado em branches atômicas e rastreadas:

### 4.1. Topologia de Branches
```text
main (produção / estável)
  ▲
  │ (Pull Request / Merge com testes verdes)
  │
feature/CORE-10-hardware-bot
  ▲
  ├── task/CORE-01-backend-inventory-and-tests
  ├── task/CORE-02-ai-gemini-tool-calling
  ├── task/CORE-03-fastapi-chat-endpoint
  ├── task/CORE-04-frontend-chat-ui
  └── task/CORE-05-readme-documentation
```

### 4.2. Mapeamento das Tasks
* **`task/CORE-01-backend-inventory-and-tests`:** Implementação do catálogo de hardware (`inventory.py`) e criação do teste unitário `tests/test_inventory.py` via TDD.
* **`task/CORE-02-ai-gemini-tool-calling`:** Implementação do serviço de IA (`ai_service.py`) acoplando as funções de inventário ao Gemini Tool Calling.
* **`task/CORE-03-fastapi-chat-endpoint`:** Criação da API FastAPI (`main.py`), CORS, schemas Pydantic e o segundo teste unitário (`tests/test_chat_api.py`).
* **`task/CORE-04-frontend-chat-ui`:** Desenvolvimento da interface de chat com design clean, responsivo e botões de atalho ("Tem MacBook Air?", "Quantos monitores têm?").
* **`task/CORE-05-readme-documentation`:** Criação do `README.md` objetivo, contendo instruções em 3 passos para rodar o backend, os 2 testes em Python e o frontend.

### 4.3. Padrão de Commits Semânticos
* `feat(inventory): [CORE-01] add hardware products and stock lookup logic`
* `test(inventory): [CORE-01] add unit test for stock quantity and out-of-stock cases`
* `feat(ai): [CORE-02] implement gemini tool calling for inventory query`
* `feat(api): [CORE-03] create /api/chat endpoint with pydantic validation`
* `test(api): [CORE-03] add testclient integration test for chat route`
* `feat(ui): [CORE-04] build sleek hardware store chat interface`
* `docs: [CORE-05] add comprehensive README with python test instructions`

---

## 5. README Padrão de Entrega (Checklist de Avaliação)

O arquivo `README.md` final deve ser direto e focado no avaliador:
1. **Pré-requisitos:** Python 3.10+ e Node.js 18+.
2. **Backend e Testes:**
   ```bash
   cd backend
   pip install -r requirements.txt
   pytest  # Executa os 2 testes obrigatórios em Python
   uvicorn app.main:app --reload --port 8000
   ```
3. **Frontend:**
   ```bash
   cd frontend
   npm install
   npm run dev
   ```
4. **Variáveis de Ambiente:** Instruções simples para criar o `.env` no backend com `GEMINI_API_KEY`.