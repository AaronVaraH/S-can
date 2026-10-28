import React from 'react'
import {
  ShieldCheck,
  Cpu,
  Thermometer,
  HardDrive,
  Server,
  Zap,
  CheckCircle2,
  XCircle,
  Wifi,
  Activity,
  Layers,
  Terminal
} from 'lucide-react'

export default function AuditView({
  piTelemetry = {},
  metrics = {},
  connectionStatus = 'disconnected',
  backendUrl = 'http://localhost:8000',
  pingMs
}) {
  const isConnected = connectionStatus === 'connected'
  const isHot = piTelemetry.cpuTemp > 70

  const endpoints = [
    {
      name: 'Stream MJPEG',
      path: `${backendUrl}/video_feed`,
      protocol: 'HTTP / MJPEG',
      status: isConnected ? 'Activo' : 'Inactivo',
      desc: 'Transmisión de fotogramas ópticos a 60 FPS'
    },
    {
      name: 'Canal Telemetría',
      path: `${backendUrl.replace(/^http/, 'ws')}/ws/telemetry`,
      protocol: 'WebSocket',
      status: isConnected ? 'Conectado' : 'Desconectado',
      desc: 'Transmisión bidireccional de inferencia y estado de hardware'
    },
    {
      name: 'Health Check / Ping',
      path: `${backendUrl}/health`,
      protocol: 'REST GET',
      status: pingMs !== null ? `${pingMs}ms` : 'Sin respuesta',
      desc: 'Sondeo de latencia y disponibilidad del servidor'
    },
    {
      name: 'Inferencia Directa',
      path: `${backendUrl}/predict`,
      protocol: 'REST POST',
      status: isConnected ? 'Listo' : 'Standby',
      desc: 'Entrada multipart para fotogramas aislados'
    }
  ]

  return (
    <div className="flex-1 h-full overflow-hidden flex flex-col select-none">
      <div className="w-full flex-1 flex flex-col space-y-4 overflow-y-auto pr-1">
        {/* Header */}
        <div className="glass-panel p-4 rounded-2xl flex items-center justify-between">
          <div>
            <h2 className="text-sm font-bold text-white flex items-center gap-2 font-mono">
              <ShieldCheck className="w-4 h-4 text-cyan-400" />
              <span>Telemetría de Hardware y Diagnóstico de Red</span>
            </h2>
            <p className="text-xs text-slate-400 font-mono mt-0.5">
              Supervisión en tiempo real de la Raspberry Pi y canales de comunicación
            </p>
          </div>

          <div className="flex items-center space-x-2 text-xs font-mono">
            <span
              className={`w-2 h-2 rounded-full ${
                isConnected ? 'bg-emerald-400' : 'bg-rose-400'
              }`}
            />
            <span className="text-slate-300 font-medium">
              {isConnected ? 'Hardware Sincronizado' : 'Sin Enlace con la Pi'}
            </span>
          </div>
        </div>

        {/* 4 Telemetry Metrics Cards */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
          {/* CPU Card */}
          <div className="glass-card p-4 rounded-2xl flex flex-col justify-between">
            <div className="flex items-center justify-between text-slate-400 mb-2">
              <span className="text-xs font-mono font-medium">Carga CPU ARM</span>
              <Cpu className="w-4 h-4 text-cyan-400" />
            </div>
            <div className="text-2xl font-bold font-mono text-white tracking-tight">
              {isConnected && piTelemetry.cpuUsage > 0 ? `${piTelemetry.cpuUsage}%` : '--'}
            </div>
            <div className="w-full bg-slate-900/80 h-1.5 rounded-full overflow-hidden mt-3 border border-white/5">
              <div
                className="bg-cyan-500 h-full rounded-full transition-all"
                style={{
                  width: `${isConnected ? piTelemetry.cpuUsage || 0 : 0}%`
                }}
              />
            </div>
            <span className="text-[10px] font-mono text-slate-500 mt-2 block">
              Broadcom BCM2711 · 4 Cores
            </span>
          </div>

          {/* Temperature */}
          <div className="glass-card p-4 rounded-2xl flex flex-col justify-between">
            <div className="flex items-center justify-between text-slate-400 mb-2">
              <span className="text-xs font-mono font-medium">Temperatura SoC</span>
              <Thermometer
                className={`w-4 h-4 ${isHot ? 'text-rose-400' : 'text-emerald-400'}`}
              />
            </div>
            <div className="text-2xl font-bold font-mono text-white tracking-tight">
              {isConnected && piTelemetry.cpuTemp > 0 ? `${piTelemetry.cpuTemp}°C` : '--'}
            </div>
            <div className="w-full bg-slate-900/80 h-1.5 rounded-full overflow-hidden mt-3 border border-white/5">
              <div
                className={`h-full rounded-full transition-all ${
                  isHot ? 'bg-rose-500' : 'bg-emerald-500'
                }`}
                style={{
                  width: `${
                    isConnected
                      ? Math.min(100, (piTelemetry.cpuTemp || 0) * 1.2)
                      : 0
                  }%`
                }}
              />
            </div>
            <span className="text-[10px] font-mono text-slate-500 mt-2 block">
              {isConnected
                ? isHot
                  ? 'Alerta: disipación térmica requerida'
                  : 'Temperatura de operación conforme'
                : 'Esperando conexión con sensor térmico'}
            </span>
          </div>

          {/* RAM Memory */}
          <div className="glass-card p-4 rounded-2xl flex flex-col justify-between">
            <div className="flex items-center justify-between text-slate-400 mb-2">
              <span className="text-xs font-mono font-medium">Memoria RAM</span>
              <HardDrive className="w-4 h-4 text-purple-400" />
            </div>
            <div className="text-2xl font-bold font-mono text-white tracking-tight">
              {isConnected ? piTelemetry.ramUsage || '--' : '--'}
            </div>
            <div className="w-full bg-slate-900/80 h-1.5 rounded-full overflow-hidden mt-3 border border-white/5">
              <div
                className="bg-purple-500 h-full rounded-full"
                style={{ width: isConnected ? '32%' : '0%' }}
              />
            </div>
            <span className="text-[10px] font-mono text-slate-500 mt-2 block">
              LPDDR4 SDRAM Compartida
            </span>
          </div>

          {/* Inference Model Engine */}
          <div className="glass-card p-4 rounded-2xl flex flex-col justify-between">
            <div className="flex items-center justify-between text-slate-400 mb-2">
              <span className="text-xs font-mono font-medium">Latencia Inferencia</span>
              <Zap className="w-4 h-4 text-amber-400" />
            </div>
            <div className="text-2xl font-bold font-mono text-white tracking-tight">
              {isConnected && piTelemetry.modelLatencyMs > 0
                ? `${piTelemetry.modelLatencyMs} ms`
                : '--'}
            </div>
            <div className="w-full bg-slate-900/80 h-1.5 rounded-full overflow-hidden mt-3 border border-white/5">
              <div
                className="bg-amber-400 h-full rounded-full"
                style={{
                  width: isConnected
                    ? `${Math.min(100, (piTelemetry.modelLatencyMs || 20) * 2)}%`
                    : '0%'
                }}
              />
            </div>
            <span className="text-[10px] font-mono text-slate-500 mt-2 block truncate">
              {piTelemetry.modelEngine || 'ONNX Runtime ARM64'}
            </span>
          </div>
        </div>

        {/* API Endpoints & Transport Status Table */}
        <div className="glass-panel p-4 rounded-2xl flex flex-col space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-xs font-mono font-semibold uppercase tracking-wider text-slate-400">
              Rutas y Canales de Comunicación
            </span>
            <span className="text-[11px] font-mono text-slate-500">
              Host actual: {backendUrl}
            </span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-2.5">
            {endpoints.map((ep) => (
              <div
                key={ep.name}
                className="p-3 rounded-xl glass-card flex flex-col justify-between space-y-2"
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-2">
                    <span className="font-semibold text-xs text-slate-200 font-mono">
                      {ep.name}
                    </span>
                    <span className="text-[10px] px-1.5 py-0.5 rounded bg-slate-800 text-slate-400 font-mono border border-white/5">
                      {ep.protocol}
                    </span>
                  </div>

                  <span
                    className={`text-[11px] font-mono font-semibold ${
                      isConnected
                        ? 'text-emerald-400'
                        : 'text-slate-500'
                    }`}
                  >
                    {ep.status}
                  </span>
                </div>

                <div className="text-[11px] font-mono text-cyan-300 bg-slate-950/60 px-2 py-1 rounded-lg border border-white/5 truncate">
                  {ep.path}
                </div>

                <p className="text-[10px] text-slate-400 font-mono">
                  {ep.desc}
                </p>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}
