# CORE Hardware — Chatbot Inteligente de Atendimento & Estoque

Assistente conversacional oficial da **CORE Hardware** desenvolvido com arquitetura moderna full-stack para atender clientes com alta precisão técnica sobre computadores, notebooks de alto desempenho, placas de vídeo RTX, monitores 4K e periféricos.

O assistente integra as IAs **Grok (xAI)** e **Google Gemini** com **Tool / Function Calling**, garantindo que as respostas de disponibilidade, quantidades em estoque e valores monetários venham diretamente da base de dados oficial e não de alucinações. O sistema inclui **Mini Dashboards Gráficos de Comparação e Telemetria de Hardware** pré-montados e **Fallback Determinístico Inteligente** caso as chaves de API não estejam configuradas.

---

## 🛠️ Stack Tecnológica

- **Backend:** Python 3.10+, FastAPI, Uvicorn, Pydantic v2, Google GenAI SDK (`google-genai`), Pytest, HTTPX, python-dotenv.
- **Frontend:** React 18, TypeScript, Vite, Tailwind CSS, Lucide Icons, React Markdown (Design Dark Zinc / Titanium Hardware moderno com seletor de IA).
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

## 🔑 Configuração de Chaves de API (Grok & Gemini)

O assistente foi desenhado com foco em inteligência artificial de ponta utilizando **Tool / Function Calling** nativo. Para que o bot responda consultando o estoque em tempo real via IA, basta configurar a chave de um dos provedores suportados (**Grok da xAI** ou **Google Gemini**):

### 📋 Passo a Passo para Obter as Chaves de API

