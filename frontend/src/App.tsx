import React, { useState, useEffect, useRef } from 'react';
import {
  Cpu,
  Send,
  Bot,
  User,
  UserCheck,
  RotateCcw,
  Sparkles,
  HelpCircle,
  Laptop,
  HardDrive,
  BarChart3,
  BotMessageSquare,
  Database,
  X,
  Tag,
  MapPin,
  Bookmark
} from 'lucide-react';
import { HardwareDashboard, DashboardData } from './components/HardwareDashboard';
import Markdown from 'react-markdown';

export interface UserProfile {
  nome?: string;
  email?: string;
  cidade?: string;
  marcas_favoritas: string[];
  interesses: string[];
  ultimo_produto_id?: string;
  ultimo_produto_nome?: string;
  ultima_oferta_ia?: string;
  notas?: string[];
}

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
  'Meu nome é Tarcísio',
  'Prefiro produtos da Apple',
  'O que você sabe sobre mim?',
  '📊 Comparativo de Notebooks (MacBook vs XPS vs Legion)',
  '⚡ Benchmark RTX 4060 Ti e FPS em Jogos',
  '⌨️ Comparar Mouse MX Master 3S e Teclado Keychron',
  'Vocês têm o MacBook Air M3? Tem quantos?',
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

const STORAGE_KEY = 'core_hardware_chat_history';
const PROFILE_STORAGE_KEY = 'core_hardware_user_profile';

