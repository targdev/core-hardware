import React, { useState, useEffect, useRef } from 'react';
import {
  Cpu,
  Send,
  Bot,
  User,
  RotateCcw,
  Sparkles,
  Layers,
  CheckCircle2,
  HelpCircle,
  Laptop,
  HardDrive,
  BarChart3,
  BotMessageSquare
} from 'lucide-react';
import { HardwareDashboard, DashboardData } from './components/HardwareDashboard';

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  tools_called?: string[];
  dashboard_data?: DashboardData;
  provider?: string;
  timestamp: string;
}

const QUICK_PROMPTS = [
  '📊 Comparativo de Notebooks (MacBook vs XPS vs Legion)',
  '⚡ Benchmark RTX 4060 Ti e FPS em Jogos',
  '⌨️ Comparar Mouse MX Master 3S e Teclado Keychron',
  '🖥️ Análise do Monitor Dell UltraSharp 27" 4K',
  'Vocês têm o MacBook Air M3? Tem quantos?',
  'Tem o Lenovo Legion Pro 5 em estoque?',
];

const INITIAL_MESSAGE: Message = {
  id: 'init-1',
  role: 'assistant',
  content:
    'Olá! Seja bem-vindo à **CORE Hardware**.\n' +
    'Sou o seu assistente de alta performance para consulta em tempo real de estoque, especificações e **dashboards comparativos de desempenho**.\n\n' +
    'Como posso ajudar você hoje com nossos notebooks, GPUs, monitores ou periféricos?',
  provider: 'grok',
  timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
};

