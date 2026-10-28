import React from 'react'
import {
  Camera,
  History,
  ShieldCheck,
  Boxes,
  CheckCircle,
  XCircle,
  Percent,
  RotateCcw,
  Sliders,
  Cpu,
  Radio
} from 'lucide-react'

export default function Sidebar({
  isOpen,
  onToggle,
  activeTab,
  onSelectTab,
  metrics = { total: 0, passed: 0, rejected: 0 },
  onResetMetrics,
  piTelemetry = {},
  connectionStatus,
  pingMs,
  onOpenSettings,
  onManualTrigger,
  isTriggering
}) {
  const defectRate = metrics.total > 0 ? ((metrics.rejected / metrics.total) * 100).toFixed(1) : '0.0'
  const passRate = metrics.total > 0 ? ((metrics.passed / metrics.total) * 100).toFixed(1) : '100.0'

  const navItems = [
    { id: 'camara', label: 'Cámara en Vivo', icon: Camera, desc: 'Feed e Inferencia' },
    { id: 'history', label: 'Historial de Lote', icon: History, desc: 'Trazabilidad y Muestras' },
    { id: 'audit', label: 'Telemetría Hardware', icon: ShieldCheck, desc: 'Diagnóstico Raspberry Pi' }
  ]

  return (
    <aside
      className={`h-screen flex flex-col bg-slate-950/70 backdrop-blur-2xl border-r border-white/[0.08] transition-all duration-300 ease-in-out z-30 select-none ${
        isOpen ? 'w-72 min-w-[288px]' : 'w-16 min-w-[64px]'
      }`}
    >
      {/* 1. Header with Logo and Brand Name (Height h-14 matches Navbar) */}
      <div
        className={`h-14 border-b border-white/[0.08] flex items-center bg-slate-900/40 shrink-0 ${
          isOpen ? 'px-4 space-x-3' : 'justify-center px-2'
        }`}
      >
        <div className="w-8 h-8 rounded-lg bg-slate-900/80 border border-cyan-500/30 flex items-center justify-center shadow-inner overflow-hidden shrink-0">
          <img
            src="/logo.png"
            alt="S-can Logo"
            className="w-full h-full object-contain scale-125 filter drop-shadow-[0_0_8px_rgba(6,182,212,0.4)]"
          />
        </div>
        {isOpen && (
          <span className="text-sm font-bold tracking-tight text-white font-sans truncate">
            S-Can
          </span>
        )}
      </div>

      {/* 2. Navigation items */}
      <div className={`p-3 space-y-1 border-b border-white/[0.06] ${!isOpen ? 'px-2' : ''}`}>
        {isOpen && (
          <div className="px-3 py-1 text-[10px] font-mono font-semibold uppercase tracking-wider text-slate-500">
            Vistas Operativas
          </div>
        )}
        {navItems.map((item) => {
          const Icon = item.icon
          const isActive = activeTab === item.id
          return (
            <button
              key={item.id}
              onClick={() => onSelectTab(item.id)}
              title={item.label}
              className={`w-full flex items-center rounded-xl text-xs transition-all ${
                isOpen ? 'space-x-3 px-3.5 py-2.5' : 'justify-center py-2.5 px-0'
              } ${
                isActive
                  ? 'bg-slate-800/80 text-white border border-white/10 shadow-sm font-medium'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/30'
              }`}
            >
              <div
                className={`w-7 h-7 rounded-lg flex items-center justify-center border transition-colors shrink-0 ${
                  isActive
                    ? 'bg-cyan-500/20 border-cyan-500/30 text-cyan-300'
                    : 'bg-slate-800/40 border-white/5 text-slate-400'
                }`}
              >
                <Icon className="w-3.5 h-3.5" />
              </div>
              {isOpen && (
                <>
                  <div className="flex flex-col text-left truncate">
                    <span className="font-sans font-medium text-slate-200 text-xs truncate">{item.label}</span>
                    <span className="text-[10px] text-slate-500 font-mono truncate">{item.desc}</span>
                  </div>
                  {isActive && (
                    <span className="ml-auto w-1.5 h-1.5 rounded-full bg-cyan-400 shrink-0" />
                  )}
                </>
              )}
            </button>
          )
        })}
      </div>

      {/* 3. Real Batch Metrics (Zero Mock Data) */}
      {isOpen ? (
        <div className="flex-1 p-3.5 overflow-y-auto space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-[10px] font-mono font-semibold uppercase tracking-wider text-slate-400">
              Lote Actual
            </span>
            {metrics.total > 0 && (
              <button
                onClick={onResetMetrics}
                title="Reiniciar contadores de inspección"
                className="text-[10px] font-mono text-slate-500 hover:text-slate-300 flex items-center gap-1 transition"
              >
                <RotateCcw className="w-3 h-3" />
                <span>Reset</span>
              </button>
            )}
          </div>

          {/* 2x2 Clean Glass Grid */}
          <div className="grid grid-cols-2 gap-2 text-xs font-mono">
            {/* Total */}
            <div className="p-2.5 rounded-xl glass-card">
              <div className="flex items-center justify-between text-slate-400 mb-1">
                <span className="text-[10px]">Total</span>
                <Boxes className="w-3.5 h-3.5 text-slate-400" />
              </div>
              <div className="text-xl font-bold text-white tracking-tight">
                {metrics.total}
              </div>
            </div>

            {/* Defect Rate */}
            <div className="p-2.5 rounded-xl glass-card">
              <div className="flex items-center justify-between text-slate-400 mb-1">
                <span className="text-[10px]">Descarte</span>
                <Percent className="w-3.5 h-3.5 text-amber-400/80" />
              </div>
              <div className="text-xl font-bold text-amber-300 tracking-tight">
                {defectRate}%
              </div>
            </div>

            {/* Passed */}
            <div className="p-2.5 rounded-xl glass-card">
              <div className="flex items-center justify-between text-slate-400 mb-1">
                <span className="text-[10px]">Aprobadas</span>
                <CheckCircle className="w-3.5 h-3.5 text-emerald-400/80" />
              </div>
              <div className="text-lg font-bold text-emerald-400 tracking-tight">
                {metrics.passed}
              </div>
              <div className="text-[10px] text-slate-500 mt-0.5">
                {passRate}%
              </div>
            </div>

            {/* Rejected */}
            <div className="p-2.5 rounded-xl glass-card">
              <div className="flex items-center justify-between text-slate-400 mb-1">
                <span className="text-[10px]">Rechazos</span>
                <XCircle className="w-3.5 h-3.5 text-rose-400/80" />
              </div>
              <div className="text-lg font-bold text-rose-400 tracking-tight">
                {metrics.rejected}
              </div>
              <div className="text-[10px] text-slate-500 mt-0.5">
                {defectRate}%
              </div>
            </div>
          </div>

          {/* Quality Progress Bar */}
          <div className="p-2.5 rounded-xl glass-card">
            <div className="flex items-center justify-between text-[10px] font-mono mb-1.5 text-slate-400">
              <span>Rendimiento de Calidad</span>
              <span className="text-emerald-400 font-medium">{passRate}% OK</span>
            </div>
            <div className="w-full bg-slate-900/80 h-1.5 rounded-full overflow-hidden flex border border-white/5">
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

          {/* Real Hardware Telemetry Summary */}
          <div className="p-2.5 rounded-xl glass-card space-y-1.5">
            <div className="flex items-center justify-between text-[10px] font-mono text-slate-400">
              <span className="flex items-center gap-1.5">
                <Cpu className="w-3 h-3 text-cyan-400" />
                <span>Raspberry Pi SoC</span>
              </span>
              <span className="text-slate-300 font-medium">
                {piTelemetry.cpuTemp > 0 ? `${piTelemetry.cpuTemp}°C` : '--'}
              </span>
            </div>
            <div className="flex items-center justify-between text-[10px] font-mono text-slate-500">
              <span>CPU: {piTelemetry.cpuUsage > 0 ? `${piTelemetry.cpuUsage}%` : '--'}</span>
              <span>Latencia: {piTelemetry.modelLatencyMs > 0 ? `${piTelemetry.modelLatencyMs}ms` : '--'}</span>
            </div>
          </div>

          {/* Manual Trigger Action */}
          <button
            onClick={onManualTrigger}
            disabled={isTriggering || connectionStatus !== 'connected'}
            className="w-full py-2.5 px-3 rounded-xl bg-slate-800/70 hover:bg-slate-700/80 border border-white/10 text-cyan-300 text-xs font-mono font-medium flex items-center justify-center gap-2 transition active:scale-[0.98] disabled:opacity-40 disabled:cursor-not-allowed shadow-sm"
          >
            <Radio className={`w-3.5 h-3.5 ${isTriggering ? 'animate-spin text-cyan-400' : 'text-cyan-400'}`} />
            <span>{isTriggering ? 'Procesando...' : 'Disparar Captura'}</span>
          </button>
        </div>
      ) : (
        <div className="flex-1 p-2 flex flex-col items-center justify-start pt-3 space-y-3">
          <button
            onClick={onManualTrigger}
            disabled={isTriggering || connectionStatus !== 'connected'}
            title="Disparar Captura"
            className="w-10 h-10 rounded-xl bg-slate-800/70 hover:bg-slate-700/80 border border-white/10 text-cyan-300 flex items-center justify-center transition active:scale-95 disabled:opacity-40 disabled:cursor-not-allowed shadow-sm"
          >
            <Radio className={`w-4 h-4 ${isTriggering ? 'animate-spin text-cyan-400' : 'text-cyan-400'}`} />
          </button>
        </div>
      )}

      {/* 4. Footer with Settings & Connection Status */}
      <div
        className={`h-14 border-t border-white/[0.08] bg-slate-900/50 flex items-center shrink-0 ${
          isOpen ? 'p-3 justify-between' : 'p-2 justify-center'
        }`}
      >
        {isOpen ? (
          <>
            <div className="flex items-center space-x-2">
              <span
                className={`w-2 h-2 rounded-full ${
                  connectionStatus === 'connected'
                    ? 'bg-emerald-400 shadow-[0_0_6px_rgba(52,211,153,0.6)]'
                    : connectionStatus === 'reconnecting'
                    ? 'bg-amber-400 animate-pulse'
                    : 'bg-rose-400'
                }`}
              />
              <div className="flex flex-col">
                <span className="text-[11px] font-mono text-slate-300 font-medium leading-none">
                  {connectionStatus === 'connected'
                    ? 'Pi Conectada'
                    : connectionStatus === 'reconnecting'
                    ? 'Reconectando...'
                    : 'Desconectada'}
                </span>
                {connectionStatus === 'connected' && pingMs !== null && (
                  <span className="text-[9px] font-mono text-slate-500">
                    RTT {pingMs}ms
                  </span>
                )}
              </div>
            </div>

            <button
              onClick={onOpenSettings}
              title="Configuración de Red / IP"
              aria-label="Configuración de Red / IP"
              className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800/60 transition border border-transparent hover:border-white/10"
            >
              <Sliders className="w-4 h-4" />
            </button>
          </>
        ) : (
          <button
            onClick={onOpenSettings}
            title="Configuración de Red / IP"
            aria-label="Configuración de Red / IP"
            className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800/60 transition border border-transparent hover:border-white/10"
          >
            <Sliders className="w-4 h-4" />
          </button>
        )}
      </div>
    </aside>
  )
}
