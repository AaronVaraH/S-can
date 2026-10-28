import React from 'react'
import {
  Menu,
  Volume2,
  VolumeX,
  Sliders,
  Radio,
  Wifi,
  WifiOff,
  Clock,
  Sparkles
} from 'lucide-react'

export default function Navbar({
  isSidebarOpen,
  onToggleSidebar,
  activeTab,
  connectionStatus,
  pingMs,
  soundEnabled,
  onToggleSound,
  onOpenSettings,
  onManualTrigger,
  isTriggering,
  lastPrediction
}) {
  const getTabLabel = () => {
    switch (activeTab) {
      case 'camara':
        return 'Control Óptico · Inferencia en Vivo'
      case 'history':
        return 'Registro de Inspección y Calidad'
      case 'audit':
        return 'Telemetría de Hardware y Diagnóstico'
      default:
        return 'Sistema S-can'
    }
  }

  return (
    <header className="h-14 px-4 bg-slate-900/50 backdrop-blur-xl border-b border-white/[0.08] flex items-center justify-between gap-3 shrink-0 z-20 shadow-sm">
      {/* Left: Sidebar trigger and View Title */}
      <div className="flex items-center space-x-3">
        {!isSidebarOpen && (
          <button
            onClick={onToggleSidebar}
            title="Abrir panel lateral"
            aria-label="Abrir panel lateral"
            className="w-9 h-9 rounded-xl border border-white/10 bg-slate-800/60 hover:bg-slate-700/60 text-slate-200 hover:text-white flex items-center justify-center transition-all shadow-sm active:scale-95"
          >
            <Menu className="w-4 h-4" />
          </button>
        )}

        <div className="flex items-center space-x-2.5">
          {!isSidebarOpen && (
            <div className="flex items-center gap-2 mr-1">
              <div className="w-6 h-6 rounded-lg bg-gradient-to-br from-cyan-500/20 to-blue-500/20 border border-cyan-500/30 flex items-center justify-center font-mono font-bold text-xs text-cyan-300">
                S
              </div>
              <span className="font-semibold text-white text-sm tracking-tight font-sans">
                S-can
              </span>
            </div>
          )}

          <h1 className="text-xs font-mono font-semibold uppercase tracking-wider text-slate-300 flex items-center gap-2">
            <span>{getTabLabel()}</span>
          </h1>

          {/* Connection Status Pill with Real Ping */}
          <div className="hidden sm:flex items-center space-x-1.5 px-2.5 py-1 rounded-full text-[11px] font-mono border glass-pill">
            <span
              className={`w-1.5 h-1.5 rounded-full ${
                connectionStatus === 'connected'
                  ? 'bg-emerald-400 shadow-[0_0_8px_rgba(52,211,153,0.5)]'
                  : connectionStatus === 'reconnecting'
                  ? 'bg-amber-400 animate-pulse'
                  : 'bg-rose-400'
              }`}
            />
            <span className="text-slate-300 font-medium">
              {connectionStatus === 'connected'
                ? 'Raspberry Pi En Línea'
                : connectionStatus === 'reconnecting'
                ? 'Reconectando...'
                : 'Sin Conexión'}
            </span>
            {connectionStatus === 'connected' && pingMs !== null && (
              <span className="text-slate-400 border-l border-white/10 pl-1.5 ml-1">
                {pingMs} ms
              </span>
            )}
          </div>
        </div>
      </div>

      {/* Right: Actions and Status */}
      <div className="flex items-center space-x-2">
        {/* Dynamic Last Detection Pill (if any) */}
        {lastPrediction && (
          <div
            className={`hidden md:flex items-center gap-2 px-3 py-1 rounded-full text-xs font-mono border glass-pill transition-all ${
              lastPrediction.class === 'intacta'
                ? 'border-emerald-500/30 text-emerald-300 bg-emerald-950/30'
                : 'border-rose-500/30 text-rose-300 bg-rose-950/30'
            }`}
          >
            <span
              className={`w-1.5 h-1.5 rounded-full ${
                lastPrediction.class === 'intacta' ? 'bg-emerald-400' : 'bg-rose-400'
              }`}
            />
            <span className="font-semibold uppercase">{lastPrediction.class}</span>
            <span className="text-slate-400">·</span>
            <span>{(lastPrediction.confidence * 100).toFixed(1)}%</span>
          </div>
        )}

        {/* Trigger Capture Button */}
        <button
          onClick={onManualTrigger}
          disabled={isTriggering || connectionStatus !== 'connected'}
          title="Disparar captura óptica manual"
          className="px-3 py-1.5 rounded-xl border border-white/10 bg-slate-800/50 hover:bg-slate-700/60 text-slate-200 text-xs font-mono font-medium flex items-center gap-1.5 transition active:scale-95 disabled:opacity-40 disabled:cursor-not-allowed shadow-sm"
        >
          <Radio className={`w-3.5 h-3.5 ${isTriggering ? 'animate-spin text-cyan-400' : 'text-slate-400'}`} />
          <span className="hidden sm:inline">Disparar Captura</span>
        </button>

        {/* Audio Alerts Toggle */}
        <button
          onClick={onToggleSound}
          title={soundEnabled ? 'Silenciar alertas acústicas' : 'Activar alertas acústicas'}
          aria-label={soundEnabled ? 'Silenciar alertas' : 'Activar alertas'}
          className={`p-2 rounded-xl border transition-all text-xs shadow-sm ${
            soundEnabled
              ? 'bg-slate-800/60 hover:bg-slate-700/60 text-cyan-400 border-white/10'
              : 'bg-slate-900/40 text-slate-500 border-white/5'
          }`}
        >
          {soundEnabled ? <Volume2 className="w-4 h-4" /> : <VolumeX className="w-4 h-4" />}
        </button>

        {/* Settings Modal Button */}
        <button
          onClick={onOpenSettings}
          title="Configuración de Red y Umbrales"
          aria-label="Configuración de Red y Umbrales"
          className="p-2 rounded-xl border border-white/10 bg-slate-800/60 hover:bg-slate-700/60 text-slate-300 hover:text-white transition shadow-sm active:scale-95"
        >
          <Sliders className="w-4 h-4" />
        </button>
      </div>
    </header>
  )
}
