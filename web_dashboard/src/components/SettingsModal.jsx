import React, { useState } from 'react'
import {
  X,
  Server,
  Sliders,
  Check,
  AlertCircle,
  Wifi,
  RefreshCw
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
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm animate-fade-in">
      <div className="bg-[#0f172a] border border-slate-700 rounded-2xl max-w-md w-full p-6 shadow-2xl relative text-slate-100 font-sans">
        {/* Close Button */}
        <button
          onClick={onClose}
          className="absolute top-4 right-4 p-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-400 transition"
        >
          <X className="w-4 h-4" />
        </button>

        {/* Modal Title */}
        <div className="flex items-center space-x-2 mb-4">
          <div className="p-2 rounded-lg bg-cyan-950 text-cyan-400 border border-cyan-800">
            <Sliders className="w-5 h-5" />
          </div>
          <div>
            <h3 className="text-base font-bold text-white">
              Configuración de Conexión
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
            <label className="block text-xs font-mono text-slate-300 mb-1.5 font-semibold">
              Dirección IP del Servidor Raspberry Pi
            </label>
            <div className="flex gap-2">
              <input
                type="text"
                value={localUrl}
                onChange={(e) => setLocalUrl(e.target.value)}
                placeholder="http://192.168.1.42:8000"
                className="flex-1 bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-xs font-mono text-cyan-300 focus:outline-none focus:border-cyan-500"
              />
              <button
                onClick={handleTest}
                disabled={isTestingConnection}
                className="px-3 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 border border-slate-700 text-xs font-mono text-slate-200 flex items-center gap-1.5 transition disabled:opacity-50"
              >
                {isTestingConnection ? (
                  <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                ) : (
                  <Wifi className="w-3.5 h-3.5 text-cyan-400" />
                )}
                <span>Ping</span>
              </button>
            </div>
            <p className="text-[11px] text-slate-400 mt-1 font-mono">
              Ambos dispositivos (Laptop y Pi) deben estar conectados a la misma red Wi-Fi o punto de acceso.
            </p>
          </div>

          {/* Test Status feedback */}
          {testResult && (
            <div
              className={`p-3 rounded-lg border text-xs font-mono flex items-center gap-2 ${
                testResult.success
                  ? 'bg-emerald-950/60 border-emerald-800 text-emerald-300'
                  : 'bg-rose-950/60 border-rose-800 text-rose-300'
              }`}
            >
              {testResult.success ? (
                <Check className="w-4 h-4 text-emerald-400" />
              ) : (
                <AlertCircle className="w-4 h-4 text-rose-400" />
              )}
              <span>{testResult.message}</span>
            </div>
          )}

          {/* Confidence Threshold */}
          <div>
            <div className="flex justify-between items-center text-xs font-mono mb-1.5">
              <span className="text-slate-300 font-semibold">
                Umbral Mínimo de Confianza
              </span>
              <span className="text-cyan-400 font-bold">
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
              className="w-full accent-cyan-400 bg-slate-800 cursor-pointer"
            />
            <p className="text-[11px] text-slate-500 font-mono mt-1">
              Las detecciones por debajo de este porcentaje se marcarán para revisión manual.
            </p>
          </div>

          {/* Endpoints Summary */}
          <div className="p-3 rounded-lg bg-slate-950 border border-slate-800 text-[11px] font-mono text-slate-400 space-y-1">
            <div className="text-slate-300 font-bold mb-1">Rutas API Esperadas:</div>
            <div>• Video Stream: <span className="text-cyan-400">{localUrl}/video_feed</span></div>
            <div>• WebSockets: <span className="text-cyan-400">{localUrl.replace(/^http/, 'ws')}/ws/telemetry</span></div>
            <div>• Health Check: <span className="text-cyan-400">{localUrl}/health</span></div>
          </div>
        </div>

        {/* Action Buttons */}
        <div className="mt-6 flex justify-end gap-2">
          <button
            onClick={onClose}
            className="px-4 py-2 text-xs font-mono rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 transition"
          >
            Cancelar
          </button>
          <button
            onClick={handleSave}
            className="px-4 py-2 text-xs font-mono font-bold rounded-lg bg-cyan-600 hover:bg-cyan-500 text-white transition shadow-lg shadow-cyan-600/30"
          >
            Guardar Configuración
          </button>
        </div>
      </div>
    </div>
  )
}