export default function App() {
  const [messages, setMessages] = useState<Message[]>(() => {
    try {
      const saved = localStorage.getItem(STORAGE_KEY);
      if (saved) {
        const parsed = JSON.parse(saved);
        if (Array.isArray(parsed) && parsed.length > 0) {
          return parsed;
        }
      }
    } catch (e) {
      console.warn('Erro ao carregar mensagens do localStorage:', e);
    }
    return [INITIAL_MESSAGE];
  });
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [serverOnline, setServerOnline] = useState<boolean | null>(null);
  const [selectedProvider, setSelectedProvider] = useState<'auto' | 'grok' | 'gemini'>('auto');
  const [userProfile, setUserProfile] = useState<UserProfile>(() => {
    try {
      const saved = localStorage.getItem(PROFILE_STORAGE_KEY);
      if (saved) {
        const parsed = JSON.parse(saved);
        if (parsed && typeof parsed === 'object') {
          return {
            nome: parsed.nome || undefined,
            email: parsed.email || undefined,
            cidade: parsed.cidade || undefined,
            marcas_favoritas: Array.isArray(parsed.marcas_favoritas) ? parsed.marcas_favoritas : [],
            interesses: Array.isArray(parsed.interesses) ? parsed.interesses : [],
            ultimo_produto_id: parsed.ultimo_produto_id || undefined,
            ultimo_produto_nome: parsed.ultimo_produto_nome || undefined,
            ultima_oferta_ia: parsed.ultima_oferta_ia || undefined,
            notas: Array.isArray(parsed.notas) ? parsed.notas : undefined,
          };
        }
      }
    } catch (e) {
      console.warn('Erro ao carregar perfil do localStorage:', e);
    }
    return { marcas_favoritas: [], interesses: [] };
  });
  const [showProfileModal, setShowProfileModal] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const API_BASE_URL = 'http://localhost:8000';

  // Persistir histórico de mensagens no localStorage para memória conversacional contínua
  useEffect(() => {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(messages));
    } catch (e) {
      console.warn('Erro ao salvar mensagens no localStorage:', e);
    }
  }, [messages]);

  // Persistir perfil do usuário no localStorage
  useEffect(() => {
    try {
      localStorage.setItem(PROFILE_STORAGE_KEY, JSON.stringify(userProfile));
    } catch (e) {
      console.warn('Erro ao salvar perfil no localStorage:', e);
    }
  }, [userProfile]);

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
      // Montar histórico contextual para a API mantendo até os últimos 10 turnos relevantes
      const history = newMessages
        .filter((m) => m.id !== 'init-1' && m.id !== userMessage.id && !m.content.startsWith('⚠️'))
        .slice(-10)
        .map((m) => ({
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
          user_profile: userProfile,
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

      if (data.user_profile) {
        setUserProfile(data.user_profile);
      }

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
    try {
      localStorage.removeItem(STORAGE_KEY);
    } catch (e) {
      console.warn('Erro ao limpar histórico do localStorage:', e);
    }
    setMessages([INITIAL_MESSAGE]);
  };

  const handleResetProfile = () => {
    const emptyProfile: UserProfile = { marcas_favoritas: [], interesses: [] };
    setUserProfile(emptyProfile);
    try {
      localStorage.removeItem(PROFILE_STORAGE_KEY);
    } catch (e) {
      console.warn('Erro ao remover perfil do localStorage:', e);
    }
    setShowProfileModal(false);
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
    return (
      <div className="text-[14.5px] leading-relaxed text-zinc-200">
        <Markdown
          components={{
            strong: ({ ...props }) => (
              <strong className="text-cyan-200 font-semibold" {...props} />
            ),
            em: ({ ...props }) => (
              <em className="text-zinc-200 font-medium not-italic" {...props} />
            ),
            p: ({ ...props }) => (
              <p className="leading-relaxed mb-2 last:mb-0" {...props} />
            ),
            ul: ({ ...props }) => (
              <ul className="space-y-1.5 my-2 pl-1" {...props} />
            ),
            ol: ({ ...props }) => (
              <ol className="space-y-1.5 my-2 list-decimal pl-5 text-zinc-300" {...props} />
            ),
            li: ({ children, ...props }) => (
              <li className="flex items-start gap-2 leading-relaxed text-zinc-200" {...props}>
                <span className="text-cyan-400 font-bold select-none mt-1 text-xs">•</span>
                <span className="flex-1">{children}</span>
              </li>
            ),
            h1: ({ ...props }) => (
              <h1 className="text-base font-bold text-white mb-2" {...props} />
            ),
            h2: ({ ...props }) => (
              <h2 className="text-sm font-bold text-white mb-1.5" {...props} />
            ),
            h3: ({ ...props }) => (
              <h3 className="text-sm font-semibold text-cyan-300 mb-1" {...props} />
            ),
            code: ({ ...props }) => (
              <code className="bg-zinc-800 text-cyan-300 px-1.5 py-0.5 rounded text-xs font-mono" {...props} />
            ),
          }}
        >
          {content}
        </Markdown>
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

            {/* Perfil & Preferências Memorizadas */}
            <button
              onClick={() => setShowProfileModal(true)}
              title="Ver preferências e dados memorizados do usuário"
              className={`flex items-center gap-1.5 px-2.5 py-1 rounded-xl text-xs font-medium border transition ${
                userProfile.nome
                  ? 'bg-cyan-950/80 border-cyan-700/80 text-cyan-200 hover:bg-cyan-900/60 shadow-sm shadow-cyan-950/30'
                  : 'bg-zinc-900 border-zinc-800 text-zinc-400 hover:text-zinc-200 hover:bg-zinc-850'
              }`}
            >
              {userProfile.nome ? (
                <>
                  <UserCheck className="h-3.5 w-3.5 text-cyan-400" />
                  <span className="font-semibold text-cyan-300 max-w-[90px] sm:max-w-[120px] truncate">{userProfile.nome}</span>
                </>
              ) : (
                <>
                  <User className="h-3.5 w-3.5 text-zinc-400" />
                  <span className="hidden sm:inline">Perfil</span>
                </>
              )}
            </button>

            {/* Indicador de Memória Local */}
            <div
              title="Histórico persistido localmente via localStorage"
              className="hidden lg:flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-zinc-900/70 border border-zinc-800 text-[11px] text-zinc-400 font-mono"
            >
              <Database className="h-3 w-3 text-cyan-400" />
              <span>Memória Ativa</span>
            </div>

            <button
              onClick={handleClearHistory}
              title="Reiniciar conversa e limpar histórico salvo no localStorage"
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium text-zinc-400 hover:text-zinc-200 bg-zinc-850 hover:bg-zinc-800 border border-zinc-750 transition"
            >
              <RotateCcw className="h-3.5 w-3.5" />
              <span className="hidden sm:inline">Limpar</span>
            </button>
          </div>
        </div>
      </header>

      {/* Modal de Perfil e Preferências do Usuário */}
      {showProfileModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/75 backdrop-blur-sm p-4">
          <div className="w-full max-w-md rounded-2xl border border-zinc-800 bg-[#12161f] p-5 sm:p-6 shadow-2xl shadow-cyan-950/30 text-zinc-200">
            <div className="flex items-center justify-between pb-4 border-b border-zinc-800/80">
              <div className="flex items-center gap-2.5">
                <div className="p-2 rounded-xl bg-cyan-950/80 text-cyan-400 border border-cyan-800/60">
                  <UserCheck className="h-5 w-5" />
                </div>
                <div>
                  <h3 className="text-base font-bold text-white">Perfil do Cliente</h3>
                  <p className="text-xs text-zinc-400">Dados & Preferências memorizadas pela IA</p>
                </div>
              </div>
              <button
                onClick={() => setShowProfileModal(false)}
                className="rounded-lg p-1 text-zinc-400 hover:bg-zinc-800 hover:text-white transition"
              >
                <X className="h-5 w-5" />
              </button>
            </div>

            <div className="py-4 space-y-3.5 text-xs sm:text-sm">
              {/* Nome */}
              <div className="flex items-center justify-between p-3 rounded-xl bg-zinc-900/70 border border-zinc-800/80">
                <span className="text-zinc-400 flex items-center gap-1.5">
                  <User className="h-4 w-4 text-cyan-400" /> Nome:
                </span>
                <span className="font-semibold text-white">
                  {userProfile.nome || <em className="text-zinc-500 not-italic">Não informado (Diga: "Meu nome é...")</em>}
                </span>
              </div>

              {/* Localização / Cidade */}
              {userProfile.cidade && (
                <div className="flex items-center justify-between p-3 rounded-xl bg-zinc-900/70 border border-zinc-800/80">
                  <span className="text-zinc-400 flex items-center gap-1.5">
                    <MapPin className="h-4 w-4 text-cyan-400" /> Cidade:
                  </span>
                  <span className="font-semibold text-white">{userProfile.cidade}</span>
                </div>
              )}

              {/* Último Produto em Foco */}
              {userProfile.ultimo_produto_nome && (
                <div className="flex items-center justify-between p-3 rounded-xl bg-zinc-900/70 border border-zinc-800/80">
                  <span className="text-zinc-400 flex items-center gap-1.5">
                    <Laptop className="h-4 w-4 text-cyan-400" /> Produto em Foco:
                  </span>
                  <span className="font-semibold text-cyan-200">{userProfile.ultimo_produto_nome}</span>
                </div>
              )}

              {/* Marcas Favoritas */}
              <div className="p-3 rounded-xl bg-zinc-900/70 border border-zinc-800/80 space-y-2">
                <div className="text-zinc-400 flex items-center gap-1.5 font-medium">
                  <Bookmark className="h-4 w-4 text-purple-400" /> Marcas Preferidas:
                </div>
                {userProfile.marcas_favoritas.length > 0 ? (
                  <div className="flex flex-wrap gap-1.5">
                    {userProfile.marcas_favoritas.map((marca, i) => (
                      <span
                        key={i}
                        className="px-2.5 py-0.5 rounded-md bg-purple-950/80 text-purple-300 border border-purple-800/60 text-xs font-medium"
                      >
                        {marca}
                      </span>
                    ))}
                  </div>
                ) : (
                  <p className="text-zinc-500 text-xs">
                    Nenhuma marca salva ainda (ex: "Prefiro produtos da Apple").
                  </p>
                )}
              </div>

              {/* Interesses / Foco */}
              <div className="p-3 rounded-xl bg-zinc-900/70 border border-zinc-800/80 space-y-2">
                <div className="text-zinc-400 flex items-center gap-1.5 font-medium">
                  <Tag className="h-4 w-4 text-cyan-400" /> Foco de Uso & Interesses:
                </div>
                {userProfile.interesses.length > 0 ? (
                  <div className="flex flex-wrap gap-1.5">
                    {userProfile.interesses.map((interesse, i) => (
                      <span
                        key={i}
                        className="px-2.5 py-0.5 rounded-md bg-cyan-950/80 text-cyan-300 border border-cyan-800/60 text-xs font-medium"
                      >
                        {interesse}
                      </span>
                    ))}
                  </div>
                ) : (
                  <p className="text-zinc-500 text-xs">
                    Nenhum foco registrado ainda (ex: "Sou programador" ou "Gosto de jogos").
                  </p>
                )}
              </div>
            </div>

            <div className="pt-3 border-t border-zinc-800/80 flex items-center justify-between gap-3">
              <button
                onClick={handleResetProfile}
                className="px-3 py-1.5 rounded-lg text-xs font-medium text-rose-400 hover:text-rose-300 bg-rose-950/40 hover:bg-rose-950/70 border border-rose-800/50 transition"
              >
                Resetar Perfil
              </button>
              <button
                onClick={() => setShowProfileModal(false)}
                className="px-4 py-1.5 rounded-lg text-xs font-semibold text-black bg-cyan-400 hover:bg-cyan-300 transition"
              >
                Fechar
              </button>
            </div>
          </div>
        </div>
      )}

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

                  {/* Badge discreto do assistente / provedor */}
                  {!isUser && message.provider && (
                    <div className="flex items-center gap-2 pt-0.5 pl-1">
                      {renderProviderBadge(message.provider)}
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
