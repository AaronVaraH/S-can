import React from 'react'
import {
  Cpu,
  Thermometer,
  HardDrive,
  Radio,
  Server,
  Zap
} from 'lucide-react'

export default function PiTelemetryCard({
  cpuUsage = 42,
  cpuTemp = 48.5,
  ramUsage = '1.2 / 4.0 GB',
  modelEngine = 'ONNX Runtime (ARM64)',
  isSimulator = false
}) {
  const isHot = cpuTemp > 70

  return (
    <div className="bg-[#0e1626] border border-brand-border/70 rounded-2xl p-4 shadow-xl shadow-black/20">
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center space-x-2">
          <Server className="w-4 h-4 text-cyan-400" />
          <h3 className="text-xs font-mono font-bold uppercase tracking-wider text-slate-300">
            Telemetría Raspberry Pi
          </h3>
        </div>
        <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-cyan-950/70 border border-cyan-800 text-cyan-400">
          {isSimulator ? 'Simulated Telemetry' : 'Hardware Telemetry'}
        </span>
      </div>

      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs font-mono">
        {/* CPU Usage */}
        <div className="p-3 rounded-xl bg-slate-950/80 border border-slate-800/80">
          <div className="flex items-center justify-between text-slate-400 mb-1">
            <span className="text-[10px]">Carga CPU</span>
            <Cpu className="w-3.5 h-3.5 text-cyan-400" />
          </div>
          <div className="text-lg font-bold text-white">
            {cpuUsage}%
          </div>
          <div className="w-full bg-slate-900 h-1.5 rounded-full overflow-hidden mt-1.5">
            <div
              className="bg-cyan-500 h-full rounded-full transition-all"
              style={{ width: `${cpuUsage}%` }}
            />
          </div>
        </div>

        {/* Temperature */}
        <div className="p-3 rounded-xl bg-slate-950/80 border border-slate-800/80">
          <div className="flex items-center justify-between text-slate-400 mb-1">
            <span className="text-[10px]">Temperatura Pi</span>
            <Thermometer
              className={`w-3.5 h-3.5 ${isHot ? 'text-rose-400' : 'text-emerald-400'}`}
            />
          </div>
          <div
            className={`text-lg font-bold ${
              isHot ? 'text-rose-400' : 'text-emerald-400'
            }`}
          >
            {cpuTemp}°C
          </div>
          <div className="text-[9px] text-slate-500 mt-1">
            {isHot ? '⚠️ Alta temperatura' : 'Óptimo (<65°C)'}
          </div>
        </div>

        {/* Memory */}
        <div className="p-3 rounded-xl bg-slate-950/80 border border-slate-800/80">
          <div className="flex items-center justify-between text-slate-400 mb-1">
            <span className="text-[10px]">Memoria RAM</span>
            <HardDrive className="w-3.5 h-3.5 text-purple-400" />
          </div>
          <div className="text-sm font-bold text-slate-200 mt-1">
            {ramUsage}
          </div>
          <div className="text-[9px] text-slate-500 mt-1">
            LPDDR4 Edge Cache
          </div>
        </div>

        {/* Model Engine */}
        <div className="p-3 rounded-xl bg-slate-950/80 border border-slate-800/80">
          <div className="flex items-center justify-between text-slate-400 mb-1">
            <span className="text-[10px]">Inferencia Edge</span>
            <Zap className="w-3.5 h-3.5 text-amber-400" />
          </div>
          <div className="text-xs font-bold text-amber-300 mt-1 truncate">
            {modelEngine}
          </div>
          <div className="text-[9px] text-slate-500 mt-1">
            100% Core AI Dedicado
          </div>
        </div>
      </div>
    </div>
  )
}
