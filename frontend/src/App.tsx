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
  HardDrive
} from 'lucide-react';

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  tools_called?: string[];
  timestamp: string;
}

const QUICK_PROMPTS = [
  'Vocês têm o MacBook Air M3? Tem quantos?',
  'Tem o Lenovo Legion Pro 5 em estoque?',
  'Quantos teclados Keychron K2 Pro têm?',
  'Quais monitores vocês têm disponíveis?',
  'Tem a RTX 4060 Ti? Qual o preço?',
];

const INITIAL_MESSAGE: Message = {
  id: 'init-1',
  role: 'assistant',
  content:
    'Olá! Seja bem-vindo à **CORE Hardware**.\n' +
    'Sou o seu assistente de alta performance para consulta em tempo real de computadores, notebooks, monitores e periféricos.\n' +
    'Como posso ajudar você hoje?',
  timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
};

export default function App() {
  const [messages, setMessages] = useState<Message[]>([INITIAL_MESSAGE]);
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [serverOnline, setServerOnline] = useState<boolean | null>(null);
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

  // Renderizador simples de markdown (negrito, itálico, bullet points e quebras de linha)
  const renderFormattedContent = (content: string) => {
    const lines = content.split('\n');
    return (
      <div className="space-y-1.5 text-[14.5px] leading-relaxed">
        {lines.map((line, idx) => {
          if (!line.trim()) {
            return <div key={idx} className="h-1.5" />;
          }

          // Renderizar marcadores de lista
          const isBullet = line.trim().startsWith('-') || line.trim().startsWith('*');
          const cleanLine = isBullet ? line.trim().substring(1).trim() : line;

          // Processar negrito simples **texto**
          const parts = cleanLine.split(/(\*\*.*?\*\*)/g);

          const formattedLine = (
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

          return formattedLine;
        })}
      </div>
    );
  };

  return (
    <div className="flex h-screen flex-col bg-[#0b0d11] text-zinc-200 selection:bg-cyan-500 selection:text-black">
      {/* Top Header */}
      <header className="border-b border-zinc-800/80 bg-[#10141a]/90 backdrop-blur-md px-4 sm:px-6 py-3.5 z-10">
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
                  Tool Calling v1.0
                </span>
              </div>
              <p className="text-xs text-zinc-400 flex items-center gap-1.5">
                Assistente de Estoque & Alta Performance
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2 sm:gap-4">
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
                {serverOnline === true
                  ? 'API Conectada'
                  : serverOnline === false
                  ? 'API Desconectada'
                  : 'Verificando API...'}
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
        <div className="max-w-3xl mx-auto space-y-6">
          {/* Badge de introdução */}
          <div className="rounded-xl border border-zinc-800/80 bg-zinc-900/50 p-4 shadow-sm flex items-start gap-3">
            <div className="p-2 rounded-lg bg-cyan-950/40 text-cyan-400 border border-cyan-800/40 shrink-0">
              <Sparkles className="h-5 w-5" />
            </div>
            <div className="text-xs sm:text-sm text-zinc-300 space-y-1">
              <p className="font-semibold text-zinc-100 flex items-center gap-1.5">
                Base de Dados de Estoque Oficial Conectada
              </p>
              <p className="text-zinc-400 leading-relaxed">
                Consulte em linguagem natural especificações, preços e disponibilidade de MacBooks, XPS, Lenovo Legion, monitores Dell 4K e GPUs RTX.
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
                <div className={`max-w-[85%] sm:max-w-[78%] space-y-1.5`}>
                  <div
                    className={`rounded-2xl px-4 py-3 sm:px-5 sm:py-3.5 shadow-md ${
                      isUser
                        ? 'bg-gradient-to-br from-cyan-600 to-blue-600 text-white rounded-tr-none'
                        : 'bg-[#151921] border border-zinc-800/90 text-zinc-200 rounded-tl-none'
                    }`}
                  >
                    {renderFormattedContent(message.content)}
                  </div>

                  {/* Tool Calling Badges (se foram chamadas ferramentas) */}
                  {!isUser && message.tools_called && message.tools_called.length > 0 && (
                    <div className="flex flex-wrap items-center gap-1.5 pt-0.5 pl-1">
                      <span className="text-[11px] text-zinc-500 font-mono flex items-center gap-1">
                        <Layers className="h-3 w-3 text-cyan-400" />
                        Tool Calling:
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
                  <span>Consultando inventário em tempo real...</span>
                </div>
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>
      </main>

      {/* Footer Area: Quick Prompts & Input Bar */}
      <footer className="border-t border-zinc-800/80 bg-[#10141a]/95 backdrop-blur-md px-4 sm:px-6 py-3 sm:py-4">
        <div className="max-w-3xl mx-auto space-y-3">
          {/* Quick Prompts Bar */}
          <div className="flex items-center gap-1.5 overflow-x-auto pb-1 text-xs no-scrollbar">
            <span className="text-zinc-500 flex items-center gap-1 shrink-0 font-medium text-[11px] mr-1">
              <HelpCircle className="h-3.5 w-3.5 text-zinc-400" />
              Sugestões:
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
              placeholder="Pergunte sobre produtos, preços ou estoque (ex: Tem MacBook M3?)..."
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
              <Laptop className="h-3 w-3" /> Notebooks &bull; <HardDrive className="h-3 w-3" /> Monitores &bull; GPUs
            </span>
            <span>Pressione <kbd className="font-mono bg-zinc-800 px-1 py-0.5 rounded text-[10px] text-zinc-400">Enter</kbd> para enviar</span>
          </div>
        </div>
      </footer>
    </div>
  );
}
