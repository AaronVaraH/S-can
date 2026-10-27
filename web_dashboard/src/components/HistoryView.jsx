import React, { useState } from 'react'
import {
  History,
  CheckCircle2,
  AlertTriangle,
  Search,
  Filter,
  Clock,
  ArrowUpRight,
  ShieldCheck,
  ShieldAlert,
  Boxes
} from 'lucide-react'

export default function HistoryView({ recentDetections = [] }) {
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

  return (
    <div className="flex-1 h-full overflow-hidden flex flex-col p-6 bg-[#070b14] select-none">
      <div className="max-w-6xl w-full mx-auto flex-1 flex flex-col space-y-4">
        {/* Header & Filter Controls */}
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 pb-2 border-b border-slate-800/80">
          <div>
            <h2 className="text-lg font-bold text-white flex items-center gap-2">
              <History className="w-5 h-5 text-cyan-400" />
              <span>Historial de Inspección</span>
            </h2>
            <p className="text-xs text-slate-400 font-mono mt-0.5">
              Registro continuo de muestras analizadas en la línea de escaneo
            </p>
          </div>

          <div className="flex items-center space-x-2 w-full sm:w-auto">
            {/* Search Input */}
            <div className="relative flex-1 sm:w-48">
              <Search className="w-3.5 h-3.5 absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" />
              <input
                type="text"
                placeholder="Buscar lata # o defecto..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full pl-8 pr-3 py-1.5 bg-slate-900 border border-slate-700/80 rounded-lg text-xs font-mono text-slate-200 placeholder:text-slate-500 focus:outline-none focus:border-cyan-500"
              />
            </div>

            {/* Filter Tabs */}
            <div className="flex bg-slate-900 p-1 rounded-lg border border-slate-800 text-xs font-mono">
              <button
                onClick={() => setFilter('all')}
                className={`px-2.5 py-1 rounded-md transition ${
                  filter === 'all' ? 'bg-slate-800 text-white font-semibold' : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                Todas
              </button>
              <button
                onClick={() => setFilter('passed')}
                className={`px-2.5 py-1 rounded-md transition ${
                  filter === 'passed' ? 'bg-emerald-950 text-emerald-400 border border-emerald-800' : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                OK
              </button>
              <button
                onClick={() => setFilter('rejected')}
                className={`px-2.5 py-1 rounded-md transition ${
                  filter === 'rejected' ? 'bg-rose-950 text-rose-400 border border-rose-800' : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                Rechazos
              </button>
            </div>
          </div>
        </div>

        {/* History Table Container */}
        <div className="flex-1 bg-[#0b1120] border border-slate-800/80 rounded-2xl overflow-hidden shadow-xl flex flex-col">
          <div className="px-5 py-3 border-b border-slate-800/80 bg-slate-900/60 grid grid-cols-12 text-xs font-mono text-slate-400 font-semibold uppercase tracking-wider">
            <span className="col-span-2">ID Muestra</span>
            <span className="col-span-2">Hora</span>
            <span className="col-span-3">Dictamen</span>
            <span className="col-span-3">Defecto / Superficie</span>
            <span className="col-span-2 text-right">Certeza AI</span>
          </div>

          <div className="flex-1 overflow-y-auto divide-y divide-slate-800/50">
            {filteredDetections.length === 0 ? (
              <div className="p-12 text-center flex flex-col items-center justify-center text-slate-500 font-mono text-xs">
                <Boxes className="w-8 h-8 mb-2 opacity-40 text-slate-400" />
                <p>No hay registros coincidentes en este filtro.</p>
              </div>
            ) : (
              filteredDetections.map((item) => {
                const isDefect =
                  item.class === 'dañada' || item.class === 'abollada' || item.class === 'defectuosa'

                return (
                  <div
                    key={item.id}
                    className="px-5 py-3.5 grid grid-cols-12 items-center text-xs font-mono hover:bg-slate-800/30 transition-colors"
                  >
                    <div className="col-span-2 flex items-center space-x-2 font-bold text-white">
                      <span>#{item.id}</span>
                    </div>

                    <div className="col-span-2 text-slate-400 flex items-center gap-1.5">
                      <Clock className="w-3.5 h-3.5 text-slate-500" />
                      <span>{item.time}</span>
                    </div>

                    <div className="col-span-3">
                      <span
                        className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[11px] font-semibold border ${
                          isDefect
                            ? 'bg-rose-950/60 text-rose-300 border-rose-800/80'
                            : 'bg-emerald-950/60 text-emerald-300 border-emerald-800/80'
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

                    <div className="col-span-3 text-slate-300">
                      {item.defectType || (isDefect ? 'Abolladura Lateral' : 'Superficie Conforme')}
                    </div>

                    <div className="col-span-2 text-right font-bold">
                      <span className={isDefect ? 'text-rose-400' : 'text-emerald-400'}>
                        {(item.confidence * 100).toFixed(1)}%
                      </span>
                      <span className="text-[10px] text-slate-500 ml-1">({item.latency || 22}ms)</span>
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