export default function App() {
  const [messages, setMessages] = useState<Message[]>([INITIAL_MESSAGE]);
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [serverOnline, setServerOnline] = useState<boolean | null>(null);
  const [selectedProvider, setSelectedProvider] = useState<'auto' | 'grok' | 'gemini'>('auto');
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const API_BASE_URL = 'http://localhost:8000';

  // Verificar status da API no carregamento
  useEffect(() => {
    const checkServer = async () => {
      try {
        const res = await fetch(`${API_BASE_URL}/api/health`, { method: 'GET' });
        if (res.ok) {
          setServerOnline(true);
        } else {
          setServerOnline(false);
        }
      } catch {
        setServerOnline(false);
      }
    };
    checkServer();
    const interval = setInterval(checkServer, 10000);
    return () => clearInterval(interval);
  }, []);

  // Rolagem suave até o fim das mensagens
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isLoading]);

  const handleSendMessage = async (textToSend?: string) => {
    const text = (textToSend || inputValue).trim();
    if (!text || isLoading) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: text,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    };

    const newMessages = [...messages, userMessage];
    setMessages(newMessages);
    setInputValue('');
    setIsLoading(true);

    try {
      // Montar histórico para a API
      const history = newMessages.slice(1, -1).map((m) => ({
        role: m.role,
        content: m.content,
      }));

      const res = await fetch(`${API_BASE_URL}/api/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message: text,
          history: history,
          provider: selectedProvider,
        }),
      });

      if (!res.ok) {
        throw new Error(`Erro na resposta do servidor (HTTP ${res.status})`);
      }

      const data = await res.json();
      const botMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: data.reply,
        tools_called: data.tools_called || [],
        dashboard_data: data.dashboard_data || undefined,
        provider: data.provider || 'fallback_core',
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      };

      setMessages((prev) => [...prev, botMessage]);
      setServerOnline(true);
    } catch (err: unknown) {
      const errorMessage = err instanceof Error ? err.message : 'Falha na comunicação com o servidor.';
      const fallbackErrorMsg: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content:
          `⚠️ Não foi possível conectar ao backend (${errorMessage}).\n` +
          'Certifique-se de que a API FastAPI está em execução na porta 8000 (`uvicorn app.main:app --port 8000`).',
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      };
      setMessages((prev) => [...prev, fallbackErrorMsg]);
      setServerOnline(false);
    } finally {
      setIsLoading(false);
      setTimeout(() => inputRef.current?.focus(), 100);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  const handleClearHistory = () => {
    setMessages([INITIAL_MESSAGE]);
  };

  const renderProviderBadge = (provider?: string) => {
    if (!provider) return null;
    if (provider === 'grok') {
      return (
        <span className="inline-flex items-center gap-1 text-[10.5px] font-mono px-2 py-0.5 rounded-full bg-purple-950/80 text-purple-300 border border-purple-800/60">
          <BotMessageSquare className="h-3 w-3 text-purple-400" /> Grok (xAI)
        </span>
      );
    }
    if (provider === 'gemini') {
      return (
        <span className="inline-flex items-center gap-1 text-[10.5px] font-mono px-2 py-0.5 rounded-full bg-blue-950/80 text-blue-300 border border-blue-800/60">
          <Sparkles className="h-3 w-3 text-blue-400" /> Gemini Flash
        </span>
      );
    }
    return (
      <span className="inline-flex items-center gap-1 text-[10.5px] font-mono px-2 py-0.5 rounded-full bg-zinc-800 text-cyan-300 border border-zinc-700">
        <Cpu className="h-3 w-3 text-cyan-400" /> CORE Engine
      </span>
    );
  };

  // Renderizador simples de markdown
  const renderFormattedContent = (content: string) => {
    const lines = content.split('\n');
    return (
      <div className="space-y-1.5 text-[14.5px] leading-relaxed">
        {lines.map((line, idx) => {
          if (!line.trim()) {
            return <div key={idx} className="h-1.5" />;
          }

          const isBullet = line.trim().startsWith('-') || line.trim().startsWith('*') || line.trim().startsWith('•');
          const cleanLine = isBullet ? line.trim().replace(/^[-*•]\s*/, '') : line;

          const parts = cleanLine.split(/(\*\*.*?\*\*)/g);

          return (
            <span key={idx} className={isBullet ? 'flex items-start gap-2' : 'block'}>
              {isBullet && (
                <span className="text-cyan-400 font-bold select-none mt-0.5">•</span>
              )}
              <span>
                {parts.map((part, pIdx) => {
                  if (part.startsWith('**') && part.endsWith('**')) {
                    return (
                      <strong key={pIdx} className="text-cyan-200 font-semibold">
                        {part.slice(2, -2)}
                      </strong>
                    );
                  }
                  return <span key={pIdx}>{part}</span>;
                })}
              </span>
            </span>
          );
        })}
      </div>
    );
  };

  return (
    <div className="flex h-screen flex-col bg-[#0b0d11] text-zinc-200 selection:bg-cyan-500 selection:text-black">
      {/* Top Header */}
      <header className="border-b border-zinc-800/80 bg-[#10141a]/95 backdrop-blur-md px-4 sm:px-6 py-3.5 z-10">
        <div className="max-w-5xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="relative flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-tr from-cyan-600 via-cyan-500 to-blue-600 shadow-lg shadow-cyan-500/20">
              <Cpu className="h-5 w-5 text-black" strokeWidth={2.5} />
              <div className="absolute -bottom-1 -right-1 h-3.5 w-3.5 rounded-full border-2 border-[#10141a] bg-emerald-500"></div>
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h1 className="text-base sm:text-lg font-bold tracking-tight text-white font-mono">
                  CORE <span className="text-cyan-400">HARDWARE</span>
                </h1>
                <span className="text-[10px] tracking-wider uppercase font-semibold px-2 py-0.5 rounded bg-zinc-800 border border-zinc-700/60 text-zinc-300">
                  Grok & Gemini AI
                </span>
              </div>
              <p className="text-xs text-zinc-400 flex items-center gap-1.5">
                Assistente de Estoque & Dashboards de Desempenho
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2 sm:gap-4">
            {/* Seletor de Modelo de IA */}
            <div className="flex items-center gap-1.5 bg-zinc-900 border border-zinc-800 px-2.5 py-1 rounded-xl text-xs">
              <span className="text-zinc-500 hidden sm:inline">IA:</span>
              <select
                value={selectedProvider}
                onChange={(e) => setSelectedProvider(e.target.value as 'auto' | 'grok' | 'gemini')}
                className="bg-transparent text-cyan-300 font-medium focus:outline-none cursor-pointer text-xs"
              >
                <option value="auto" className="bg-zinc-900 text-zinc-200">Auto (Grok / Gemini)</option>
                <option value="grok" className="bg-zinc-900 text-purple-300">Grok (xAI)</option>
                <option value="gemini" className="bg-zinc-900 text-blue-300">Google Gemini</option>
              </select>
            </div>

            {/* Server Status Badge */}
            <div className="hidden sm:flex items-center gap-2 px-3 py-1 rounded-full bg-zinc-900/90 border border-zinc-800 text-xs">
              <span
                className={`h-2 w-2 rounded-full ${
                  serverOnline === true
                    ? 'bg-emerald-400 animate-pulse'
                    : serverOnline === false
                    ? 'bg-rose-500'
                    : 'bg-amber-400'
                }`}
              />
              <span className="text-zinc-400">
                {serverOnline === true ? 'API Conectada' : serverOnline === false ? 'API Offline' : 'Verificando...'}
              </span>
            </div>

            <button
              onClick={handleClearHistory}
              title="Reiniciar conversa"
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium text-zinc-400 hover:text-zinc-200 bg-zinc-850 hover:bg-zinc-800 border border-zinc-750 transition"
            >
              <RotateCcw className="h-3.5 w-3.5" />
              <span className="hidden sm:inline">Limpar</span>
            </button>
          </div>
        </div>
      </header>

      {/* Main Chat Container */}
      <main className="flex-1 overflow-y-auto px-4 sm:px-6 py-6 scroll-smooth">
        <div className="max-w-4xl mx-auto space-y-6">
          {/* Badge de introdução */}
          <div className="rounded-xl border border-zinc-800/80 bg-zinc-900/50 p-4 shadow-sm flex items-start gap-3">
            <div className="p-2 rounded-lg bg-cyan-950/40 text-cyan-400 border border-cyan-800/40 shrink-0">
              <BarChart3 className="h-5 w-5" />
            </div>
            <div className="text-xs sm:text-sm text-zinc-300 space-y-1">
              <p className="font-semibold text-zinc-100 flex items-center gap-1.5">
                Suporte Completo a Grok (xAI) e Mini Dashboards de Telemetria
              </p>
              <p className="text-zinc-400 leading-relaxed">
                Peça comparações de hardware ou análises de FPS e veja mini dashboards gráficos gerados dinamicamente com dados do catálogo oficial da CORE Hardware.
              </p>
            </div>
          </div>

          {/* Messages Feed */}
          {messages.map((message) => {
            const isUser = message.role === 'user';
            return (
              <div
                key={message.id}
                className={`flex gap-3 sm:gap-4 ${isUser ? 'flex-row-reverse' : 'flex-row'}`}
              >
                {/* Avatar */}
                <div
                  className={`flex h-8 w-8 sm:h-9 sm:w-9 shrink-0 items-center justify-center rounded-xl border ${
                    isUser
                      ? 'border-cyan-500/30 bg-gradient-to-br from-cyan-600 to-blue-600 text-white'
                      : 'border-zinc-700 bg-zinc-800/90 text-cyan-400'
                  }`}
                >
                  {isUser ? <User className="h-4 w-4" /> : <Bot className="h-4 w-4" />}
                </div>

                {/* Bubble */}
                <div className={`max-w-[92%] sm:max-w-[88%] space-y-1.5`}>
                  <div
                    className={`rounded-2xl px-4 py-3 sm:px-5 sm:py-3.5 shadow-md ${
                      isUser
                        ? 'bg-gradient-to-br from-cyan-600 to-blue-600 text-white rounded-tr-none'
                        : 'bg-[#151921] border border-zinc-800/90 text-zinc-200 rounded-tl-none'
                    }`}
                  >
                    {renderFormattedContent(message.content)}

                    {/* Renderiza o Mini Dashboard Pré-Montado se presente */}
                    {message.dashboard_data && (
                      <HardwareDashboard data={message.dashboard_data} />
                    )}
                  </div>

                  {/* Informações da Resposta: Provedor e Tool Calling */}
                  {!isUser && (
                    <div className="flex flex-wrap items-center gap-2 pt-0.5 pl-1">
                      {renderProviderBadge(message.provider)}

                      {message.tools_called && message.tools_called.length > 0 && (
                        <div className="flex flex-wrap items-center gap-1.5">
                          <span className="text-[11px] text-zinc-500 font-mono flex items-center gap-1">
                            <Layers className="h-3 w-3 text-cyan-400" />
                            Tools:
                          </span>
                          {message.tools_called.map((tool, tIdx) => (
                            <span
                              key={tIdx}
                              className="inline-flex items-center gap-1 text-[11px] font-mono font-medium px-2 py-0.5 rounded-full bg-cyan-950/60 border border-cyan-800/50 text-cyan-300"
                            >
                              <CheckCircle2 className="h-3 w-3 text-emerald-400" />
                              {tool}()
                            </span>
                          ))}
                        </div>
                      )}
                    </div>
                  )}

                  {/* Timestamp */}
                  <div
                    className={`text-[10px] text-zinc-500 px-1 ${
                      isUser ? 'text-right' : 'text-left'
                    }`}
                  >
                    {message.timestamp}
                  </div>
                </div>
              </div>
            );
          })}

          {/* Loading Indicator */}
          {isLoading && (
            <div className="flex gap-3 sm:gap-4 items-start">
              <div className="flex h-8 w-8 sm:h-9 sm:w-9 shrink-0 items-center justify-center rounded-xl border border-zinc-700 bg-zinc-800/90 text-cyan-400">
                <Bot className="h-4 w-4" />
              </div>
              <div className="rounded-2xl rounded-tl-none bg-[#151921] border border-zinc-800/90 px-4 py-3 text-zinc-300">
                <div className="flex items-center gap-2 text-xs font-mono text-cyan-400">
                  <div className="flex space-x-1">
                    <div className="h-2 w-2 rounded-full bg-cyan-400 animate-bounce" style={{ animationDelay: '0ms' }} />
                    <div className="h-2 w-2 rounded-full bg-cyan-400 animate-bounce" style={{ animationDelay: '150ms' }} />
                    <div className="h-2 w-2 rounded-full bg-cyan-400 animate-bounce" style={{ animationDelay: '300ms' }} />
                  </div>
                  <span>Processando resposta e telemetria de hardware...</span>
                </div>
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>
      </main>

      {/* Footer Area: Quick Prompts & Input Bar */}
      <footer className="border-t border-zinc-800/80 bg-[#10141a]/95 backdrop-blur-md px-4 sm:px-6 py-3 sm:py-4">
        <div className="max-w-4xl mx-auto space-y-3">
          {/* Quick Prompts Bar */}
          <div className="flex items-center gap-1.5 overflow-x-auto pb-1 text-xs no-scrollbar">
            <span className="text-zinc-500 flex items-center gap-1 shrink-0 font-medium text-[11px] mr-1">
              <HelpCircle className="h-3.5 w-3.5 text-zinc-400" />
              Dashboards & Dúvidas:
            </span>
            {QUICK_PROMPTS.map((prompt, idx) => (
              <button
                key={idx}
                onClick={() => handleSendMessage(prompt)}
                disabled={isLoading}
                className="shrink-0 px-3 py-1.5 rounded-lg bg-zinc-900 hover:bg-zinc-800 border border-zinc-750 text-zinc-300 hover:text-cyan-300 hover:border-cyan-500/40 text-[11.5px] transition disabled:opacity-50"
              >
                {prompt}
              </button>
            ))}
          </div>

          {/* Input & Send Form */}
          <div className="relative flex items-center">
            <input
              ref={inputRef}
              type="text"
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              onKeyDown={handleKeyDown}
              disabled={isLoading}
              placeholder="Pergunte sobre estoque ou peça um comparativo (ex: Comparar MacBook com XPS)..."
              className="w-full rounded-xl bg-[#161a22] border border-zinc-750 pl-4 pr-12 py-3 text-sm text-zinc-100 placeholder-zinc-500 focus:outline-none focus:border-cyan-500 focus:ring-1 focus:ring-cyan-500/50 transition disabled:opacity-60"
            />
            <button
              onClick={() => handleSendMessage()}
              disabled={!inputValue.trim() || isLoading}
              className="absolute right-2 flex h-8 w-8 items-center justify-center rounded-lg bg-gradient-to-r from-cyan-500 to-blue-500 text-black hover:opacity-95 transition disabled:opacity-30 disabled:cursor-not-allowed"
            >
              <Send className="h-4 w-4" />
            </button>
          </div>

          <div className="flex items-center justify-between text-[11px] text-zinc-500 px-1">
            <span className="flex items-center gap-1.5">
              <Laptop className="h-3 w-3" /> Notebooks &bull; <HardDrive className="h-3 w-3" /> Monitores &bull; RTX GPUs &bull; Periféricos
            </span>
            <span>Pressione <kbd className="font-mono bg-zinc-800 px-1 py-0.5 rounded text-[10px] text-zinc-400">Enter</kbd> para enviar</span>
          </div>
        </div>
      </footer>
    </div>
  );
}
