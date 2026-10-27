import React from 'react'
import {
  Camera,
  History,
  ShieldCheck,
  ChevronLeft,
  Boxes,
  CheckCircle,
  XCircle,
  Percent,
  RotateCcw,
  Sliders,
  Cpu,
  Thermometer,
  Zap,
  Radio
} from 'lucide-react'

export default function Sidebar({
  isOpen,
  onToggle,
  activeTab,
  onSelectTab,
  metrics,
  onResetMetrics,
  piTelemetry,
  connectionStatus,
  isSimulator,
  onOpenSettings,
  onManualTrigger
}) {
  const defectRate = metrics.total > 0 ? ((metrics.rejected / metrics.total) * 100).toFixed(1) : '0.0'
  const passRate = metrics.total > 0 ? ((metrics.passed / metrics.total) * 100).toFixed(1) : '100.0'

  const navItems = [
    { id: 'camara', label: 'Cámara', icon: Camera },
    { id: 'history', label: 'History', icon: History },
    { id: 'audit', label: 'Audit', icon: ShieldCheck }
  ]

  return (
    <aside
      className={`h-screen flex flex-col bg-[#0b1120] border-r border-slate-800/80 transition-all duration-300 ease-in-out z-30 select-none ${
        isOpen ? 'w-72 min-w-[288px]' : 'w-0 min-w-0 overflow-hidden border-r-0'
      }`}
    >
      {/* 1. Header with Branding matching wireframe */}
      <div className="p-4 border-b border-slate-800/80 flex items-center justify-between gap-3 bg-[#0d1527]">
        {/* Wireframe rounded branding box */}
        <div className="flex-1 flex items-center space-x-3 px-3 py-2 rounded-xl bg-slate-900/90 border border-slate-700/60 shadow-sm">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-cyan-500/20 to-emerald-500/20 text-cyan-400 font-mono font-black text-base flex items-center justify-center border border-cyan-500/40 shadow-[0_0_12px_rgba(6,182,212,0.25)]">
            S
          </div>
          <div className="flex flex-col">
            <div className="flex items-center space-x-1.5">
              <span className="text-sm font-bold tracking-tight text-white font-sans">
                S-can
              </span>
              <span className="text-[10px] px-1 py-0.2 rounded font-mono font-semibold bg-cyan-950 text-cyan-400 border border-cyan-800/80">
                AI
              </span>
            </div>
            <span className="text-[10px] text-slate-400 font-mono">
              Edge Industrial
            </span>
          </div>
        </div>

        {/* Collapse toggle button */}
        <button
          onClick={onToggle}
          title="Colapsar menú lateral"
          className="w-8 h-8 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800/80 flex items-center justify-center transition border border-transparent hover:border-slate-700"
        >
          <ChevronLeft className="w-5 h-5" />
        </button>
      </div>

      {/* 2. Navigation items (Camara, History, Audit) */}
      <div className="p-3 space-y-1 border-b border-slate-800/60">
        <div className="px-3 py-1 text-[10px] font-mono font-semibold uppercase tracking-wider text-slate-500">
          Vistas Principales
        </div>
        {navItems.map((item) => {
          const Icon = item.icon
          const isActive = activeTab === item.id
          return (
            <button
              key={item.id}
              onClick={() => onSelectTab(item.id)}
              className={`w-full flex items-center space-x-3 px-3.5 py-2.5 rounded-xl text-sm font-medium transition-all ${
                isActive
                  ? 'bg-gradient-to-r from-cyan-500/15 to-transparent text-cyan-300 border-l-2 border-cyan-400 font-semibold shadow-inner'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/50'
              }`}
            >
              <Icon className={`w-4 h-4 ${isActive ? 'text-cyan-400' : 'text-slate-500'}`} />
              <span>{item.label}</span>
              {isActive && (
                <span className="ml-auto w-1.5 h-1.5 rounded-full bg-cyan-400 shadow-[0_0_6px_#22d3ee]" />
              )}
            </button>
          )
        })}
      </div>

      {/* 3. Compact Metrics Section inside Sidebar (keeps portview clean without scroll) */}
      <div className="flex-1 p-3.5 overflow-y-auto space-y-3">
        <div className="flex items-center justify-between">
          <span className="text-[10px] font-mono font-bold uppercase tracking-wider text-slate-400">
            Métricas de Inspección
          </span>
          <button
            onClick={onResetMetrics}
            title="Reiniciar contadores"
            className="text-[10px] font-mono text-slate-500 hover:text-slate-300 flex items-center gap-1 transition"
          >
            <RotateCcw className="w-3 h-3" />
            <span>Reset</span>
          </button>
        </div>

        {/* 2x2 Grid of Minimalist Metrics */}
        <div className="grid grid-cols-2 gap-2 text-xs font-mono">
          {/* Total */}
          <div className="p-2.5 rounded-xl bg-slate-900/80 border border-slate-800/80">
            <div className="flex items-center justify-between text-slate-400 mb-1">
              <span className="text-[10px]">Total</span>
              <Boxes className="w-3.5 h-3.5 text-cyan-400" />
            </div>
            <div className="text-xl font-bold text-white">
              {metrics.total}
            </div>
          </div>

          {/* Defect Rate */}
          <div className="p-2.5 rounded-xl bg-slate-900/80 border border-slate-800/80">
            <div className="flex items-center justify-between text-slate-400 mb-1">
              <span className="text-[10px]">Descarte</span>
              <Percent className="w-3.5 h-3.5 text-amber-400" />
            </div>
            <div className="text-xl font-bold text-amber-400">
              {defectRate}%
            </div>
          </div>

          {/* Passed */}
          <div className="p-2.5 rounded-xl bg-slate-900/80 border border-slate-800/80">
            <div className="flex items-center justify-between text-slate-400 mb-1">
              <span className="text-[10px]">Aprobadas</span>
              <CheckCircle className="w-3.5 h-3.5 text-emerald-400" />
            </div>
            <div className="text-lg font-bold text-emerald-400">
              {metrics.passed}
            </div>
            <div className="text-[9px] text-slate-500 mt-0.5">
              {passRate}%
            </div>
          </div>

          {/* Rejected */}
          <div className="p-2.5 rounded-xl bg-slate-900/80 border border-slate-800/80">
            <div className="flex items-center justify-between text-slate-400 mb-1">
              <span className="text-[10px]">Rechazadas</span>
              <XCircle className="w-3.5 h-3.5 text-rose-400" />
            </div>
            <div className="text-lg font-bold text-rose-400">
              {metrics.rejected}
            </div>
            <div className="text-[9px] text-slate-500 mt-0.5">
              {defectRate}%
            </div>
          </div>
        </div>

        {/* Quality Progress Bar */}
        <div className="p-2.5 rounded-xl bg-slate-900/60 border border-slate-800/60">
          <div className="flex items-center justify-between text-[10px] font-mono mb-1.5 text-slate-400">
            <span>Rendimiento de Línea</span>
            <span className="text-emerald-400 font-semibold">{passRate}% OK</span>
          </div>
          <div className="w-full bg-slate-950 h-2 rounded-full overflow-hidden flex">
            <div
              className="bg-emerald-500 h-full transition-all duration-300"
              style={{ width: `${passRate}%` }}
            />
            <div
              className="bg-rose-500 h-full transition-all duration-300"
              style={{ width: `${defectRate}%` }}
            />
          </div>
        </div>

        {/* Hardware Status Pill */}
        <div className="p-2.5 rounded-xl bg-slate-900/60 border border-slate-800/60 space-y-2">
          <div className="flex items-center justify-between text-[10px] font-mono text-slate-400">
            <span className="flex items-center gap-1.5">
              <Cpu className="w-3 h-3 text-cyan-400" />
              <span>Raspberry Pi</span>
            </span>
            <span className="text-slate-300">{piTelemetry.cpuTemp}°C</span>
          </div>
          <div className="flex items-center justify-between text-[10px] font-mono text-slate-500">
            <span>CPU: {piTelemetry.cpuUsage}%</span>
            <span>Infer: {piTelemetry.modelLatencyMs}ms</span>
          </div>
        </div>

        {/* Quick Manual Scan Action */}
        <button
          onClick={onManualTrigger}
          className="w-full py-2 px-3 rounded-xl bg-cyan-950/60 hover:bg-cyan-900/60 border border-cyan-800/60 text-cyan-300 text-xs font-mono font-medium flex items-center justify-center gap-2 transition active:scale-[0.98]"
        >
          <Radio className="w-3.5 h-3.5 animate-pulse text-cyan-400" />
          <span>Disparar Captura</span>
        </button>
      </div>

      {/* 4. Footer with Settings & Connection Status */}
      <div className="p-3 border-t border-slate-800/80 bg-[#0d1527] flex items-center justify-between">
        <div className="flex items-center space-x-2">
          <span
            className={`w-2.5 h-2.5 rounded-full ${
              connectionStatus === 'connected'
                ? 'bg-emerald-400 shadow-[0_0_6px_#10b981]'
                : connectionStatus === 'reconnecting'
                ? 'bg-amber-400 animate-pulse'
                : 'bg-rose-400'
            }`}
          />
          <span className="text-[11px] font-mono text-slate-300 font-medium">
            {connectionStatus === 'connected'
              ? 'Pi Online'
              : connectionStatus === 'reconnecting'
              ? 'Reconectando...'
              : 'Pi Offline'}
          </span>
        </div>

        <button
          onClick={onOpenSettings}
          title="Configuración de Red / IP"
          className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition"
        >
          <Sliders className="w-4 h-4" />
        </button>
      </div>
    </aside>
  )
}
