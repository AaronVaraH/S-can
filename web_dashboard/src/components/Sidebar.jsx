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
      style={{ backgroundColor: 'var(--bg-sidebar)', borderColor: 'var(--border-subtle)' }}
      className={`h-screen flex flex-col backdrop-blur-2xl border-r transition-all duration-300 ease-in-out z-30 select-none ${isOpen ? 'w-72 min-w-[288px]' : 'w-16 min-w-[64px]'
        }`}
    >
      {/* 1. Header with Logo and Brand Name (Height h-14 matches Navbar, no box around logo) */}
      <div
        style={{ borderColor: 'var(--border-subtle)' }}
      className={`h-14 border-b flex items-center shrink-0 ${isOpen ? 'px-4 space-x-3' : 'justify-center px-2'
        }`}
      >
      <img
        src="/logo.png"
        alt="S-can Logo"
        className="w-8 h-8 object-contain scale-125 shrink-0 filter drop-shadow-[0_0_8px_rgba(183,161,129,0.45)]"
      />
      {isOpen && (
        <div className="flex flex-col truncate">
          <span className="text-sm font-bold tracking-tight text-skin-primary font-sans truncate leading-tight">
            S-Can
          </span>
          <span className="text-[10px] font-mono text-brand-brass dark:text-brand-sand tracking-wider uppercase leading-none">
            Optical QC
          </span>
        </div>
      )}
    </div>

      {/* 2. Navigation items */ }
  <div
    style={{ borderColor: 'var(--border-subtle)' }}
    className={`p-3 space-y-1 border-b ${!isOpen ? 'px-2' : ''}`}
  >
    {isOpen && (
      <div className="px-3 py-1 text-[10px] font-mono font-semibold uppercase tracking-wider text-skin-muted">
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
          className={`w-full flex items-center rounded-xl text-xs transition-all ${isOpen ? 'space-x-3 px-3.5 py-2.5' : 'justify-center py-2.5 px-0'
            } ${isActive
              ? 'bg-brand-ice/80 dark:bg-brand-umber/55 text-brand-umber dark:text-brand-ice border border-brand-brass/40 dark:border-brand-sand/35 shadow-sm font-semibold'
              : 'text-skin-secondary hover:text-skin-primary hover:bg-brand-ice/40 dark:hover:bg-brand-umber/25 border border-transparent'
            }`}
        >
          <div
            className={`w-7 h-7 rounded-lg flex items-center justify-center border transition-colors shrink-0 ${isActive
              ? 'bg-brand-umber dark:bg-brand-sand/20 border-brand-umber dark:border-brand-sand/40 text-brand-ice dark:text-brand-sand'
              : 'bg-white/70 dark:bg-brand-800/80 border-brand-silver/50 dark:border-white/5 text-skin-secondary'
              }`}
          >
            <Icon className="w-3.5 h-3.5" />
          </div>
          {
            isOpen && (
              <>
                <div className="flex flex-col text-left truncate">
                  <span className="font-sans font-semibold text-skin-primary text-xs truncate">
                    {item.label}
                  </span>
                  <span className="text-[10px] text-skin-muted font-mono truncate">
                    {item.desc}
                  </span>
                </div>
                {isActive && (
                  <span className="ml-auto w-1.5 h-1.5 rounded-full bg-brand-umber dark:bg-brand-sand shrink-0" />
                )}
              </>
            )
          }
        </button>
      )
    })}
  </div >

  {/* 3. Real Batch Metrics (Zero Mock Data) */ }
  {
    isOpen ? (
      <div className="flex-1 p-3.5 overflow-y-auto space-y-3">
        <div className="flex items-center justify-between">
          <span className="text-[10px] font-mono font-semibold uppercase tracking-wider text-skin-secondary">
            Lote Actual
          </span>
          {metrics.total > 0 && (
            <button
              onClick={onResetMetrics}
              title="Reiniciar contadores de inspección"
              className="text-[10px] font-mono text-skin-muted hover:text-skin-primary flex items-center gap-1 transition"
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
            <div className="flex items-center justify-between text-skin-secondary mb-1">
              <span className="text-[10px]">Total</span>
              <Boxes className="w-3.5 h-3.5 text-brand-brass dark:text-brand-sand" />
            </div>
            <div className="text-xl font-bold text-skin-primary tracking-tight">
              {metrics.total}
            </div>
          </div>

          {/* Defect Rate */}
          <div className="p-2.5 rounded-xl glass-card">
            <div className="flex items-center justify-between text-skin-secondary mb-1">
              <span className="text-[10px]">Descarte</span>
              <Percent className="w-3.5 h-3.5 text-brand-brass dark:text-brand-sand" />
            </div>
            <div className="text-xl font-bold text-brand-umber dark:text-brand-sand tracking-tight">
              {defectRate}%
            </div>
          </div>

          {/* Passed */}
          <div className="p-2.5 rounded-xl glass-card">
            <div className="flex items-center justify-between text-skin-secondary mb-1">
              <span className="text-[10px]">Aprobadas</span>
              <CheckCircle className="w-3.5 h-3.5 text-emerald-600 dark:text-emerald-400" />
            </div>
            <div className="text-lg font-bold text-emerald-700 dark:text-emerald-400 tracking-tight">
              {metrics.passed}
            </div>
            <div className="text-[10px] text-skin-muted mt-0.5">
              {passRate}%
            </div>
          </div>

          {/* Rejected */}
          <div className="p-2.5 rounded-xl glass-card">
            <div className="flex items-center justify-between text-skin-secondary mb-1">
              <span className="text-[10px]">Rechazos</span>
              <XCircle className="w-3.5 h-3.5 text-rose-600 dark:text-rose-400" />
            </div>
            <div className="text-lg font-bold text-rose-700 dark:text-rose-400 tracking-tight">
              {metrics.rejected}
            </div>
            <div className="text-[10px] text-skin-muted mt-0.5">
              {defectRate}%
            </div>
          </div>
        </div>

        {/* Quality Progress Bar */}
        <div className="p-2.5 rounded-xl glass-card">
          <div className="flex items-center justify-between text-[10px] font-mono mb-1.5 text-skin-secondary">
            <span>Rendimiento de Calidad</span>
            <span className="text-emerald-700 dark:text-emerald-400 font-semibold">{passRate}% OK</span>
          </div>
          <div className="w-full bg-brand-silver/30 dark:bg-brand-950/90 h-1.5 rounded-full overflow-hidden flex border border-brand-silver/40 dark:border-white/5">
            <div
              className="bg-emerald-600 dark:bg-emerald-500 h-full transition-all duration-300"
              style={{ width: `${passRate}%` }}
            />
            <div
              className="bg-rose-600 dark:bg-rose-500 h-full transition-all duration-300"
              style={{ width: `${defectRate}%` }}
            />
          </div>
        </div>

        {/* Real Hardware Telemetry Summary */}
        <div className="p-2.5 rounded-xl glass-card space-y-1.5">
          <div className="flex items-center justify-between text-[10px] font-mono text-skin-secondary">
            <span className="flex items-center gap-1.5">
              <Cpu className="w-3 h-3 text-brand-brass dark:text-brand-sand" />
              <span>Raspberry Pi SoC</span>
            </span>
            <span className="text-skin-primary font-semibold">
              {piTelemetry.cpuTemp > 0 ? `${piTelemetry.cpuTemp}°C` : '--'}
            </span>
          </div>
          <div className="flex items-center justify-between text-[10px] font-mono text-skin-muted">
            <span>CPU: {piTelemetry.cpuUsage > 0 ? `${piTelemetry.cpuUsage}%` : '--'}</span>
            <span>Latencia: {piTelemetry.modelLatencyMs > 0 ? `${piTelemetry.modelLatencyMs}ms` : '--'}</span>
          </div>
        </div>

        {/* Manual Trigger Action (WCAG AAA Brand CTA) */}
        <button
          onClick={onManualTrigger}
          disabled={isTriggering || connectionStatus !== 'connected'}
          className="btn-brand w-full py-2.5 px-3 rounded-xl text-xs font-mono font-semibold flex items-center justify-center gap-2 active:scale-[0.98] disabled:opacity-40 disabled:cursor-not-allowed shadow-sm"
        >
          <Radio className={`w-3.5 h-3.5 ${isTriggering ? 'animate-spin' : ''}`} />
          <span>{isTriggering ? 'Procesando...' : 'Disparar Captura'}</span>
        </button>
      </div>
    ) : (
      <div className="flex-1 p-2 flex flex-col items-center justify-start pt-3 space-y-3">
        <button
          onClick={onManualTrigger}
          disabled={isTriggering || connectionStatus !== 'connected'}
          title="Disparar Captura"
          className="btn-brand w-10 h-10 rounded-xl flex items-center justify-center active:scale-95 disabled:opacity-40 disabled:cursor-not-allowed shadow-sm"
        >
          <Radio className={`w-4 h-4 ${isTriggering ? 'animate-spin' : ''}`} />
        </button>
      </div>
    )
  }

  {/* 4. Footer with Settings & Connection Status */ }
  <div
    style={{ borderColor: 'var(--border-subtle)' }}
    className={`h-14 border-t bg-brand-ice/25 dark:bg-brand-900/60 flex items-center shrink-0 ${isOpen ? 'p-3 justify-between' : 'p-2 justify-center'
      }`}
  >
    {isOpen ? (
      <>
        <div className="flex items-center space-x-2">
          <span
            className={`w-2 h-2 rounded-full ${connectionStatus === 'connected'
              ? 'bg-emerald-500 dark:bg-emerald-400 shadow-[0_0_6px_rgba(16,185,129,0.6)]'
              : connectionStatus === 'reconnecting'
                ? 'bg-amber-500 dark:bg-brand-sand animate-pulse'
                : 'bg-rose-500 dark:bg-rose-400'
              }`}
          />
          <div className="flex flex-col">
            <span className="text-[11px] font-mono text-skin-primary font-medium leading-none">
              {connectionStatus === 'connected'
                ? 'Pi Conectada'
                : connectionStatus === 'reconnecting'
                  ? 'Reconectando...'
                  : 'Desconectada'}
            </span>
            {connectionStatus === 'connected' && pingMs !== null && (
              <span className="text-[9px] font-mono text-skin-muted">
                RTT {pingMs}ms
              </span>
            )}
          </div>
        </div>

        <button
          onClick={onOpenSettings}
          title="Configuración de Red / IP"
          aria-label="Configuración de Red / IP"
          className="p-1.5 rounded-lg text-skin-secondary hover:text-skin-primary hover:bg-brand-ice/60 dark:hover:bg-brand-umber/50 transition border border-transparent hover:border-brand-silver/50 dark:hover:border-brand-sand/25"
        >
          <Sliders className="w-4 h-4" />
        </button>
      </>
    ) : (
      <button
        onClick={onOpenSettings}
        title="Configuración de Red / IP"
        aria-label="Configuración de Red / IP"
        className="p-1.5 rounded-lg text-skin-secondary hover:text-skin-primary hover:bg-brand-ice/60 dark:hover:bg-brand-umber/50 transition border border-transparent hover:border-brand-silver/50 dark:hover:border-brand-sand/25"
      >
        <Sliders className="w-4 h-4" />
      </button>
    )}
  </div>
    </aside >
  )
}
