import React, { useState } from 'react'
import {
  History,
  Search,
  Clock,
  ShieldCheck,
  ShieldAlert,
  Boxes,
  Download,
  Trash2
} from 'lucide-react'

export default function HistoryView({ recentDetections = [], onResetMetrics }) {
  const [filter, setFilter] = useState('all') // 'all' | 'passed' | 'rejected'
  const [searchTerm, setSearchTerm] = useState('')

  const filteredDetections = recentDetections.filter((item) => {
    const isDefect =
      item.class === 'dañada' || item.class === 'abollada' || item.class === 'defectuosa'

    if (filter === 'passed' && isDefect) return false
    if (filter === 'rejected' && !isDefect) return false

    if (searchTerm) {
      const term = searchTerm.toLowerCase()
      const matchId = String(item.id).includes(term)
      const matchClass = item.class?.toLowerCase().includes(term)
      const matchDefect = item.defectType?.toLowerCase().includes(term)
      return matchId || matchClass || matchDefect
    }

    return true
  })

  // Export to CSV
  const handleExportCSV = () => {
    if (recentDetections.length === 0) return
    const headers = 'ID,Hora,Clase,Dictamen,Defecto,Confianza,Latencia_ms\n'
    const rows = recentDetections
      .map(
        (d) =>
          `${d.id},"${d.time}","${d.class}","${
            d.class === 'intacta' ? 'CONFORME' : 'RECHAZADA'
          }","${d.defectType || ''}",${(d.confidence * 100).toFixed(1)}%,${
            d.latency || 22
          }`
      )
      .join('\n')

    const blob = new Blob([headers + rows], { type: 'text/csv;charset=utf-8;' })
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.setAttribute('download', `s-can_inspeccion_${Date.now()}.csv`)
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
  }

  return (
    <div className="flex-1 h-full overflow-hidden flex flex-col select-none">
      <div className="w-full flex-1 flex flex-col space-y-3 min-h-0">
        {/* Header & Filter Controls Glass Bar */}
        <div className="glass-panel p-4 rounded-2xl flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 shrink-0">
          <div>
            <h2 className="text-sm font-bold text-white flex items-center gap-2 font-mono">
              <History className="w-4 h-4 text-cyan-400" />
              <span>Registro de Control de Calidad</span>
            </h2>
            <p className="text-xs text-slate-400 font-mono mt-0.5">
              Trazabilidad en tiempo real de muestras analizadas en la estación óptica
            </p>
          </div>

          <div className="flex flex-wrap items-center gap-2 w-full sm:w-auto">
            {/* Search Input */}
            <div className="relative flex-1 sm:w-56">
              <Search className="w-3.5 h-3.5 absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" />
              <input
                type="text"
                placeholder="Buscar por # o defecto..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full pl-8 pr-3 py-1.5 bg-slate-900/60 border border-white/10 rounded-xl text-xs font-mono text-slate-200 placeholder:text-slate-500 focus:outline-none focus:border-cyan-500/60 shadow-inner"
              />
            </div>

            {/* Filter Pill Tabs */}
            <div className="flex bg-slate-900/60 p-1 rounded-xl border border-white/10 text-xs font-mono">
              <button
                onClick={() => setFilter('all')}
                className={`px-3 py-1 rounded-lg transition-all ${
                  filter === 'all'
                    ? 'bg-slate-700/70 text-white font-medium shadow-sm'
                    : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                Todas ({recentDetections.length})
              </button>
              <button
                onClick={() => setFilter('passed')}
                className={`px-3 py-1 rounded-lg transition-all ${
                  filter === 'passed'
                    ? 'bg-emerald-950/80 text-emerald-300 font-medium border border-emerald-500/30'
                    : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                OK
              </button>
              <button
                onClick={() => setFilter('rejected')}
                className={`px-3 py-1 rounded-lg transition-all ${
                  filter === 'rejected'
                    ? 'bg-rose-950/80 text-rose-300 font-medium border border-rose-500/30'
                    : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                Rechazos
              </button>
            </div>

            {/* Export CSV button */}
            <button
              onClick={handleExportCSV}
              disabled={recentDetections.length === 0}
              title="Descargar reporte CSV"
              className="p-2 rounded-xl bg-slate-800/60 hover:bg-slate-700/60 border border-white/10 text-slate-300 hover:text-white transition disabled:opacity-30 disabled:cursor-not-allowed"
            >
              <Download className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>

        {/* History Table Container */}
        <div className="flex-1 glass-panel rounded-2xl overflow-hidden flex flex-col min-h-0 border border-white/10">
          {/* Table Header */}
          <div className="px-5 py-3 border-b border-white/[0.08] bg-slate-900/60 grid grid-cols-12 text-xs font-mono text-slate-400 font-semibold uppercase tracking-wider shrink-0">
            <span className="col-span-2">ID Muestra</span>
            <span className="col-span-2">Hora Captura</span>
            <span className="col-span-3">Dictamen Calidad</span>
            <span className="col-span-3">Clasificación / Defecto</span>
            <span className="col-span-2 text-right">Certeza AI</span>
          </div>

          {/* Table Rows */}
          <div className="flex-1 overflow-y-auto divide-y divide-white/[0.04]">
            {filteredDetections.length === 0 ? (
              <div className="p-16 text-center flex flex-col items-center justify-center text-slate-500 font-mono text-xs h-full">
                <Boxes className="w-10 h-10 mb-3 opacity-30 text-slate-400" />
                <p className="font-semibold text-slate-400">
                  {recentDetections.length === 0
                    ? 'No hay registros de inspección en esta sesión.'
                    : 'No hay muestras que coincidan con el filtro seleccionado.'}
                </p>
                <p className="text-slate-500 text-[11px] mt-1 max-w-sm">
                  {recentDetections.length === 0
                    ? 'Las muestras aparecerán aquí automáticamente conforme la cámara detecte latas.'
                    : 'Intenta limpiar el término de búsqueda o cambiar el filtro.'}
                </p>
              </div>
            ) : (
              filteredDetections.map((item) => {
                const isDefect =
                  item.class === 'dañada' ||
                  item.class === 'abollada' ||
                  item.class === 'defectuosa'

                return (
                  <div
                    key={item.id}
                    className="px-5 py-3.5 grid grid-cols-12 items-center text-xs font-mono hover:bg-slate-800/30 transition-colors"
                  >
                    <div className="col-span-2 flex items-center space-x-2 font-bold text-white">
                      <span className="text-cyan-300">#{item.id}</span>
                    </div>

                    <div className="col-span-2 text-slate-400 flex items-center gap-1.5">
                      <Clock className="w-3.5 h-3.5 text-slate-500" />
                      <span>{item.time}</span>
                    </div>

                    <div className="col-span-3">
                      <span
                        className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[11px] font-semibold border ${
                          isDefect
                            ? 'bg-rose-950/60 text-rose-300 border-rose-500/40'
                            : 'bg-emerald-950/60 text-emerald-300 border-emerald-500/40'
                        }`}
                      >
                        {isDefect ? (
                          <ShieldAlert className="w-3 h-3 text-rose-400" />
                        ) : (
                          <ShieldCheck className="w-3 h-3 text-emerald-400" />
                        )}
                        <span>{isDefect ? 'RECHAZADA' : 'CONFORME'}</span>
                      </span>
                    </div>

                    <div className="col-span-3 text-slate-300 truncate pr-2">
                      {item.defectType || (isDefect ? 'Abolladura' : 'Superficie Conforme')}
                    </div>

                    <div className="col-span-2 text-right font-bold">
                      <span className={isDefect ? 'text-rose-400' : 'text-emerald-400'}>
                        {(item.confidence * 100).toFixed(1)}%
                      </span>
                      {item.latency && (
                        <span className="text-[10px] text-slate-500 ml-1.5">
                          ({item.latency}ms)
                        </span>
                      )}
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
