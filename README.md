# CORE Hardware — Chatbot Inteligente de Atendimento & Estoque

Assistente conversacional oficial da **CORE Hardware** desenvolvido com arquitetura moderna full-stack para atender clientes com alta precisão técnica sobre computadores, notebooks de alto desempenho, placas de vídeo RTX, monitores 4K e periféricos.

O assistente integra as IAs **Grok (xAI)** e **Google Gemini** com **Tool / Function Calling**, garantindo que as respostas de disponibilidade, quantidades em estoque e valores monetários venham diretamente da base de dados oficial e não de alucinações. O sistema inclui **Mini Dashboards Gráficos de Comparação e Telemetria de Hardware** pré-montados e **Fallback Determinístico Inteligente** caso as chaves de API não estejam configuradas.

---

## 🛠️ Stack Tecnológica

- **Backend:** Python 3.10+, FastAPI, Uvicorn, Pydantic v2, Google GenAI SDK (`google-genai`), Pytest, HTTPX, python-dotenv.
- **Frontend:** React 18, TypeScript, Vite, Tailwind CSS, Lucide Icons (Design Dark Zinc / Titanium Hardware moderno com seletor de IA e badges de Tool Calling).
- **Inteligência Artificial:** 
  - **Grok (xAI):** Suporte nativo via `grok-2-latest` com Function Calling via OpenAI/xAI API schema.
  - **Google Gemini:** `gemini-2.5-flash` com Function Calling declarativo.
  - **CORE Engine (Fallback):** Mecanismo determinístico local com telemetria e estoque em tempo real.
- **Mini Dashboards Pré-Montados:**
  - Comparativo de Notebooks (MacBook Air M3 vs Dell XPS 13 Plus vs Lenovo Legion Pro 5).
  - Telemetria de GPU RTX 4060 Ti com taxas médias de quadros (FPS em Cyberpunk, Warzone, etc.).
  - Comparativo de Periféricos de Elite (Logitech MX Master 3S + Keychron K2 Pro).
  - Análise de Fidelidade de Cores e USB-C Hub do Monitor Dell UltraSharp 27" 4K.
- **Arquitetura de Testes:** Suíte automatizada com Pytest cobrindo regras de negócio de estoque, dashboards e testes de integração com `TestClient` e Mocks.

---

## 📦 Catálogo Oficial de Hardware

| ID | Produto | Categoria | Especificações Técnicas | Preço | Estoque |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `NOTE-01` | **MacBook Air 15" M3** | Notebooks | Chip Apple M3, 16GB RAM, 512GB SSD, Cinza-espacial | R$ 11.999,00 | **4 unidades** |
| `NOTE-02` | **Dell XPS 13 Plus** | Notebooks | Intel Core i7 13ª Ger, 32GB RAM, 1TB SSD, Tela 3.5K OLED | R$ 10.850,00 | **2 unidades** |
| `NOTE-03` | **Lenovo Legion Pro 5** | Notebooks | AMD Ryzen 7 7745HX, RTX 4070 8GB, 32GB RAM, 1TB SSD | R$ 9.400,00 | **0 un (Esgotado)** |
| `PERIF-01` | **Mouse Logitech MX Master 3S** | Periféricos | Sensor 8K DPI, Conexão Bluetooth/Logi Bolt, Grafite | R$ 650,00 | **11 unidades** |
| `PERIF-02` | **Teclado Keychron K2 Pro** | Periféricos | Switch Red, Layout 75%, Hot-swappable, Conexão Sem Fio | R$ 780,00 | **6 unidades** |
| `MON-01` | **Monitor Dell UltraSharp 27" 4K** | Monitores | Painel IPS Black (U2723QE), 4K UHD, Hub USB-C 90W | R$ 3.790,00 | **5 unidades** |
| `GPU-01` | **Nvidia GeForce RTX 4060 Ti 8GB** | Hardware | 8GB GDDR6, Dual Fan, Ray Tracing, DLSS 3 | R$ 2.650,00 | **3 unidades** |

---

## 📋 Pré-requisitos

- **Python:** 3.10 ou superior
- **Node.js:** 18.0 ou superior (e gerenciador `npm`)

---

## 🚀 Como Executar o Projeto

### 1. Backend & Testes (Python FastAPI)

1. Entre no diretório do backend:
   ```bash
   cd backend
   ```

2. Instale as dependências:
   ```bash
   pip install -r requirements.txt
   ```

3. Configure as variáveis de ambiente (Opcional):
   ```bash
   cp .env.example .env
   ```
   > **Nota de Resiliência:** Caso não informe `XAI_API_KEY` ou `GEMINI_API_KEY`, o sistema ativará automaticamente o **Fallback Determinístico Inteligente**, permitindo testar todas as consultas de estoque, comparativos e mini dashboards sem interrupções.

4. Execute a suíte de testes unitários e de integração:
   ```bash
   pytest
   ```

5. Inicie o servidor da API:
   ```bash
   uvicorn app.main:app --reload --port 8000
   ```
   A API estará acessível em `http://localhost:8000` (documentação interativa Swagger em `http://localhost:8000/docs`).

---

### 2. Frontend (React + TypeScript + Vite)

1. Em um novo terminal, entre no diretório do frontend:
   ```bash
   cd frontend
   ```

2. Instale as dependências:
   ```bash
   npm install
   ```

3. Inicie o servidor de desenvolvimento:
   ```bash
   npm run dev
   ```

4. Abra a aplicação no navegador em `http://localhost:3000` (ou endereço indicado no terminal).

---

## 🧪 Suíte de Testes Automatizados

A aplicação possui 3 arquivos de testes cobrindo todos os requisitos funcionais:

1. **`backend/tests/test_inventory.py`:**
   - **Cenário A:** Busca por produto existente (ex: "MacBook", "MX Master 3S") retornando disponibilidade e estoque > 0.
   - **Cenário B:** Busca por produto esgotado ("Lenovo Legion Pro 5") retornando `estoque == 0` e status esgotado.
   - **Cenário C:** Busca por produto inexistente ("PlayStation 5") retornando não encontrado sem levantar exceções.
   - **Listagem por Categoria:** Filtros de catálogo por categoria e listagem completa.

2. **`backend/tests/test_chat_api.py`:**
   - Teste de integração HTTP com `fastapi.testclient.TestClient`.
   - Mock da chamada externa do LLM para execução rápida em CI/CD.
   - Verificação de payload de entrada e saída (`reply` e `tools_called`).
   - Rejeição de requisições inválidas com `422 Unprocessable Entity`.
   - Endpoint de verificação de integridade (`/api/health`).

3. **`backend/tests/test_benchmarks.py`:**
   - Validação da estrutura de dados do dashboard comparativo de notebooks.
   - Telemetria de GPU RTX 4060 Ti e taxas médias de FPS.
   - Comparativo de periféricos (MX Master 3S vs Keychron K2 Pro).
   - Detecção automática de intenções de benchmark e comparação.

---

## 🌲 Disciplina de Git & Branches

O projeto segue rigorosamente o fluxo de branches atômicas e merges sem fast-forward (`--no-ff`):

```text
main (estável / produção)
  ▲
  ├── feature/CORE-10-hardware-bot (Fundação e Entrega PRD)
  └── feature/CORE-20-grok-and-hardware-dashboards (Grok & Dashboards)
        ├── task/CORE-21-backend-grok-and-comparison-benchmarks
        ├── task/CORE-22-frontend-hardware-mini-dashboards
        └── task/CORE-23-docs-and-final-validation
```
