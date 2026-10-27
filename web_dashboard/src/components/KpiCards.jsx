import React from 'react'
import {
  Boxes,
  CheckCircle,
  XCircle,
  Percent,
  RotateCcw
} from 'lucide-react'

export default function KpiCards({
  total = 0,
  passed = 0,
  rejected = 0,
  onReset
}) {
  const defectRate = total > 0 ? ((rejected / total) * 100).toFixed(1) : '0.0'
  const passRate = total > 0 ? ((passed / total) * 100).toFixed(1) : '100.0'

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <h3 className="text-xs font-mono font-bold uppercase tracking-wider text-slate-400">
          Métricas de Producción
        </h3>
        <button
          onClick={onReset}
          title="Reiniciar contadores de inspección"
          className="text-[11px] font-mono text-slate-500 hover:text-slate-300 flex items-center gap-1 transition"
        >
          <RotateCcw className="w-3 h-3" />
          <span>Reset</span>
        </button>
      </div>

      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        {/* Total Cans */}
        <div className="bg-[#0e1626] border border-brand-border/60 rounded-xl p-3.5 flex flex-col justify-between shadow-md">
          <div className="flex items-center justify-between text-slate-400 mb-2">
            <span className="text-[11px] font-mono font-medium">Total Latas</span>
            <Boxes className="w-4 h-4 text-cyan-400" />
          </div>
          <p className="text-2xl font-bold font-mono text-white tracking-tight">
            {total}
          </p>
          <div className="mt-2 text-[10px] font-mono text-slate-500">
            Lote activo #104
          </div>
        </div>

        {/* Passed Cans */}
        <div className="bg-[#0e1626] border border-brand-border/60 rounded-xl p-3.5 flex flex-col justify-between shadow-md">
          <div className="flex items-center justify-between text-slate-400 mb-2">
            <span className="text-[11px] font-mono font-medium">Aprobadas</span>
            <CheckCircle className="w-4 h-4 text-emerald-400" />
          </div>
          <div className="flex items-baseline justify-between">
            <p className="text-2xl font-bold font-mono text-emerald-400 tracking-tight">
              {passed}
            </p>
            <span className="text-xs font-mono font-semibold text-emerald-500/90">
              {passRate}%
            </span>
          </div>
          <div className="mt-2 w-full bg-slate-900 h-1.5 rounded-full overflow-hidden">
            <div
              className="bg-emerald-500 h-full rounded-full transition-all"
              style={{ width: `${passRate}%` }}
            />
          </div>
        </div>

        {/* Rejected Cans */}
        <div className="bg-[#0e1626] border border-brand-border/60 rounded-xl p-3.5 flex flex-col justify-between shadow-md">
          <div className="flex items-center justify-between text-slate-400 mb-2">
            <span className="text-[11px] font-mono font-medium">Rechazadas</span>
            <XCircle className="w-4 h-4 text-rose-400" />
          </div>
          <div className="flex items-baseline justify-between">
            <p className="text-2xl font-bold font-mono text-rose-400 tracking-tight">
              {rejected}
            </p>
            <span className="text-xs font-mono font-semibold text-rose-500/90">
              {defectRate}%
            </span>
          </div>
          <div className="mt-2 w-full bg-slate-900 h-1.5 rounded-full overflow-hidden">
            <div
              className="bg-rose-500 h-full rounded-full transition-all"
              style={{ width: `${defectRate}%` }}
            />
          </div>
        </div>

        {/* Defect Rate */}
        <div className="bg-[#0e1626] border border-brand-border/60 rounded-xl p-3.5 flex flex-col justify-between shadow-md">
          <div className="flex items-center justify-between text-slate-400 mb-2">
            <span className="text-[11px] font-mono font-medium">Tasa de Descarte</span>
            <Percent className="w-4 h-4 text-amber-400" />
          </div>
          <p className="text-2xl font-bold font-mono text-amber-400 tracking-tight">
            {defectRate}%
          </p>
          <div className="mt-2 text-[10px] font-mono text-slate-400 flex items-center justify-between">
            <span>Tolerancia Máx:</span>
            <strong className="text-slate-300">5.0%</strong>
          </div>
        </div>
      </div>
    </div>
  )
}
