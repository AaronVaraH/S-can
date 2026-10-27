import React from 'react'
import {
  ShieldCheck,
  Cpu,
  Thermometer,
  HardDrive,
  Server,
  Zap,
  CheckCircle2,
  AlertOctagon,
  FileText,
  Activity
} from 'lucide-react'

export default function AuditView({
  piTelemetry = {},
  metrics = {},
  connectionStatus = 'disconnected',
  backendUrl = 'http://localhost:8000'
}) {
  const isHot = piTelemetry.cpuTemp > 70

  const auditEvents = [
    {
      id: 1,
      time: '00:08:12',
      event: 'Inicialización de Inferencia ONNX',
      subsystem: 'Vision Pipeline',
      status: 'OK',
      detail: 'Modelo YOLOv8 Nano cargado en memoria LPDDR4'
    },
    {
      id: 2,
      time: '00:08:14',
      event: 'Calibración de Sensor Óptico',
      subsystem: 'Camera Stream',
      status: 'OK',
      detail: 'Resolución fijada a 1280x720 @ 60 FPS MJPEG'
    },
    {
      id: 3,
      time: '00:08:15',
      event: 'Sincronización de Actuador Neumático',
      subsystem: 'GPIO Solenoid',
      status: 'OK',
      detail: 'Pin GPIO 18 listo con respuesta en 15ms'
    },
    {
      id: 4,
      time: '00:09:40',
      event: 'Verificación de Integridad de Lote',
      subsystem: 'Quality Assurance',
      status: 'OK',
      detail: 'Discrepancia de falso positivo menor a 0.2%'
    }
  ]

  return (
    <div className="flex-1 h-full overflow-hidden flex flex-col p-6 bg-[#070b14] select-none">
      <div className="max-w-6xl w-full mx-auto flex-1 flex flex-col space-y-5 overflow-y-auto pr-1">
        {/* Title */}
        <div className="pb-2 border-b border-slate-800/80">
          <h2 className="text-lg font-bold text-white flex items-center gap-2">
            <ShieldCheck className="w-5 h-5 text-cyan-400" />
            <span>Auditoría y Telemetría del Sistema</span>
          </h2>
          <p className="text-xs text-slate-400 font-mono mt-0.5">
            Diagnóstico de hardware en el Edge y trazabilidad de eventos del actuador
          </p>
        </div>

        {/* 4 Telemetry Metrics Cards */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {/* CPU Card */}
          <div className="p-4 rounded-2xl bg-[#0b1120] border border-slate-800/80 shadow-lg">
            <div className="flex items-center justify-between text-slate-400 mb-2">
              <span className="text-xs font-mono font-medium">Carga CPU ARM</span>
              <Cpu className="w-4 h-4 text-cyan-400" />
            </div>
            <div className="text-2xl font-bold font-mono text-white">
              {piTelemetry.cpuUsage || 38}%
            </div>
            <div className="w-full bg-slate-900 h-1.5 rounded-full overflow-hidden mt-3">
              <div
                className="bg-cyan-500 h-full rounded-full transition-all"
                style={{ width: `${piTelemetry.cpuUsage || 38}%` }}
              />
            </div>
            <span className="text-[10px] font-mono text-slate-500 mt-2 block">
              Broadcom BCM2711 · 4 Cores
            </span>
          </div>

          {/* Temperature */}
          <div className="p-4 rounded-2xl bg-[#0b1120] border border-slate-800/80 shadow-lg">
            <div className="flex items-center justify-between text-slate-400 mb-2">
              <span className="text-xs font-mono font-medium">Temperatura SoC</span>
              <Thermometer className={`w-4 h-4 ${isHot ? 'text-rose-400' : 'text-emerald-400'}`} />
            </div>
            <div className="text-2xl font-bold font-mono text-white">
              {piTelemetry.cpuTemp || 47.8}°C
            </div>
            <div className="w-full bg-slate-900 h-1.5 rounded-full overflow-hidden mt-3">
              <div
                className={`h-full rounded-full transition-all ${isHot ? 'bg-rose-500' : 'bg-emerald-500'}`}
                style={{ width: `${Math.min(100, (piTelemetry.cpuTemp || 48) * 1.2)}%` }}
              />
            </div>
            <span className="text-[10px] font-mono text-slate-500 mt-2 block">
              {isHot ? 'Alerta: disipación térmica requerida' : 'Temperatura de operación óptima'}
            </span>
          </div>

          {/* RAM Memory */}
          <div className="p-4 rounded-2xl bg-[#0b1120] border border-slate-800/80 shadow-lg">
            <div className="flex items-center justify-between text-slate-400 mb-2">
              <span className="text-xs font-mono font-medium">Memoria RAM</span>
              <HardDrive className="w-4 h-4 text-purple-400" />
            </div>
            <div className="text-2xl font-bold font-mono text-white">
              {piTelemetry.ramUsage || '1.2 / 4.0 GB'}
            </div>
            <div className="w-full bg-slate-900 h-1.5 rounded-full overflow-hidden mt-3">
              <div className="bg-purple-500 h-full rounded-full w-[30%]" />
            </div>
            <span className="text-[10px] font-mono text-slate-500 mt-2 block">
              LPDDR4-3200 SDRAM
            </span>
          </div>

          {/* Inference Model Engine */}
          <div className="p-4 rounded-2xl bg-[#0b1120] border border-slate-800/80 shadow-lg">
            <div className="flex items-center justify-between text-slate-400 mb-2">
              <span className="text-xs font-mono font-medium">Latencia Inferencia</span>
              <Zap className="w-4 h-4 text-amber-400" />
            </div>
            <div className="text-2xl font-bold font-mono text-white">
              {piTelemetry.modelLatencyMs || 22.4} ms
            </div>
            <div className="w-full bg-slate-900 h-1.5 rounded-full overflow-hidden mt-3">
              <div className="bg-amber-400 h-full rounded-full w-[25%]" />
            </div>
            <span className="text-[10px] font-mono text-slate-500 mt-2 block">
              {piTelemetry.modelEngine || 'ONNX Runtime ARM64'}
            </span>
          </div>
        </div>

        {/* Audit Log Trail */}
        <div className="bg-[#0b1120] border border-slate-800/80 rounded-2xl overflow-hidden shadow-xl flex-1 flex flex-col min-h-[220px]">
          <div className="px-5 py-3 border-b border-slate-800/80 bg-slate-900/60 flex items-center justify-between">
            <span className="text-xs font-mono font-bold uppercase tracking-wider text-slate-400">
              Bitácora de Seguridad y Actuador
            </span>
            <span className="text-[10px] font-mono text-slate-500">
              Host: {backendUrl}
            </span>
          </div>

          <div className="p-4 space-y-2.5 overflow-y-auto">
            {auditEvents.map((ev) => (
              <div
                key={ev.id}
                className="p-3 rounded-xl bg-slate-900/60 border border-slate-800/70 flex items-start justify-between gap-4 text-xs font-mono"
              >
                <div className="flex items-start space-x-3">
                  <div className="w-5 h-5 rounded-full bg-emerald-950 border border-emerald-700/80 text-emerald-400 flex items-center justify-center shrink-0 mt-0.5">
                    <CheckCircle2 className="w-3.5 h-3.5" />
                  </div>
                  <div>
                    <div className="flex items-center space-x-2">
                      <span className="font-bold text-white">{ev.event}</span>
                      <span className="text-[10px] px-1.5 py-0.2 rounded bg-slate-800 text-slate-400 border border-slate-700">
                        {ev.subsystem}
                      </span>
                    </div>
                    <p className="text-slate-400 text-[11px] mt-0.5">{ev.detail}</p>
                  </div>
                </div>

                <span className="text-slate-500 text-[11px] whitespace-nowrap">{ev.time}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}