#### 1. Google Gemini (Recomendado — Gratuito, Rápido e Sem Cartão)
1. Acesse o **[Google AI Studio](https://aistudio.google.com/app/apikey)**.
2. Faça login com a sua conta Google (Gmail).
3. Clique no botão azul **"Create API key"** (Criar chave de API).
4. Selecione ou crie um projeto padrão do Google Cloud em 1 clique.
5. Copie a chave gerada (iniciada por `AIzaSy...`).
6. Cole a chave na variável `GEMINI_API_KEY`.
> *Vantagem:* Tier gratuito generoso, ativação instantânea sem cartão de crédito e suporte completo a Function Calling com o modelo `gemini-2.5-flash`.

#### 2. Grok (xAI)
1. Acesse o console oficial da **[xAI Console](https://console.x.ai/)**.
2. Crie uma conta ou faça login usando sua conta do X (Twitter).
3. No menu lateral, acesse a seção **API Keys**.
4. Clique em **Create Key** (ou Gerar Chave), defina um nome (ex: `core-hardware-bot`) e copie o token gerado (formato `xai-...`).
5. *(Nota de Saldo):* Em contas novas da xAI, certifique-se de habilitar créditos na aba **Billing** para que as requisições ao modelo `grok-2-latest` sejam autorizadas.
6. Cole a chave na variável `XAI_API_KEY`.

---

### ⚙️ Como Configurar as Variáveis de Ambiente

#### Localmente (via `.env`):
Copie o modelo de variáveis de ambiente e preencha a chave escolhida:
```bash
# Na raiz ou na pasta backend/
cp .env.example .env
```
Exemplo de preenchimento do `.env`:
```env
# Provedor padrão: 'auto', 'grok' ou 'gemini'
LLM_PROVIDER=auto

# Chave do Grok (xAI):
XAI_API_KEY=sua_chave_grok_aqui
GROK_MODEL=grok-2-latest

# Chave do Google Gemini (Alternativa gratuita recomendada):
GEMINI_API_KEY=AIzaSySuaChaveDoGeminiAqui
GEMINI_MODEL=gemini-2.5-flash
```

#### No Deploy na Vercel (Frontend e Backend Separados):

Como o projeto possui Frontend (React/Vite) e Backend (FastAPI), o recomendado na Vercel é criar **dois projetos a partir do mesmo repositório do GitHub**:

1. **Projeto 1: Backend (FastAPI)**
   - No painel da Vercel, clique em **Add New... > Project** e selecione o repositório.
   - Em **Root Directory**, clique em Edit e selecione a pasta: `backend`.
   - Em **Environment Variables**, adicione:
     - `GEMINI_API_KEY` (ou `XAI_API_KEY`) com sua chave.
     - `LLM_PROVIDER`: `gemini` (ou `auto` / `grok`).
   - Clique em **Deploy**. O projeto já conta com [`backend/vercel.json`](file:///D:/Empresa/core-hardware/backend/vercel.json) e [`backend/api/index.py`](file:///D:/Empresa/core-hardware/backend/api/index.py) configurados para serverless.
   - Ao finalizar, copie a URL gerada pela Vercel para o backend (ex: `https://core-hardware-api.vercel.app`).

2. **Projeto 2: Frontend (React / Vite)**
   - No painel da Vercel, crie um segundo projeto a partir do mesmo repositório.
   - Em **Root Directory**, selecione a pasta: `frontend`.
   - Em **Environment Variables**, adicione a variável que aponta para o backend:
     - **Key:** `VITE_API_BASE_URL`
     - **Value:** `https://core-hardware-api.vercel.app` *(a URL do seu backend gerada no Passo 1)*
   - Clique em **Deploy** (ou faça um Redeploy se o frontend já estiver criado). O Vite injetará automaticamente a URL da API em tempo de build!

> **Hierarquia de Execução & Resiliência:**
> - **IA Principal Obrigatória (Grok / Gemini):** Toda mensagem é enviada primariamente para o modelo de IA com Function Calling (`consultar_estoque` e `listar_produtos`).
> - **Fallback de Contingência Opcional:** O mecanismo determinístico atua estritamente como contingência de resiliência caso a API externa apresente instabilidade ou erros de rede, evitando interrupções para o cliente final.

---

## 📋 Pré-requisitos

- **Python:** 3.10 ou superior
- **Node.js:** 18.0 ou superior (e gerenciador `npm`)

---

## 🚀 Como Executar o Projeto Localmente

### 1. Backend & Testes (Python FastAPI)

1. Abra um terminal e entre no diretório do backend:
   ```bash
   cd backend
   ```

2. Instale as dependências:
   ```bash
   pip install -r requirements.txt
   # No Windows, caso prefira:
   # python -m pip install -r requirements.txt
   ```

3. Configure as variáveis de ambiente no `.env`:
   ```bash
   # Linux / macOS
   cp .env.example .env

   # Windows (PowerShell)
   Copy-Item .env.example .env
   ```
   Abra o `.env` e insira sua `GEMINI_API_KEY` ou `XAI_API_KEY` conforme o passo a passo acima.

4. Execute a suíte de testes unitários e de integração:
   ```bash
   pytest
   # Ou explicitamente:
   # python -m pytest tests/ -v
   ```

5. Inicie o servidor da API:
   ```bash
   uvicorn app.main:app --reload --port 8000
   ```
   A API estará acessível em `http://localhost:8000` (documentação interativa Swagger em `http://localhost:8000/docs`).

---

### 2. Frontend (React + TypeScript + Vite)

1. Em um segundo terminal, entre no diretório do frontend:
   ```bash
   cd frontend
   ```

2. Instale as dependências:
   ```bash
   npm install
   # No Windows (PowerShell com restrição de script):
   # npm.cmd install
   ```

3. Inicie o servidor de desenvolvimento:
   ```bash
   npm run dev
   # No Windows:
   # npm.cmd run dev
   ```

4. Abra a aplicação no navegador em **[http://localhost:3000](http://localhost:3000)**.

---

### 3. Teste Rápido via Terminal (cURL / HTTP)

Você também pode consultar o endpoint diretamente via linha de comando com a API em execução:

```bash
# Teste de consulta de estoque (MacBook Air M3)
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Vocês têm o MacBook Air M3? Tem quantos?"}'

# Teste de produto esgotado (Lenovo Legion Pro 5)
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Tem o Lenovo Legion Pro 5 em estoque?"}'
```

---

## 🧪 Suíte de Testes Automatizados

A aplicação possui 3 suítes de testes cobrindo 100% dos requisitos funcionais e não-funcionais:

1. **`backend/tests/test_inventory.py`:**
   - **Cenário A:** Busca por produto existente (ex: "MacBook", "MX Master 3S") retornando disponibilidade e estoque > 0.
   - **Cenário B:** Busca por produto esgotado ("Lenovo Legion Pro 5") retornando `estoque == 0` e status esgotado.
   - **Cenário C:** Busca por produto inexistente ("PlayStation 5") retornando não encontrado sem levantar exceções.
   - **Listagem por Categoria:** Filtros de catálogo por categoria e listagem completa.

2. **`backend/tests/test_chat_api.py`:**
   - Teste de integração HTTP com `fastapi.testclient.TestClient`.
   - Mock da chamada externa do LLM para execução rápida e isolada em CI/CD.
   - Verificação de payload de entrada e saída (`reply` e `tools_called`).
   - Rejeição de requisições inválidas com `422 Unprocessable Entity`.
   - Endpoint de verificação de integridade (`/api/health`).

3. **`backend/tests/test_benchmarks.py`:**
   - Validação da estrutura de dados do dashboard comparativo de notebooks.
   - Telemetria de GPU RTX 4060 Ti e taxas médias de FPS.
   - Comparativo de periféricos (MX Master 3S vs Keychron K2 Pro).
   - Detecção automática de intenções de benchmark e comparação.

---
