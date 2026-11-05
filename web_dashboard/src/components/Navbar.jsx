import React from 'react'
import {
  PanelLeftClose,
  PanelLeftOpen,
  Volume2,
  VolumeX,
  Sliders,
  Radio,
  Sun,
  Moon
} from 'lucide-react'

export default function Navbar({
  isSidebarOpen,
  onToggleSidebar,
  activeTab,
  connectionStatus,
  pingMs,
  soundEnabled,
  onToggleSound,
  theme = 'dark',
  onToggleTheme,
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

  const isDark = theme === 'dark'

  return (
    <header
      style={{ backgroundColor: 'var(--bg-navbar)', borderColor: 'var(--border-subtle)' }}
      className="h-14 px-4 backdrop-blur-xl border-b flex items-center justify-between gap-3 shrink-0 z-20 shadow-sm transition-colors duration-200"
    >
      {/* Left: Sidebar trigger and View Title */}
      <div className="flex items-center space-x-3 min-w-0">
        <button
          onClick={onToggleSidebar}
          title={isSidebarOpen ? 'Colapsar panel lateral' : 'Expandir panel lateral'}
          aria-label={isSidebarOpen ? 'Colapsar panel lateral' : 'Expandir panel lateral'}
          className="w-8 h-8 rounded-lg border border-brand-silver/50 dark:border-white/10 bg-white/70 dark:bg-brand-800/80 hover:bg-brand-ice dark:hover:bg-brand-umber/70 dark:hover:border-brand-sand/35 text-brand-umber dark:text-brand-silver hover:text-brand-umber dark:hover:text-brand-ice flex items-center justify-center transition-all shadow-sm active:scale-95 shrink-0"
        >
          {isSidebarOpen ? (
            <PanelLeftClose className="w-4 h-4" />
          ) : (
            <PanelLeftOpen className="w-4 h-4 text-brand-brass dark:text-brand-sand" />
          )}
        </button>

        <h1 className="text-xs font-mono font-semibold uppercase tracking-wider text-skin-primary truncate">
          {getTabLabel()}
        </h1>

        {/* Connection Status Pill with Real Ping */}
        <div className="hidden sm:flex items-center space-x-1.5 px-2.5 py-1 rounded-full text-[11px] font-mono glass-pill shrink-0">
          <span
            className={`w-1.5 h-1.5 rounded-full ${connectionStatus === 'connected'
                ? 'bg-emerald-500 dark:bg-emerald-400 shadow-[0_0_8px_rgba(16,185,129,0.5)]'
                : connectionStatus === 'reconnecting'
                  ? 'bg-amber-500 dark:bg-brand-sand animate-pulse'
                  : 'bg-rose-500 dark:bg-rose-400'
              }`}
          />
          <span className="text-skin-primary font-medium">
            {connectionStatus === 'connected'
              ? 'Raspberry Pi En Línea'
              : connectionStatus === 'reconnecting'
                ? 'Reconectando...'
                : 'Sin Conexión'}
          </span>
          {connectionStatus === 'connected' && pingMs !== null && (
            <span className="text-skin-secondary border-l border-brand-silver/50 dark:border-brand-sand/20 pl-1.5 ml-1">
              {pingMs} ms
            </span>
          )}
        </div>
      </div>

      {/* Right: Actions, Theme Switch, and Status */}
      <div className="flex items-center space-x-2">
        {/* Dynamic Last Detection Pill (if any) */}
        {lastPrediction && (
          <div
            className={`hidden md:flex items-center gap-2 px-3 py-1 rounded-full text-xs font-mono border transition-all ${lastPrediction.class === 'intacta'
                ? 'border-emerald-600/30 dark:border-emerald-500/30 text-emerald-800 dark:text-emerald-300 bg-emerald-500/10 dark:bg-emerald-950/40'
                : 'border-rose-600/30 dark:border-rose-500/30 text-rose-800 dark:text-rose-300 bg-rose-500/10 dark:bg-rose-950/40'
              }`}
          >
            <span
              className={`w-1.5 h-1.5 rounded-full ${lastPrediction.class === 'intacta'
                  ? 'bg-emerald-600 dark:bg-emerald-400'
                  : 'bg-rose-600 dark:bg-rose-400'
                }`}
            />
            <span className="font-semibold uppercase">{lastPrediction.class}</span>
            <span className="opacity-60">·</span>
            <span>{(lastPrediction.confidence * 100).toFixed(1)}%</span>
          </div>
        )}

        {/* Trigger Capture Button (WCAG AAA Brand CTA) */}
        <button
          onClick={onManualTrigger}
          disabled={isTriggering || connectionStatus !== 'connected'}
          title="Disparar captura óptica manual"
          className="btn-brand px-3 py-1.5 rounded-xl text-xs font-mono font-semibold flex items-center gap-1.5 active:scale-95 disabled:opacity-40 disabled:cursor-not-allowed shadow-sm"
        >
          <Radio className={`w-3.5 h-3.5 ${isTriggering ? 'animate-spin' : ''}`} />
          <span className="hidden sm:inline">Disparar Captura</span>
        </button>

        {/* Theme Switch (Light / Dark Mode) */}
        <button
          onClick={onToggleTheme}
          role="switch"
          aria-checked={isDark}
          title={isDark ? 'Cambiar a modo claro (Light Mode)' : 'Cambiar a modo oscuro (Dark Mode)'}
          aria-label="Cambiar tema visual"
          className="relative inline-flex items-center h-8 w-14 rounded-xl p-1 border border-brand-silver/60 dark:border-white/10 bg-brand-ice/70 dark:bg-brand-950/90 transition-colors duration-200 focus:outline-none focus:ring-2 focus:ring-brand-brass/50 shadow-inner shrink-0"
        >
          <span className="sr-only">Cambiar tema</span>
          <Sun
            className={`w-3.5 h-3.5 ml-0.5 transition-opacity duration-200 ${isDark ? 'text-brand-silver/40' : 'text-brand-umber'
              }`}
          />
          <Moon
            className={`w-3.5 h-3.5 ml-auto mr-0.5 transition-opacity duration-200 ${isDark ? 'text-brand-sand' : 'text-brand-umber/35'
              }`}
          />
          <span
            className={`absolute top-1 bottom-1 w-6 rounded-lg shadow-sm flex items-center justify-center transition-transform duration-200 ease-out ${isDark
                ? 'translate-x-6 bg-brand-umber border border-brand-sand/40 text-brand-ice'
                : 'translate-x-0 bg-brand-umber text-brand-ice'
              }`}
          >
            {isDark ? (
              <Moon className="w-3 h-3 text-brand-sand" />
            ) : (
              <Sun className="w-3 h-3 text-brand-ice" />
            )}
          </span>
        </button>

        {/* Audio Alerts Toggle */}
        <button
          onClick={onToggleSound}
          title={soundEnabled ? 'Silenciar alertas acústicas' : 'Activar alertas acústicas'}
          aria-label={soundEnabled ? 'Silenciar alertas' : 'Activar alertas'}
          className={`p-2 rounded-xl border transition-all text-xs shadow-sm ${soundEnabled
                ? 'bg-white/80 dark:bg-brand-800/80 hover:bg-brand-ice dark:hover:bg-brand-umber/70 text-brand-umber dark:text-brand-sand border-brand-silver/60 dark:border-white/10'
                : 'bg-white/40 dark:bg-brand-900/40 text-skin-muted border-brand-silver/30 dark:border-white/5'
          }`}
        >
          {soundEnabled ? <Volume2 className="w-4 h-4" /> : <VolumeX className="w-4 h-4" />}
        </button>

        {/* Settings Modal Button */}
        <button
          onClick={onOpenSettings}
          title="Configuración de Red y Umbrales"
          aria-label="Configuración de Red y Umbrales"
          className="p-2 rounded-xl border border-brand-silver/60 dark:border-white/10 bg-white/80 dark:bg-brand-800/80 hover:bg-brand-ice dark:hover:bg-brand-umber/70 dark:hover:border-brand-sand/35 text-brand-umber dark:text-brand-silver hover:text-brand-umber dark:hover:text-brand-ice transition shadow-sm active:scale-95"
        >
          <Sliders className="w-4 h-4" />
        </button>
      </div>
    </header>
  )
}
