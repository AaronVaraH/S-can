import React from 'react'
import {
  CheckCircle2,
  AlertTriangle,
  HelpCircle,
  ShieldCheck,
  ShieldAlert,
  ArrowRightCircle,
  Zap,
  Target
} from 'lucide-react'

export default function VerdictCard({ lastPrediction }) {
  const isDefect =
    lastPrediction?.class === 'dañada' ||
    lastPrediction?.class === 'abollada' ||
    lastPrediction?.class === 'defectuosa'

  const hasPrediction = !!lastPrediction

  const confidencePct = lastPrediction
    ? (lastPrediction.confidence * 100).toFixed(1)
    : '0.0'

  return (
    <div className="bg-[#0e1626] border border-brand-border/70 rounded-2xl p-5 shadow-xl shadow-black/20 flex flex-col justify-between relative overflow-hidden">
      {/* Decorative ambient background glow */}
      {hasPrediction && (
        <div
          className={`absolute -right-20 -top-20 w-48 h-48 rounded-full blur-3xl pointer-events-none transition-all duration-500 ${
            isDefect ? 'bg-rose-600/20' : 'bg-emerald-600/20'
          }`}
        />
      )}

      {/* Header */}
      <div className="flex items-center justify-between mb-4 z-10">
        <div className="flex items-center space-x-2">
          <Target className="w-4 h-4 text-cyan-400" />
          <h2 className="text-xs font-mono font-bold uppercase tracking-wider text-slate-300">
            Dictamen en Tiempo Real
          </h2>
        </div>
        <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-900 border border-slate-700 text-slate-400">
          QC Stage 1
        </span>
      </div>

      {/* Main Verdict Display Banner */}
      <div className="z-10 mb-4">
        {!hasPrediction ? (
          <div className="p-5 rounded-xl bg-slate-950/60 border border-dashed border-slate-800 text-center flex flex-col items-center justify-center min-h-[140px]">
            <HelpCircle className="w-8 h-8 text-slate-600 mb-2 animate-pulse" />
            <p className="text-sm font-semibold text-slate-300">En Espera de Muestra</p>
            <p className="text-xs text-slate-500 font-mono mt-1">
              Coloque una lata frente al sensor óptico
            </p>
          </div>
        ) : isDefect ? (
          <div className="p-5 rounded-xl bg-gradient-to-br from-rose-950/70 via-rose-900/30 to-slate-950 border-2 border-rose-600 shadow-[0_0_25px_rgba(239,68,68,0.25)] flex flex-col items-center text-center transition-all animate-pulse-glow">
            <div className="w-12 h-12 rounded-full bg-rose-600/30 border border-rose-500 text-rose-300 flex items-center justify-center mb-2 shadow-lg shadow-rose-900/40">
              <ShieldAlert className="w-7 h-7" />
            </div>
            <span className="text-xs font-mono uppercase tracking-widest text-rose-400 font-bold">
              Defecto Detectado
            </span>
            <h3 className="text-xl sm:text-2xl font-black text-white tracking-tight mt-0.5">
              LATA RECHAZADA
            </h3>
            <div className="mt-2 inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-rose-950 border border-rose-700/80 text-rose-300 text-xs font-mono">
              <span>Tipo: {lastPrediction.defectType || 'Abolladura / Deformidad'}</span>
            </div>
          </div>
        ) : (
          <div className="p-5 rounded-xl bg-gradient-to-br from-emerald-950/70 via-emerald-900/30 to-slate-950 border-2 border-emerald-500 shadow-[0_0_25px_rgba(16,185,129,0.25)] flex flex-col items-center text-center transition-all">
            <div className="w-12 h-12 rounded-full bg-emerald-600/30 border border-emerald-500 text-emerald-300 flex items-center justify-center mb-2 shadow-lg shadow-emerald-900/40">
              <ShieldCheck className="w-7 h-7" />
            </div>
            <span className="text-xs font-mono uppercase tracking-widest text-emerald-400 font-bold">
              Control Superado
            </span>
            <h3 className="text-xl sm:text-2xl font-black text-white tracking-tight mt-0.5">
              LATA INTACTA
            </h3>
            <div className="mt-2 inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-emerald-950 border border-emerald-700/80 text-emerald-300 text-xs font-mono">
              <CheckCircle2 className="w-3.5 h-3.5" />
              <span>Superficie Conforme · Estructura OK</span>
            </div>
          </div>
        )}
      </div>

      {/* Confidence Level & Quality Metrics */}
      <div className="z-10 bg-[#0a101d] rounded-xl p-4 border border-brand-border/60 space-y-3">
        <div className="flex justify-between items-center text-xs font-mono">
          <span className="text-slate-400">Certeza del Modelo</span>
          <span className="text-base font-bold text-white font-mono">
            {confidencePct}%
          </span>
        </div>

        {/* Progress Energy Bar */}
        <div className="w-full bg-slate-900 h-2.5 rounded-full overflow-hidden p-0.5 border border-slate-800">
          <div
            className={`h-full rounded-full transition-all duration-500 ${
              !hasPrediction
                ? 'bg-slate-700'
                : isDefect
                ? 'bg-rose-500 shadow-[0_0_10px_#ef4444]'
                : 'bg-emerald-500 shadow-[0_0_10px_#10b981]'
            }`}
            style={{ width: `${hasPrediction ? confidencePct : 0}%` }}
          />
        </div>

        {/* Action Recommendation */}
        <div className="pt-2 border-t border-slate-800/80 flex items-center justify-between text-[11px] font-mono">
          <span className="text-slate-400">Acción Actuador:</span>
          <span
            className={`font-semibold flex items-center gap-1 ${
              !hasPrediction
                ? 'text-slate-500'
                : isDefect
                ? 'text-rose-400'
                : 'text-emerald-400'
            }`}
          >
            <ArrowRightCircle className="w-3.5 h-3.5" />
            {!hasPrediction
              ? 'Standby'
              : isDefect
              ? 'Expulsar a Reciclaje'
              : 'Avanzar a Envasado'}
          </span>
        </div>
      </div>
    </div>
  )
}
