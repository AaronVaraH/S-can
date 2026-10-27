import React from 'react'
import {
  Menu,
  Volume2,
  VolumeX,
  Sliders,
  Camera,
  Boxes,
  CheckCircle,
  XCircle,
  Percent,
  Radio,
  Zap,
  Activity
} from 'lucide-react'

export default function Navbar({
  isSidebarOpen,
  onToggleSidebar,
  activeTab,
  metrics,
  connectionStatus,
  isSimulator,
  onToggleSimulator,
  soundEnabled,
  onToggleSound,
  onOpenSettings,
  onManualTrigger,
  lastPrediction
}) {
  const defectRate = metrics.total > 0 ? ((metrics.rejected / metrics.total) * 100).toFixed(1) : '0.0'

  return (
    <header className="h-14 px-4 bg-[#0a101d]/90 border-b border-slate-800/80 backdrop-blur-md flex items-center justify-between gap-3 shrink-0 z-20">
      {/* Left: Circle/Ellipse Hamburger Menu Button matching wireframe */}
      <div className="flex items-center space-x-3">
        {!isSidebarOpen && (
          <button
            onClick={onToggleSidebar}
            title="Abrir menú lateral"
            className="w-10 h-10 rounded-full border border-slate-700/80 bg-slate-900/90 hover:bg-slate-800 text-slate-200 hover:text-cyan-400 flex items-center justify-center transition-all shadow-md active:scale-95 group"
          >
            <Menu className="w-5 h-5 group-hover:scale-110 transition-transform" />
          </button>
        )}

        {/* View Title or Brand Indicator */}
        <div className="flex items-center space-x-2">
          {!isSidebarOpen && (
            <div className="font-bold text-white text-sm font-sans flex items-center gap-1.5 mr-2">
              <span className="w-2 h-2 rounded-full bg-cyan-400 shadow-[0_0_8px_#22d3ee]" />
              <span>S-can</span>
            </div>
          )}
          <span className="text-xs font-mono font-bold uppercase tracking-wider text-slate-300">
            {activeTab === 'camara'
              ? 'Feed Óptico · Raspberry Pi'
              : activeTab === 'history'
              ? 'Historial de Inspección'
              : 'Auditoría y Telemetría'}
          </span>
          <span className="hidden sm:inline-block text-[10px] px-2 py-0.5 rounded font-mono bg-slate-900 border border-slate-800 text-slate-400">
            {connectionStatus === 'connected' ? 'LIVE 30FPS' : 'STANDBY'}
          </span>
        </div>
      </div>

      {/* Center: Clean navbar metrics */}
      <div className="hidden md:flex items-center space-x-4 px-3 py-1 rounded-full bg-slate-900/70 border border-slate-800/80 text-xs font-mono">
        <div className="flex items-center space-x-1.5 text-slate-400">
          <Boxes className="w-3.5 h-3.5 text-cyan-400" />
          <span>Total:</span>
          <strong className="text-white">{metrics.total}</strong>
        </div>

        <span className="text-slate-700">•</span>

        <div className="flex items-center space-x-1.5 text-slate-400">
          <CheckCircle className="w-3.5 h-3.5 text-emerald-400" />
          <span>OK:</span>
          <strong className="text-emerald-400">{metrics.passed}</strong>
        </div>

        <span className="text-slate-700">•</span>

        <div className="flex items-center space-x-1.5 text-slate-400">
          <XCircle className="w-3.5 h-3.5 text-rose-400" />
          <span>Defectos:</span>
          <strong className="text-rose-400">{metrics.rejected}</strong>
        </div>

        <span className="text-slate-700">•</span>

        <div className="flex items-center space-x-1.5 text-slate-400">
          <Percent className="w-3.5 h-3.5 text-amber-400" />
          <span>Descarte:</span>
          <strong className="text-amber-400">{defectRate}%</strong>
        </div>
      </div>

      {/* Right: Quick Controls (Sound, Manual Scan, Settings) */}
      <div className="flex items-center space-x-2">
        {/* Subtle Verdict Pill if prediction exists */}
        {lastPrediction && (
          <div
            className={`hidden lg:flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-mono font-semibold border transition-all ${
              lastPrediction.class === 'intacta'
                ? 'bg-emerald-950/40 border-emerald-700/60 text-emerald-300'
                : 'bg-rose-950/40 border-rose-700/60 text-rose-300 animate-pulse'
            }`}
          >
            <span
              className={`w-2 h-2 rounded-full ${
                lastPrediction.class === 'intacta' ? 'bg-emerald-400' : 'bg-rose-400'
              }`}
            />
            <span>
              {lastPrediction.class.toUpperCase()} · {(lastPrediction.confidence * 100).toFixed(1)}%
            </span>
          </div>
        )}

        {/* Audio Toggle */}
        <button
          onClick={onToggleSound}
          title={soundEnabled ? "Silenciar alarmas" : "Activar sonido"}
          className={`p-2 rounded-lg border text-xs transition ${
            soundEnabled
              ? 'bg-slate-900/80 hover:bg-slate-800 text-cyan-400 border-slate-700/80'
              : 'bg-slate-900/40 hover:bg-slate-900 text-slate-500 border-slate-800'
          }`}
        >
          {soundEnabled ? <Volume2 className="w-4 h-4" /> : <VolumeX className="w-4 h-4" />}
        </button>

        {/* Settings Modal Button */}
        <button
          onClick={onOpenSettings}
          title="Configuración de Red / Backend"
          className="p-2 rounded-lg bg-slate-900/80 hover:bg-slate-800 border border-slate-700/80 text-slate-300 hover:text-white transition"
        >
          <Sliders className="w-4 h-4" />
        </button>
      </div>
    </header>
  )
}
