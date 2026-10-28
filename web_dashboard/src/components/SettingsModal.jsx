import React, { useState } from 'react'
import {
  X,
  Sliders,
  Check,
  AlertCircle,
  Wifi,
  RefreshCw,
  Server
} from 'lucide-react'

export default function SettingsModal({
  isOpen,
  onClose,
  backendUrl,
  onSaveBackendUrl,
  confidenceThreshold,
  onSaveThreshold,
  onTestConnection,
  isTestingConnection
}) {
  const [localUrl, setLocalUrl] = useState(backendUrl)
  const [localThreshold, setLocalThreshold] = useState(confidenceThreshold)
  const [testResult, setTestResult] = useState(null)

  if (!isOpen) return null

  const handleTest = async () => {
    setTestResult(null)
    const result = await onTestConnection(localUrl)
    setTestResult(result)
  }

  const handleSave = () => {
    onSaveBackendUrl(localUrl)
    onSaveThreshold(localThreshold)
    onClose()
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-md transition-all">
      <div className="glass-dock max-w-md w-full p-6 rounded-3xl border border-white/10 shadow-2xl relative text-slate-100 font-sans">
        {/* Close Button */}
        <button
          onClick={onClose}
          aria-label="Cerrar ventana"
          className="absolute top-5 right-5 p-1.5 rounded-xl bg-slate-800/60 hover:bg-slate-700/60 border border-white/10 text-slate-400 hover:text-white transition shadow-sm"
        >
          <X className="w-4 h-4" />
        </button>

        {/* Modal Title */}
        <div className="flex items-center space-x-3 mb-5">
          <div className="p-2.5 rounded-xl bg-cyan-500/15 text-cyan-300 border border-cyan-500/30">
            <Sliders className="w-5 h-5" />
          </div>
          <div>
            <h3 className="text-sm font-bold text-white font-mono">
              Configuración del Sistema
            </h3>
            <p className="text-xs text-slate-400 font-mono">
              Parámetros de enlace con la Raspberry Pi
            </p>
          </div>
        </div>

        {/* Settings Body */}
        <div className="space-y-4">
          {/* Backend IP URL */}
          <div>
            <label className="block text-xs font-mono text-slate-300 mb-1.5 font-medium">
              Dirección IP del Servidor FastAPI
            </label>
            <div className="flex gap-2">
              <input
                type="text"
                value={localUrl}
                onChange={(e) => setLocalUrl(e.target.value)}
                placeholder="http://192.168.1.42:8000"
                className="flex-1 bg-slate-900/80 border border-white/10 rounded-xl px-3 py-2 text-xs font-mono text-cyan-300 placeholder:text-slate-600 focus:outline-none focus:border-cyan-500/60 shadow-inner"
              />
              <button
                onClick={handleTest}
                disabled={isTestingConnection}
                className="px-3.5 py-2 rounded-xl bg-slate-800/80 hover:bg-slate-700/80 border border-white/10 text-xs font-mono text-slate-200 flex items-center gap-1.5 transition disabled:opacity-50 shadow-sm"
              >
                {isTestingConnection ? (
                  <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                ) : (
                  <Wifi className="w-3.5 h-3.5 text-cyan-400" />
                )}
                <span>Ping</span>
              </button>
            </div>
            <p className="text-[11px] text-slate-400 mt-1.5 font-mono">
              Asegúrate de que la laptop y la Pi estén conectadas a la misma red Wi-Fi o punto de acceso.
            </p>
          </div>

          {/* Test Status feedback */}
          {testResult && (
            <div
              className={`p-3 rounded-xl border text-xs font-mono flex items-center gap-2.5 ${
                testResult.success
                  ? 'bg-emerald-950/60 border-emerald-500/30 text-emerald-300'
                  : 'bg-rose-950/60 border-rose-500/30 text-rose-300'
              }`}
            >
              {testResult.success ? (
                <Check className="w-4 h-4 text-emerald-400 shrink-0" />
              ) : (
                <AlertCircle className="w-4 h-4 text-rose-400 shrink-0" />
              )}
              <span>{testResult.message}</span>
            </div>
          )}

          {/* Confidence Threshold */}
          <div className="pt-2 border-t border-white/5">
            <div className="flex justify-between items-center text-xs font-mono mb-2">
              <span className="text-slate-300 font-medium">
                Umbral Mínimo de Certeza (Confidence)
              </span>
              <span className="text-cyan-300 font-bold px-2 py-0.5 rounded-lg bg-slate-900/60 border border-white/10">
                {Math.round(localThreshold * 100)}%
              </span>
            </div>
            <input
              type="range"
              min="0.5"
              max="0.99"
              step="0.01"
              value={localThreshold}
              onChange={(e) => setLocalThreshold(parseFloat(e.target.value))}
              className="w-full accent-cyan-400 cursor-pointer h-1.5 bg-slate-800 rounded-lg appearance-none"
            />
            <p className="text-[11px] text-slate-500 font-mono mt-1.5">
              Detecciones por debajo de este valor se considerarán dudosas para revisión manual.
            </p>
          </div>
        </div>

        {/* Action Buttons */}
        <div className="mt-6 pt-4 border-t border-white/[0.08] flex justify-end gap-2">
          <button
            onClick={onClose}
            className="px-4 py-2 text-xs font-mono rounded-xl bg-slate-800/60 hover:bg-slate-700/60 text-slate-300 transition border border-white/5"
          >
            Cancelar
          </button>
          <button
            onClick={handleSave}
            className="px-4 py-2 text-xs font-mono font-bold rounded-xl bg-gradient-to-r from-cyan-600 to-blue-600 hover:from-cyan-500 hover:to-blue-500 text-white transition shadow-lg shadow-cyan-600/20 active:scale-95"
          >
            Guardar Configuración
          </button>
        </div>
      </div>
    </div>
  )
}
