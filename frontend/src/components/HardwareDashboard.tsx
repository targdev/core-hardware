import {
  Gamepad2,
  CheckCircle2,
  AlertTriangle,
  Monitor,
  Award,
  Sparkles,
  BarChart3
} from 'lucide-react';

export interface ComparedProduct {
  id: string;
  nome: string;
  preco?: number;
  estoque?: number;
  status?: string;
  badge?: string;
  destaque?: string;
  scores?: Record<string, number>;
  metricas?: Record<string, string>;
}

export interface GameBenchmark {
  jogo: string;
  fps: number;
  status: string;
}

export interface DashboardData {
  tipo: 'comparativo_notebooks' | 'benchmark_gpu' | 'comparativo_perifericos' | 'analise_monitor';
  titulo: string;
  subtitulo?: string;
  categorias_avaliacao?: string[];
  produtos?: ComparedProduct[];
  produto?: ComparedProduct;
  benchmarks_jogos?: GameBenchmark[];
  veredito?: string;
}

interface HardwareDashboardProps {
  data: DashboardData;
}

export const HardwareDashboard: React.FC<HardwareDashboardProps> = ({ data }) => {
  const getScoreColor = (score: number) => {
    if (score >= 90) return 'bg-cyan-400 text-cyan-400';
    if (score >= 80) return 'bg-emerald-400 text-emerald-400';
    if (score >= 70) return 'bg-blue-400 text-blue-400';
    if (score >= 60) return 'bg-amber-400 text-amber-400';
    return 'bg-rose-500 text-rose-500';
  };

  const formatPrice = (price?: number) => {
    if (price === undefined || price === null) return '';
    return new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(price);
  };

  return (
    <div className="mt-3.5 mb-1.5 overflow-hidden rounded-xl border border-zinc-700/80 bg-[#0e1218] p-4 sm:p-5 shadow-2xl">
      {/* Header do Mini Dashboard */}
      <div className="mb-4 border-b border-zinc-800 pb-3 flex items-start justify-between gap-3">
        <div>
          <div className="flex items-center gap-2">
            <div className="p-1.5 rounded-lg bg-cyan-950/70 border border-cyan-800/60 text-cyan-400">
              <BarChart3 className="h-4 w-4" />
            </div>
            <h3 className="text-sm sm:text-base font-bold text-white tracking-wide font-mono flex items-center gap-1.5">
              {data.titulo}
            </h3>
          </div>
          {data.subtitulo && (
            <p className="mt-1 text-xs text-zinc-400 pl-8">{data.subtitulo}</p>
          )}
        </div>
        <span className="shrink-0 text-[10px] uppercase font-mono tracking-wider px-2 py-0.5 rounded bg-zinc-800/90 text-cyan-400 border border-zinc-700/60">
          Telemetria Live
        </span>
      </div>

      {/* 1. Dashboard Comparativo de Notebooks */}
      {data.tipo === 'comparativo_notebooks' && data.produtos && (
        <div className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
            {data.produtos.map((prod) => {
              const isEsgotado = prod.status === 'esgotado' || prod.estoque === 0;
              return (
                <div
                  key={prod.id}
                  className={`flex flex-col justify-between rounded-xl border p-3.5 transition-all ${
                    isEsgotado
                      ? 'border-rose-900/40 bg-zinc-900/40 opacity-85'
                      : 'border-zinc-800 bg-[#141923] hover:border-cyan-500/40 shadow-sm'
                  }`}
                >
                  <div>
                    {/* Badge Destaque */}
                    {prod.badge && (
                      <div className="mb-2">
                        <span className="inline-flex items-center gap-1 text-[10.5px] font-semibold px-2 py-0.5 rounded-full bg-cyan-950/80 text-cyan-300 border border-cyan-800/60">
                          {prod.badge}
                        </span>
                      </div>
                    )}

                    <h4 className="font-semibold text-sm text-zinc-100">{prod.nome}</h4>
                    <p className="text-[11px] text-zinc-400 mt-0.5">{prod.destaque}</p>

                    {/* Preço e Status de Estoque */}
                    <div className="mt-2.5 mb-3 flex items-center justify-between text-xs">
                      <span className="font-mono font-bold text-cyan-300">
                        {formatPrice(prod.preco)}
                      </span>
                      <span
                        className={`inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10.5px] font-medium ${
                          isEsgotado
                            ? 'bg-rose-950/80 text-rose-300 border border-rose-800/60'
                            : 'bg-emerald-950/80 text-emerald-300 border border-emerald-800/60'
                        }`}
                      >
                        {isEsgotado ? (
                          <>
                            <AlertTriangle className="h-3 w-3" /> Esgotado
                          </>
                        ) : (
                          <>
                            <CheckCircle2 className="h-3 w-3" /> {prod.estoque} un.
                          </>
                        )}
                      </span>
                    </div>

                    {/* Barras de Desempenho / Score */}
                    {prod.scores && (
                      <div className="space-y-2 pt-2 border-t border-zinc-800/80">
                        {Object.entries(prod.scores).map(([metrica, score]) => (
                          <div key={metrica} className="space-y-1">
                            <div className="flex justify-between text-[11px] text-zinc-400">
                              <span>{metrica}</span>
                              <span className="font-mono font-bold text-zinc-200">{score}%</span>
                            </div>
                            <div className="h-1.5 w-full bg-zinc-800 rounded-full overflow-hidden">
                              <div
                                className={`h-full rounded-full transition-all duration-500 ${getScoreColor(
                                  score
                                ).split(' ')[0]}`}
                                style={{ width: `${score}%` }}
                              />
                            </div>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>

                  {/* Métricas adicionais */}
                  {prod.metricas && (
                    <div className="mt-3 pt-2 border-t border-zinc-800/60 text-[10.5px] text-zinc-400 space-y-1">
                      {prod.metricas['Autonomia'] && (
                        <div>
                          <span className="text-zinc-500">Bateria:</span> {prod.metricas['Autonomia']}
                        </div>
                      )}
                      {prod.metricas['Peso'] && (
                        <div>
                          <span className="text-zinc-500">Peso:</span> {prod.metricas['Peso']}
                        </div>
                      )}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* 2. Dashboard Telemetria GPU RTX 4060 Ti */}
      {data.tipo === 'benchmark_gpu' && data.produto && (
        <div className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Coluna 1: Dados da GPU e Scores */}
            <div className="rounded-xl border border-zinc-800 bg-[#141923] p-4 space-y-3">
              <div className="flex items-start justify-between">
                <div>
                  <span className="inline-flex items-center gap-1 text-[11px] font-semibold px-2 py-0.5 rounded-full bg-emerald-950/80 text-emerald-300 border border-emerald-800/60">
                    <Award className="h-3 w-3" /> {data.produto.badge}
                  </span>
                  <h4 className="font-bold text-base text-zinc-100 mt-2 font-mono">
                    {data.produto.nome}
                  </h4>
                  <p className="text-xs text-zinc-400">{data.produto.destaque}</p>
                </div>
                <div className="text-right">
                  <div className="font-mono font-bold text-cyan-300 text-sm">
                    {formatPrice(data.produto.preco)}
                  </div>
                  <span className="inline-block mt-1 text-[10px] px-2 py-0.5 rounded bg-emerald-950 text-emerald-300 border border-emerald-800">
                    {data.produto.estoque} un. disponíveis
                  </span>
                </div>
              </div>

              {/* Scores em barras */}
              {data.produto.scores && (
                <div className="space-y-2 pt-2 border-t border-zinc-800">
                  {Object.entries(data.produto.scores).map(([metrica, score]) => (
                    <div key={metrica} className="space-y-1">
                      <div className="flex justify-between text-xs text-zinc-400">
                        <span>{metrica}</span>
                        <span className="font-mono font-semibold text-zinc-200">{score}%</span>
                      </div>
                      <div className="h-1.5 w-full bg-zinc-800 rounded-full overflow-hidden">
                        <div
                          className={`h-full rounded-full ${getScoreColor(score).split(' ')[0]}`}
                          style={{ width: `${score}%` }}
                        />
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Coluna 2: FPS Médio nos Jogos */}
            <div className="rounded-xl border border-zinc-800 bg-[#141923] p-4 flex flex-col justify-between">
              <div>
                <h5 className="text-xs font-bold text-zinc-300 uppercase tracking-wider font-mono flex items-center gap-1.5 mb-3">
                  <Gamepad2 className="h-4 w-4 text-cyan-400" /> Taxas Médias de Quadros (FPS)
                </h5>

                <div className="space-y-2.5">
                  {data.benchmarks_jogos?.map((item, idx) => (
                    <div
                      key={idx}
                      className="flex items-center justify-between p-2 rounded-lg bg-zinc-900/60 border border-zinc-800/80 text-xs"
                    >
                      <span className="text-zinc-300 font-medium">{item.jogo}</span>
                      <div className="flex items-center gap-2">
                        <span className="font-mono font-bold text-cyan-300 text-sm">
                          {item.fps} FPS
                        </span>
                        <span className="text-[10px] px-1.5 py-0.5 rounded bg-cyan-950 text-cyan-300 border border-cyan-800/50">
                          {item.status}
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {data.produto.metricas && (
                <div className="mt-3 pt-3 border-t border-zinc-800/80 grid grid-cols-2 gap-2 text-[11px] text-zinc-400">
                  <div>
                    <span className="text-zinc-500">Consumo TDP:</span> {data.produto.metricas['Consumo Médio (TDP)']}
                  </div>
                  <div>
                    <span className="text-zinc-500">Fonte Recomendada:</span> {data.produto.metricas['Fonte Recomendada']}
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* 3. Dashboard Periféricos (MX Master 3S + Keychron K2 Pro) */}
      {data.tipo === 'comparativo_perifericos' && data.produtos && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3.5">
          {data.produtos.map((prod) => (
            <div key={prod.id} className="rounded-xl border border-zinc-800 bg-[#141923] p-4 space-y-3">
              <div className="flex items-start justify-between">
                <div>
                  <span className="inline-flex items-center gap-1 text-[10.5px] font-semibold px-2 py-0.5 rounded-full bg-cyan-950 text-cyan-300 border border-cyan-800">
                    {prod.badge}
                  </span>
                  <h4 className="font-bold text-sm text-zinc-100 mt-2">{prod.nome}</h4>
                  <p className="text-xs text-zinc-400">{prod.destaque}</p>
                </div>
                <div className="text-right">
                  <div className="font-mono font-bold text-cyan-300 text-sm">
                    {formatPrice(prod.preco)}
                  </div>
                  <span className="text-[10px] text-emerald-400 font-medium">
                    {prod.estoque} un. estoque
                  </span>
                </div>
              </div>

              {prod.scores && (
                <div className="space-y-1.5 pt-2 border-t border-zinc-800">
                  {Object.entries(prod.scores).map(([metrica, score]) => (
                    <div key={metrica} className="space-y-1">
                      <div className="flex justify-between text-[11px] text-zinc-400">
                        <span>{metrica}</span>
                        <span className="font-mono font-bold text-zinc-200">{score}%</span>
                      </div>
                      <div className="h-1.5 w-full bg-zinc-800 rounded-full overflow-hidden">
                        <div
                          className={`h-full rounded-full ${getScoreColor(score).split(' ')[0]}`}
                          style={{ width: `${score}%` }}
                        />
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          ))}
        </div>
      )}

      {/* 4. Dashboard Monitor Dell UltraSharp 4K */}
      {data.tipo === 'analise_monitor' && data.produto && (
        <div className="rounded-xl border border-zinc-800 bg-[#141923] p-4 space-y-3">
          <div className="flex items-start justify-between">
            <div>
              <span className="inline-flex items-center gap-1 text-[11px] font-semibold px-2.5 py-0.5 rounded-full bg-cyan-950 text-cyan-300 border border-cyan-800">
                <Monitor className="h-3 w-3" /> {data.produto.badge}
              </span>
              <h4 className="font-bold text-base text-zinc-100 mt-2 font-mono">
                {data.produto.nome}
              </h4>
              <p className="text-xs text-zinc-400">{data.produto.destaque}</p>
            </div>
            <div className="text-right">
              <div className="font-mono font-bold text-cyan-300 text-sm">
                {formatPrice(data.produto.preco)}
              </div>
              <span className="text-[11px] text-emerald-400 font-medium">
                {data.produto.estoque} un. disponíveis
              </span>
            </div>
          </div>

          {data.produto.scores && (
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 pt-2 border-t border-zinc-800">
              {Object.entries(data.produto.scores).map(([metrica, score]) => (
                <div key={metrica} className="space-y-1">
                  <div className="flex justify-between text-xs text-zinc-400">
                    <span>{metrica}</span>
                    <span className="font-mono font-bold text-zinc-200">{score}%</span>
                  </div>
                  <div className="h-1.5 w-full bg-zinc-800 rounded-full overflow-hidden">
                    <div
                      className={`h-full rounded-full ${getScoreColor(score).split(' ')[0]}`}
                      style={{ width: `${score}%` }}
                    />
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Veredito Técnico em Destaque */}
      {data.veredito && (
        <div className="mt-4 rounded-xl border border-cyan-900/40 bg-gradient-to-r from-cyan-950/40 via-zinc-900/60 to-blue-950/30 p-3 sm:p-3.5 text-xs text-zinc-300">
          <div className="flex items-center gap-1.5 text-cyan-400 font-bold mb-1 uppercase tracking-wider text-[11px]">
            <Sparkles className="h-3.5 w-3.5" /> Veredito de Engenharia CORE Hardware
          </div>
          <div className="leading-relaxed text-zinc-300 whitespace-pre-line pl-5">
            {data.veredito}
          </div>
        </div>
      )}
    </div>
  );
};
