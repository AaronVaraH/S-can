import React, { useRef, useState, useEffect } from 'react'
import {
  Layers,
  Maximize2,
  AlertCircle,
  ShieldCheck,
  ShieldAlert,
  Clock,
  Zap,
  Activity,
  Camera,
  Radio,
  ChevronRight,
  Eye,
  CheckCircle2,
  XCircle,
  ScanLine
} from 'lucide-react'

export default function VideoFeed({
  streamUrl,
  isConnected,
  lastPrediction,
  modelLatencyMs = 0,
  recentDetections = [],
  onManualTrigger,
  isTriggering = false
}) {
  const [showBbox, setShowBbox] = useState(true)
  const [streamError, setStreamError] = useState(false)
  const [selectedDetection, setSelectedDetection] = useState(null)
  const [triggerFlash, setTriggerFlash] = useState(false)
  const containerRef = useRef(null)

  // Reset stream error on streamUrl or connection change
  useEffect(() => {
    setStreamError(false)
  }, [streamUrl, isConnected])

  // Trigger optical flash simulation when a real prediction arrives
  useEffect(() => {
    if (lastPrediction) {
      setTriggerFlash(true)
      const timer = setTimeout(() => setTriggerFlash(false), 180)
      return () => clearTimeout(timer)
    }
  }, [lastPrediction])

  const activeSample = selectedDetection || lastPrediction
  const isDefect =
    activeSample?.class === 'dañada' ||
    activeSample?.class === 'abollada' ||
    activeSample?.class === 'defectuosa'

  return (
    <div className="flex-1 w-full h-full flex flex-col lg:flex-row gap-3 min-h-0 overflow-hidden select-none">
      {/* 1. Main Optical Inspection Viewport (Left / Center) */}
      <div className="flex-1 flex flex-col min-w-0 h-full relative rounded-2xl glass-panel overflow-hidden border border-white/10 shadow-glass">
        {/* Viewport Top Bar */}
        <div className="h-10 px-4 bg-slate-900/60 border-b border-white/[0.08] flex items-center justify-between text-xs font-mono text-slate-300 z-20">
          <div className="flex items-center space-x-2.5">
            <span
              className={`w-2 h-2 rounded-full ${
                isConnected && !streamError
                  ? 'bg-emerald-400 shadow-[0_0_8px_rgba(52,211,153,0.6)]'
                  : 'bg-rose-400'
              }`}
            />
            <span className="font-semibold text-slate-200">
              {isConnected && !streamError ? 'Sensor Óptico MJPEG' : 'Sensor En Espera'}
            </span>
            <span className="text-slate-600">|</span>
            <span className="text-slate-400">
              {modelLatencyMs > 0 ? `${modelLatencyMs} ms` : 'Standby'}
            </span>
          </div>

          <div className="flex items-center space-x-2">
            {/* Toggle Bounding Box */}
            <button
              onClick={() => setShowBbox(!showBbox)}
              className={`px-2.5 py-1 rounded-lg text-[11px] font-mono flex items-center gap-1.5 transition border ${
                showBbox
                  ? 'bg-cyan-500/15 text-cyan-300 border-cyan-500/30'
                  : 'bg-slate-800/40 text-slate-500 border-white/5'
              }`}
            >
              <Layers className="w-3.5 h-3.5" />
              <span>Bounding Box</span>
            </button>
          </div>
        </div>

        {/* Viewport Display Area */}
        <div
          ref={containerRef}
          className="relative flex-1 w-full bg-[#050811] flex items-center justify-center overflow-hidden optical-grid"
        >
          {/* Optical Exposure Flash on Ingestion/Trigger */}
          {triggerFlash && (
            <div className="absolute inset-0 bg-white/10 pointer-events-none z-30 transition-opacity duration-150" />
          )}

          {/* Precision Alignment Markings (Technical, Not Arcade) */}
          <div className="absolute inset-0 pointer-events-none z-10 opacity-30">
            {/* Center target crosshair */}
            <div className="absolute top-1/2 left-0 right-0 h-px bg-slate-600/40" />
            <div className="absolute left-1/2 top-0 bottom-0 w-px bg-slate-600/40" />
            
            {/* Subtly calibrated ROI zone */}
            <div className="absolute inset-[15%] border border-dashed border-slate-600/30 rounded-lg" />
            
            {/* Corner millimeter indicators */}
            <span className="absolute top-2 left-2 text-[10px] font-mono text-slate-500">X: 0.00</span>
            <span className="absolute bottom-2 right-2 text-[10px] font-mono text-slate-500">1280 × 720</span>
          </div>

          {/* Real Live MJPEG Stream from Raspberry Pi */}
          {isConnected && !streamError ? (
            <img
              src={streamUrl}
              alt="Transmisión óptica en vivo"
              onError={() => setStreamError(true)}
              className="w-full h-full object-contain relative z-10"
            />
          ) : (
            /* Clean Empty / Standby State (NO TOY MOCK CAN) */
            <div className="flex flex-col items-center justify-center p-8 text-center z-10 max-w-sm">
              <div className="w-14 h-14 rounded-2xl bg-slate-900/80 border border-white/10 flex items-center justify-center text-slate-400 mb-3 shadow-inner">
                <Camera className="w-7 h-7 text-slate-500" />
              </div>
              <h3 className="text-sm font-semibold text-slate-200">
                {isConnected ? 'Stream en Espera de Señal' : 'Sensor Óptico Desconectado'}
              </h3>
              <p className="text-xs text-slate-400 font-mono mt-1.5 leading-relaxed">
                {isConnected
                  ? 'Esperando fotogramas de la cámara o trigger en el puerto de video.'
                  : 'Verifica la IP y que el backend en la Raspberry Pi esté en ejecución.'}
              </p>
              <div className="mt-4 px-3 py-1.5 rounded-lg bg-slate-900/60 border border-white/5 text-[11px] font-mono text-slate-400">
                Feed: {streamUrl}
              </div>
            </div>
          )}

          {/* Dynamic Technical Bounding Box Overlay */}
          {showBbox && lastPrediction && lastPrediction.bbox && (
            <div
              className={`absolute z-20 pointer-events-none border-2 transition-all duration-200 rounded-sm ${
                isDefect
                  ? 'border-rose-500 shadow-[0_0_16px_rgba(244,63,94,0.3)]'
                  : 'border-emerald-500 shadow-[0_0_16px_rgba(16,185,129,0.3)]'
              }`}
              style={{
                left: `${lastPrediction.bbox[0] * 100}%`,
                top: `${lastPrediction.bbox[1] * 100}%`,
                width: `${lastPrediction.bbox[2] * 100}%`,
                height: `${lastPrediction.bbox[3] * 100}%`
              }}
            >
              {/* Technical Class Badge */}
              <div
                className={`absolute -top-7 left-0 px-2 py-0.5 rounded text-[10px] font-mono font-bold text-white uppercase tracking-wider flex items-center gap-1.5 shadow-md ${
                  isDefect ? 'bg-rose-600' : 'bg-emerald-600'
                }`}
              >
                <span>{lastPrediction.class}</span>
                <span>{(lastPrediction.confidence * 100).toFixed(1)}%</span>
              </div>
            </div>
          )}
        </div>

        {/* Viewport Bottom Status Bar */}
        <div className="h-10 px-4 bg-slate-900/60 border-t border-white/[0.08] flex items-center justify-between text-[11px] font-mono text-slate-400 z-20">
          <div className="flex items-center space-x-3">
            <span>Resolución: 1280 × 720</span>
            <span className="text-slate-600">•</span>
            <span>Trigger: Solenoide Óptico</span>
          </div>

          <div className="flex items-center space-x-2">
            <span className="text-slate-500">Muestras hoy:</span>
            <strong className="text-slate-200 font-bold">{recentDetections.length}</strong>
          </div>
        </div>
      </div>

      {/* 2. Side Inspection Rail (Right Cockpit Panel) */}
      <div className="w-full lg:w-80 flex flex-col gap-3 shrink-0 h-full overflow-hidden">
        {/* Active Inspection Verdict Card */}
        <div className="glass-panel p-4 rounded-2xl flex flex-col space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-[10px] font-mono font-semibold uppercase tracking-wider text-slate-400">
              Dictamen en Tiempo Real
            </span>
            {activeSample && (
              <span className="text-[10px] font-mono text-slate-400">
                Muestra #{activeSample.id}
              </span>
            )}
          </div>

          {!activeSample ? (
            /* Idle State before any cans are scanned */
            <div className="p-5 rounded-xl bg-slate-900/40 border border-white/5 text-center flex flex-col items-center justify-center">
              <ScanLine className="w-6 h-6 text-slate-500 mb-2 animate-pulse" />
              <p className="text-xs font-medium text-slate-300">En Espera de Muestra</p>
              <p className="text-[11px] text-slate-500 font-mono mt-1">
                La inferencia se activará cuando pase una lata frente al sensor.
              </p>
            </div>
          ) : (
            /* Live Verdict State */
            <div
              className={`p-3.5 rounded-xl border transition-all ${
                isDefect
                  ? 'bg-rose-950/40 border-rose-500/30 text-rose-200 shadow-sm'
                  : 'bg-emerald-950/40 border-emerald-500/30 text-emerald-200 shadow-sm'
              }`}
            >
              <div className="flex items-start justify-between">
                <div className="flex items-center space-x-2.5">
                  <div
                    className={`w-8 h-8 rounded-lg flex items-center justify-center border ${
                      isDefect
                        ? 'bg-rose-900/50 border-rose-500/40 text-rose-300'
                        : 'bg-emerald-900/50 border-emerald-500/40 text-emerald-300'
                    }`}
                  >
                    {isDefect ? (
                      <ShieldAlert className="w-4 h-4" />
                    ) : (
                      <ShieldCheck className="w-4 h-4" />
                    )}
                  </div>
                  <div>
                    <h4 className="text-sm font-bold tracking-tight uppercase font-mono">
                      {isDefect ? 'Lata Rechazada' : 'Lata Conforme'}
                    </h4>
                    <p className="text-[11px] font-mono opacity-80">
                      {activeSample.defectType || (isDefect ? 'Defecto detectado' : 'Superficie OK')}
                    </p>
                  </div>
                </div>

                <div className="text-right">
                  <span className="text-base font-bold font-mono">
                    {(activeSample.confidence * 100).toFixed(1)}%
                  </span>
                  <span className="block text-[10px] font-mono opacity-70">Certeza AI</span>
                </div>
              </div>

              {/* Progress Confidence Bar */}
              <div className="w-full bg-slate-900/80 h-1.5 rounded-full overflow-hidden mt-3 border border-white/5">
                <div
                  className={`h-full rounded-full transition-all duration-300 ${
                    isDefect ? 'bg-rose-500' : 'bg-emerald-500'
                  }`}
                  style={{ width: `${activeSample.confidence * 100}%` }}
                />
              </div>

              <div className="mt-2.5 pt-2 border-t border-white/5 flex items-center justify-between text-[10px] font-mono opacity-75">
                <span>Latencia: {activeSample.latency || modelLatencyMs || 22} ms</span>
                <span>Hora: {activeSample.time}</span>
              </div>
            </div>
          )}

          {/* Trigger Action in Panel */}
          <button
            onClick={onManualTrigger}
            disabled={isTriggering || !isConnected}
            className="w-full py-2 px-3 rounded-xl bg-slate-800/80 hover:bg-slate-700/80 border border-white/10 text-cyan-300 text-xs font-mono font-medium flex items-center justify-center gap-2 transition active:scale-[0.98] disabled:opacity-40 shadow-sm"
          >
            <Radio className={`w-3.5 h-3.5 ${isTriggering ? 'animate-spin' : ''}`} />
            <span>{isTriggering ? 'Procesando...' : 'Capturar Muestra'}</span>
          </button>
        </div>

        {/* Filmstrip de Auditoría Rápida (Recent Cans in Current Session) */}
        <div className="glass-panel p-4 rounded-2xl flex-1 flex flex-col min-h-0">
          <div className="flex items-center justify-between mb-2.5">
            <span className="text-[10px] font-mono font-semibold uppercase tracking-wider text-slate-400">
              Muestras Recientes
            </span>
            <span className="text-[10px] font-mono text-slate-500">
              {recentDetections.length} registradas
            </span>
          </div>

          <div className="flex-1 overflow-y-auto space-y-1.5 pr-0.5">
            {recentDetections.length === 0 ? (
              <div className="p-6 text-center text-slate-500 font-mono text-xs flex flex-col items-center justify-center h-full">
                <p>No hay detecciones aún en esta sesión.</p>
              </div>
            ) : (
              recentDetections.map((item) => {
                const itemIsDefect =
                  item.class === 'dañada' ||
                  item.class === 'abollada' ||
                  item.class === 'defectuosa'
                const isSelected = selectedDetection?.id === item.id

                return (
                  <div
                    key={item.id}
                    onClick={() =>
                      setSelectedDetection(isSelected ? null : item)
                    }
                    className={`p-2 rounded-xl border flex items-center justify-between text-xs font-mono cursor-pointer transition-all ${
                      isSelected
                        ? 'bg-slate-700/60 border-cyan-500/50 shadow-inner'
                        : 'glass-card glass-card-hover'
                    }`}
                  >
                    <div className="flex items-center space-x-2">
                      <div
                        className={`w-2 h-2 rounded-full ${
                          itemIsDefect ? 'bg-rose-400' : 'bg-emerald-400'
                        }`}
                      />
                      <span className="font-semibold text-slate-200">#{item.id}</span>
                      <span className="text-[11px] text-slate-400 truncate max-w-[110px]">
                        {item.defectType || (itemIsDefect ? 'Rechazo' : 'OK')}
                      </span>
                    </div>

                    <div className="flex items-center space-x-2">
                      <span
                        className={`text-[11px] font-bold ${
                          itemIsDefect ? 'text-rose-400' : 'text-emerald-400'
                        }`}
                      >
                        {(item.confidence * 100).toFixed(0)}%
                      </span>
                      <ChevronRight className="w-3.5 h-3.5 text-slate-500" />
                    </div>
                  </div>
                )
              })
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
