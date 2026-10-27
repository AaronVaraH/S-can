import React, { useState } from 'react'
import {
  History,
  CheckCircle2,
  AlertTriangle,
  X,
  ExternalLink,
  Clock
} from 'lucide-react'

export default function AuditFeed({ recentDetections = [] }) {
  const [selectedItem, setSelectedItem] = useState(null)

  return (
    <div className="bg-[#0e1626] border border-brand-border/70 rounded-2xl p-4 shadow-xl shadow-black/20">
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center space-x-2">
          <History className="w-4 h-4 text-cyan-400" />
          <h3 className="text-xs font-mono font-bold uppercase tracking-wider text-slate-300">
            Tira de Auditoría Reciente
          </h3>
        </div>
        <span className="text-[10px] font-mono text-slate-500">
          Últimas {recentDetections.length} muestras
        </span>
      </div>

      {recentDetections.length === 0 ? (
        <div className="p-4 rounded-xl bg-slate-950/60 border border-dashed border-slate-800 text-center">
          <p className="text-xs text-slate-500 font-mono">
            Aún no hay registros de inspección en esta sesión.
          </p>
        </div>
      ) : (
        <div className="space-y-2 max-h-[220px] overflow-y-auto pr-1">
          {recentDetections.map((item) => {
            const isDefect =
              item.class === 'dañada' ||
              item.class === 'abollada' ||
              item.class === 'defectuosa'

            return (
              <div
                key={item.id}
                onClick={() => setSelectedItem(item)}
                className={`p-2.5 rounded-lg border flex items-center justify-between transition-all cursor-pointer hover:scale-[1.01] ${
                  isDefect
                    ? 'bg-rose-950/20 hover:bg-rose-950/30 border-rose-900/60 text-rose-200'
                    : 'bg-emerald-950/20 hover:bg-emerald-950/30 border-emerald-900/60 text-emerald-200'
                }`}
              >
                <div className="flex items-center space-x-2.5">
                  <div
                    className={`w-6 h-6 rounded-full flex items-center justify-center border text-xs font-bold ${
                      isDefect
                        ? 'bg-rose-900/40 border-rose-600 text-rose-400'
                        : 'bg-emerald-900/40 border-emerald-600 text-emerald-400'
                    }`}
                  >
                    {isDefect ? (
                      <AlertTriangle className="w-3.5 h-3.5" />
                    ) : (
                      <CheckCircle2 className="w-3.5 h-3.5" />
                    )}
                  </div>
                  <div>
                    <div className="flex items-center space-x-2">
                      <span className="text-xs font-mono font-bold text-white">
                        Lata #{item.id}
                      </span>
                      <span
                        className={`text-[10px] font-mono px-1.5 py-0.2 rounded font-semibold ${
                          isDefect
                            ? 'bg-rose-950 text-rose-400 border border-rose-800'
                            : 'bg-emerald-950 text-emerald-400 border border-emerald-800'
                        }`}
                      >
                        {isDefect ? 'RECHAZADA' : 'APROBADA'}
                      </span>
                    </div>
                    <div className="text-[10px] font-mono text-slate-400 flex items-center gap-1 mt-0.5">
                      <Clock className="w-2.5 h-2.5" />
                      <span>{item.time}</span>
                      <span className="mx-1">·</span>
                      <span>{item.defectType || (isDefect ? 'Abolladura' : 'Conforme')}</span>
                    </div>
                  </div>
                </div>

                <div className="text-right font-mono">
                  <div className="text-xs font-bold text-slate-200">
                    {(item.confidence * 100).toFixed(1)}%
                  </div>
                  <div className="text-[10px] text-slate-500">
                    {item.latency || '24'}ms
                  </div>
                </div>
              </div>
            )
          })}
        </div>
      )}

      {/* Item Detail Inspector Modal */}
      {selectedItem && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm">
          <div className="bg-[#0f172a] border border-slate-700 rounded-2xl max-w-md w-full p-5 shadow-2xl relative">
            <button
              onClick={() => setSelectedItem(null)}
              className="absolute top-4 right-4 p-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-400 transition"
            >
              <X className="w-4 h-4" />
            </button>

            <h4 className="text-sm font-mono font-bold text-white flex items-center gap-2">
              <span>Auditoría: Lata #{selectedItem.id}</span>
            </h4>
            <p className="text-xs text-slate-400 font-mono mt-0.5">
              Registrado a las {selectedItem.time}
            </p>

            <div className="mt-4 p-4 rounded-xl bg-slate-950 border border-slate-800 space-y-2.5 font-mono text-xs">
              <div className="flex justify-between">
                <span className="text-slate-400">Dictamen Final:</span>
                <strong className={selectedItem.class === 'intacta' ? 'text-emerald-400' : 'text-rose-400'}>
                  {selectedItem.class.toUpperCase()}
                </strong>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-400">Confianza del Modelo:</span>
                <strong className="text-white">{(selectedItem.confidence * 100).toFixed(2)}%</strong>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-400">Tipo de Anomalía:</span>
                <strong className="text-slate-200">{selectedItem.defectType || 'Ninguna'}</strong>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-400">Latencia de Inferencia:</span>
                <strong className="text-cyan-400">{selectedItem.latency || '24.2'} ms</strong>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-400">Coordenadas Bounding Box:</span>
                <strong className="text-slate-300">
                  {selectedItem.bbox ? `[${selectedItem.bbox.map(n => n.toFixed(2)).join(', ')}]` : '[0.33, 0.22, 0.34, 0.56]'}
                </strong>
              </div>
            </div>

            <div className="mt-4 flex justify-end">
              <button
                onClick={() => setSelectedItem(null)}
                className="px-4 py-1.5 text-xs font-mono rounded-lg bg-slate-800 hover:bg-slate-700 text-white transition"
              >
                Cerrar Inspector
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
