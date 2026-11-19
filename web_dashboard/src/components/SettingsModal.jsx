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
import { normalizeBackendUrl } from '../utils/url'

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
    const formatted = normalizeBackendUrl(localUrl)
    setLocalUrl(formatted)
    const result = await onTestConnection(formatted)
    setTestResult(result)
  }

  const handleSave = () => {
    const formatted = normalizeBackendUrl(localUrl)
    onSaveBackendUrl(formatted)
    onSaveThreshold(localThreshold)
    onClose()
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-md transition-all">
      <div className="glass-dock max-w-md w-full p-6 rounded-3xl shadow-2xl relative text-skin-primary font-sans">
        {/* Close Button */}
        <button
          onClick={onClose}
          aria-label="Cerrar ventana"
          className="absolute top-5 right-5 p-1.5 rounded-xl bg-white/80 dark:bg-brand-800/80 hover:bg-brand-ice dark:hover:bg-brand-umber/70 border border-brand-silver/60 dark:border-white/10 text-skin-secondary hover:text-skin-primary transition shadow-sm"
        >
          <X className="w-4 h-4" />
        </button>

        {/* Modal Title */}
        <div className="flex items-center space-x-3 mb-5">
            <div className="p-2.5 rounded-xl bg-brand-umber text-brand-ice border border-brand-sand/35">
              <Sliders className="w-5 h-5 text-brand-sand" />
            </div>
            <div>
              <h3 className="text-sm font-bold text-skin-primary font-mono">
                Configuración del Sistema
              </h3>
              <p className="text-xs text-skin-secondary font-mono">
                Parámetros de enlace con la Raspberry Pi
              </p>
            </div>
          </div>

          {/* Settings Body */}
          <div className="space-y-4">
            {/* Backend IP URL */}
            <div>
              <label className="block text-xs font-mono text-skin-primary mb-1.5 font-semibold">
                Dirección IP del Servidor FastAPI
              </label>
              <div className="flex gap-2">
                <input
                  type="text"
                  value={localUrl}
                  onChange={(e) => setLocalUrl(e.target.value)}
                  placeholder="http://192.168.1.42:8000"
                  style={{ backgroundColor: 'var(--bg-input)', borderColor: 'var(--border-subtle)' }}
                  className="flex-1 border rounded-xl px-3 py-2 text-xs font-mono text-brand-umber dark:text-brand-ice placeholder:text-skin-muted focus:outline-none focus:border-brand-brass dark:focus:border-brand-sand shadow-inner"
                />
                <button
                  onClick={handleTest}
                  disabled={isTestingConnection}
                  className="px-3.5 py-2 rounded-xl bg-white/80 dark:bg-brand-800/80 hover:bg-brand-ice dark:hover:bg-brand-umber/70 border border-brand-silver/60 dark:border-brand-sand/25 text-xs font-mono text-skin-primary flex items-center gap-1.5 transition disabled:opacity-50 shadow-sm"
                >
                  {isTestingConnection ? (
                    <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                  ) : (
                    <Wifi className="w-3.5 h-3.5 text-brand-brass dark:text-brand-sand" />
                  )}
                  <span>Ping</span>
                </button>
              </div>
              <p className="text-[11px] text-skin-secondary mt-1.5 font-mono">
                Asegúrate de que la laptop y la Pi estén conectadas a la misma red Wi-Fi o punto de acceso.
              </p>
            </div>

            {/* Test Status feedback */}
            {testResult && (
              <div
                className={`p-3 rounded-xl border text-xs font-mono flex items-center gap-2.5 ${testResult.success
                    ? 'bg-emerald-500/15 dark:bg-emerald-950/60 border-emerald-600/35 dark:border-emerald-500/30 text-emerald-800 dark:text-emerald-300'
                    : 'bg-rose-500/15 dark:bg-rose-950/60 border-rose-600/35 dark:border-rose-500/30 text-rose-800 dark:text-rose-300'
                  }`}
              >
                {testResult.success ? (
                  <Check className="w-4 h-4 text-emerald-600 dark:text-emerald-400 shrink-0" />
                ) : (
                  <AlertCircle className="w-4 h-4 text-rose-600 dark:text-rose-400 shrink-0" />
                )}
                <span>{testResult.message}</span>
              </div>
            )}

            {/* Confidence Threshold */}
            <div
              style={{ borderColor: 'var(--border-subtle)' }}
              className="pt-3 border-t"
            >
              <div className="flex justify-between items-center text-xs font-mono mb-2">
                <span className="text-skin-primary font-semibold">
                  Umbral Mínimo de Certeza (Confidence)
                </span>
                <span className="text-brand-umber dark:text-brand-sand font-bold px-2 py-0.5 rounded-lg bg-brand-ice/70 dark:bg-brand-900 border border-brand-silver/50 dark:border-brand-sand/25">
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
                className="w-full accent-brand-umber dark:accent-brand-sand cursor-pointer h-1.5 bg-brand-silver/50 dark:bg-brand-800 rounded-lg appearance-none"
              />
              <p className="text-[11px] text-skin-muted font-mono mt-1.5">
                Detecciones por debajo de este valor se considerarán dudosas para revisión manual.
              </p>
            </div>
          </div>

          {/* Action Buttons */}
          <div
            style={{ borderColor: 'var(--border-subtle)' }}
            className="mt-6 pt-4 border-t flex justify-end gap-2"
          >
            <button
              onClick={onClose}
              className="px-4 py-2 text-xs font-mono rounded-xl bg-white/70 dark:bg-brand-800/70 hover:bg-brand-ice dark:hover:bg-brand-umber/60 text-skin-primary transition border border-brand-silver/50 dark:border-brand-sand/20"
            >
              Cancelar
            </button>
            <button
              onClick={handleSave}
              className="btn-brand px-4 py-2 text-xs font-mono font-bold rounded-xl shadow-md active:scale-95"
            >
              Guardar Configuración
            </button>
          </div>
        </div>
      </div>
      )
}
