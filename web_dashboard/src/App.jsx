import React, { useState } from 'react'

export default function App() {
  const [backendUrl, setBackendUrl] = useState('http://localhost:8000')
  const [isConnected, setIsConnected] = useState(false)
  const [lastPrediction, setLastPrediction] = useState(null)

  const checkConnection = async () => {
    try {
      const res = await fetch(`${backendUrl}/health`)
      if (res.ok) {
        setIsConnected(true)
      } else {
        setIsConnected(false)
      }
    } catch {
      setIsConnected(false)
    }
  }

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col">
      {/* Navbar */}
      <header className="border-b border-slate-800 bg-slate-900/60 backdrop-blur px-6 py-4 flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <div className="w-8 h-8 rounded-lg bg-emerald-500/20 text-emerald-400 font-bold flex items-center justify-center border border-emerald-500/30">
            S
          </div>
          <h1 className="text-xl font-bold tracking-tight text-white">S-can Dashboard</h1>
        </div>
        <div className="flex items-center space-x-4">
          <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${isConnected ? 'bg-emerald-950 text-emerald-400 border border-emerald-800' : 'bg-rose-950 text-rose-400 border border-rose-800'}`}>
            <span className={`w-1.5 h-1.5 mr-1.5 rounded-full ${isConnected ? 'bg-emerald-400' : 'bg-rose-400'}`} />
            {isConnected ? 'Pi Backend Conectado' : 'Desconectado'}
          </span>
          <button
            onClick={checkConnection}
            className="px-3 py-1.5 text-xs font-semibold rounded-md bg-slate-800 hover:bg-slate-700 transition border border-slate-700 text-slate-200"
          >
            Verificar Estado
          </button>
        </div>
      </header>

      {/* Main Content */}
      <main className="flex-1 p-6 grid grid-cols-1 lg:grid-cols-3 gap-6 max-w-7xl mx-auto w-full">
        {/* Stream / Camera View */}
        <section className="lg:col-span-2 bg-slate-900/40 border border-slate-800 rounded-xl p-5 flex flex-col">
          <h2 className="text-sm font-semibold uppercase tracking-wider text-slate-400 mb-3">
            Transmisión en Vivo (Pi Camera)
          </h2>
          <div className="flex-1 bg-slate-950 rounded-lg border border-dashed border-slate-800 flex flex-col items-center justify-center min-h-[350px] p-6 text-center">
            <div className="w-16 h-16 rounded-full bg-slate-900 flex items-center justify-center text-slate-500 mb-3 border border-slate-800">
              📷
            </div>
            <p className="text-slate-300 font-medium">Feed de Cámara en Espera</p>
            <p className="text-xs text-slate-500 max-w-sm mt-1">
              Conecte el backend en Raspberry Pi para comenzar a visualizar los fotogramas y la inferencia en tiempo real.
            </p>
          </div>
        </section>

        {/* Inference Results / Controls */}
        <section className="space-y-6">
          <div className="bg-slate-900/40 border border-slate-800 rounded-xl p-5">
            <h2 className="text-sm font-semibold uppercase tracking-wider text-slate-400 mb-3">
              Resultado de Inferencia
            </h2>
            <div className="p-4 rounded-lg bg-slate-950 border border-slate-800">
              <span className="text-xs text-slate-500">Clase Detectada</span>
              <p className="text-2xl font-bold text-emerald-400 mt-1">
                {lastPrediction ? lastPrediction.class : 'Sin lectura'}
              </p>
              <div className="mt-3">
                <div className="flex justify-between text-xs text-slate-400 mb-1">
                  <span>Confianza</span>
                  <span>{lastPrediction ? `${(lastPrediction.confidence * 100).toFixed(1)}%` : '0%'}</span>
                </div>
                <div className="w-full bg-slate-800 h-2 rounded-full overflow-hidden">
                  <div
                    className="bg-emerald-500 h-full rounded-full transition-all"
                    style={{ width: `${lastPrediction ? lastPrediction.confidence * 100 : 0}%` }}
                  />
                </div>
              </div>
            </div>
          </div>

          <div className="bg-slate-900/40 border border-slate-800 rounded-xl p-5">
            <h2 className="text-sm font-semibold uppercase tracking-wider text-slate-400 mb-3">
              Configuración de Conexión
            </h2>
            <div className="space-y-3">
              <label className="block text-xs text-slate-400">Dirección del Backend Pi</label>
              <input
                type="text"
                value={backendUrl}
                onChange={(e) => setBackendUrl(e.target.value)}
                placeholder="http://192.168.1.X:8000"
                className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-sm text-slate-200 focus:outline-none focus:border-emerald-500"
              />
              <p className="text-xs text-slate-500">
                Asegúrate de que la laptop y la Raspberry Pi estén en la misma red local o conectadas por IP estática.
              </p>
            </div>
          </div>
        </section>
      </main>
    </div>
  )
}
