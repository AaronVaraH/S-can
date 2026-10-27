import React, { useRef, useEffect, useState } from 'react'
import {
  Layers,
  Scan,
  Maximize2,
  Crosshair,
  AlertCircle,
  ShieldCheck,
  ShieldAlert,
  ArrowRight,
  Activity
} from 'lucide-react'

export default function VideoFeed({
  streamUrl,
  isConnected,
  isSimulator,
  lastPrediction,
  modelLatencyMs,
  cameraFps = 30
}) {
  const [showOverlays, setShowOverlays] = useState(true)
  const [showLaser, setShowLaser] = useState(true)
  const [streamError, setStreamError] = useState(false)
  const canvasRef = useRef(null)
  const containerRef = useRef(null)

  // Reset stream error when streamUrl or isConnected changes
  useEffect(() => {
    setStreamError(false)
  }, [streamUrl, isConnected])

  // Canvas drawing loop for scanning ribbon (cinta de escaneo), bounding box, and simulated can
  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas) return
    const ctx = canvas.getContext('2d')
    let animationId

    let scanY = 0
    let scanDirection = 1

    const render = () => {
      ctx.clearRect(0, 0, canvas.width, canvas.height)

      const w = canvas.width
      const h = canvas.height

      // 1. Draw can background (when in simulation, offline, or fallback)
      if (isSimulator || !isConnected || streamError) {
        // Deep industrial inspection background
        ctx.fillStyle = '#060a14'
        ctx.fillRect(0, 0, w, h)

        // Precision optical alignment grid
        ctx.strokeStyle = '#0d1627'
        ctx.lineWidth = 1
        for (let x = 0; x < w; x += 40) {
          ctx.beginPath()
          ctx.moveTo(x, 0)
          ctx.lineTo(x, h)
          ctx.stroke()
        }
        for (let y = 0; y < h; y += 40) {
          ctx.beginPath()
          ctx.moveTo(0, y)
          ctx.lineTo(w, y)
          ctx.stroke()
        }

        // Conveyor belt rail guidelines
        ctx.strokeStyle = '#1e293b'
        ctx.lineWidth = 2
        ctx.beginPath()
        ctx.moveTo(0, h * 0.18)
        ctx.lineTo(w, h * 0.18)
        ctx.moveTo(0, h * 0.82)
        ctx.lineTo(w, h * 0.82)
        ctx.stroke()

        // Aluminum Can geometry (proportional to viewport)
        const canWidth = w * 0.28
        const canHeight = h * 0.52
        const canX = (w - canWidth) / 2
        const canY = (h - canHeight) / 2

        // Can drop shadow
        ctx.shadowColor = 'rgba(0, 0, 0, 0.9)'
        ctx.shadowBlur = 30
        ctx.shadowOffsetY = 15

        // Can body brushed aluminum gradient
        const canGrad = ctx.createLinearGradient(canX, canY, canX + canWidth, canY)
        canGrad.addColorStop(0, '#334155')
        canGrad.addColorStop(0.2, '#64748b')
        canGrad.addColorStop(0.5, '#f1f5f9')
        canGrad.addColorStop(0.8, '#94a3b8')
        canGrad.addColorStop(1, '#1e293b')

        ctx.fillStyle = canGrad
        ctx.beginPath()
        ctx.roundRect(canX, canY, canWidth, canHeight, [18, 18, 22, 22])
        ctx.fill()
        ctx.shadowBlur = 0 // Reset shadow

        // Can top rim ring
        ctx.fillStyle = '#cbd5e1'
        ctx.beginPath()
        ctx.ellipse(canX + canWidth / 2, canY + 10, canWidth * 0.44, 9, 0, 0, Math.PI * 2)
        ctx.fill()

        // Pull-tab slot
        ctx.fillStyle = '#0f172a'
        ctx.beginPath()
        ctx.ellipse(canX + canWidth / 2, canY + 9, 12, 4.5, 0, 0, Math.PI * 2)
        ctx.fill()

        // Can Brand Label
        const isDefect = lastPrediction?.class === 'dañada' || lastPrediction?.class === 'abollada'
        ctx.fillStyle = isDefect ? '#b91c1c' : '#047857'
        ctx.beginPath()
        ctx.roundRect(canX + 6, canY + 48, canWidth - 12, canHeight - 96, 6)
        ctx.fill()

        // Can Typography
        ctx.shadowColor = 'transparent'
        ctx.shadowBlur = 0
        ctx.fillStyle = '#ffffff'
        ctx.font = 'bold 22px "Inter", sans-serif'
        ctx.textAlign = 'center'
        ctx.textBaseline = 'middle'
        ctx.fillText('S-CAN', canX + canWidth / 2, canY + canHeight / 2 - 10)

        ctx.font = '11px "JetBrains Mono", monospace'
        ctx.fillStyle = 'rgba(255, 255, 255, 0.85)'
        ctx.fillText('355ml · PURE SODA', canX + canWidth / 2, canY + canHeight / 2 + 14)

        // Visual dent simulation if defect
        if (isDefect) {
          ctx.fillStyle = 'rgba(15, 23, 42, 0.9)'
          ctx.beginPath()
          ctx.ellipse(canX + canWidth * 0.76, canY + canHeight * 0.52, 20, 30, 0.35, 0, Math.PI * 2)
          ctx.fill()
          ctx.strokeStyle = '#ef4444'
          ctx.lineWidth = 2
          ctx.stroke()
        }
      }

      // 2. Optical Bounding Box & Corner Brackets around Can
      if (showOverlays && lastPrediction) {
        const isDefect = lastPrediction.class === 'dañada' || lastPrediction.class === 'abollada'
        const bboxColor = isDefect ? '#ef4444' : '#10b981'

        const bx = lastPrediction.bbox ? lastPrediction.bbox[0] * w : w * 0.32
        const by = lastPrediction.bbox ? lastPrediction.bbox[1] * h : h * 0.20
        const bw = lastPrediction.bbox ? lastPrediction.bbox[2] * w : w * 0.36
        const bh = lastPrediction.bbox ? lastPrediction.bbox[3] * h : h * 0.60

        // Corner bracket geometry
        const bracketLen = 24
        ctx.strokeStyle = bboxColor
        ctx.lineWidth = 3

        // Top-Left
        ctx.beginPath()
        ctx.moveTo(bx, by + bracketLen)
        ctx.lineTo(bx, by)
        ctx.lineTo(bx + bracketLen, by)
        ctx.stroke()

        // Top-Right
        ctx.beginPath()
        ctx.moveTo(bx + bw - bracketLen, by)
        ctx.lineTo(bx + bw, by)
        ctx.lineTo(bx + bw, by + bracketLen)
        ctx.stroke()

        // Bottom-Left
        ctx.beginPath()
        ctx.moveTo(bx, by + bh - bracketLen)
        ctx.lineTo(bx, by + bh)
        ctx.lineTo(bx + bracketLen, by + bh)
        ctx.stroke()

        // Bottom-Right
        ctx.beginPath()
        ctx.moveTo(bx + bw - bracketLen, by + bh)
        ctx.lineTo(bx + bw, by + bh)
        ctx.lineTo(bx + bw, by + bh - bracketLen)
        ctx.stroke()

        // Precision Center Crosshair
        ctx.strokeStyle = bboxColor
        ctx.lineWidth = 1
        ctx.beginPath()
        ctx.moveTo(bx + bw / 2 - 10, by + bh / 2)
        ctx.lineTo(bx + bw / 2 + 10, by + bh / 2)
        ctx.moveTo(bx + bw / 2, by + bh / 2 - 10)
        ctx.lineTo(bx + bw / 2, by + bh / 2 + 10)
        ctx.stroke()

        // Tech Label Tag above Bounding Box
        const label = `${lastPrediction.class.toUpperCase()} ${(lastPrediction.confidence * 100).toFixed(1)}%`
        ctx.font = 'bold 12px "JetBrains Mono", monospace'
        const textWidth = ctx.measureText(label).width + 18

        ctx.fillStyle = bboxColor
        ctx.beginPath()
        ctx.roundRect(bx, by - 26, textWidth, 22, 4)
        ctx.fill()

        ctx.fillStyle = '#ffffff'
        ctx.textAlign = 'left'
        ctx.textBaseline = 'middle'
        ctx.fillText(label, bx + 9, by - 15)
      }

      // 3. Scanning Laser Ribbon (Cinta Láser)
      if (showLaser) {
        scanY += 2.8 * scanDirection
        if (scanY > h) scanDirection = -1
        if (scanY < 0) scanDirection = 1

        // Wide cyan glow ribbon
        const laserGrad = ctx.createLinearGradient(0, scanY - 14, 0, scanY + 14)
        laserGrad.addColorStop(0, 'rgba(6, 182, 212, 0)')
        laserGrad.addColorStop(0.5, 'rgba(6, 182, 212, 0.9)')
        laserGrad.addColorStop(1, 'rgba(6, 182, 212, 0)')

        ctx.fillStyle = laserGrad
        ctx.fillRect(0, scanY - 14, w, 28)

        // Sharp core laser line
        ctx.strokeStyle = '#67e8f9'
        ctx.lineWidth = 2
        ctx.beginPath()
        ctx.moveTo(0, scanY)
        ctx.lineTo(w, scanY)
        ctx.stroke()
      }

      animationId = requestAnimationFrame(render)
    }

    render()

    return () => cancelAnimationFrame(animationId)
  }, [isSimulator, isConnected, streamError, lastPrediction, showOverlays, showLaser])

  const isDefect =
    lastPrediction?.class === 'dañada' ||
    lastPrediction?.class === 'abollada' ||
    lastPrediction?.class === 'defectuosa'

  return (
    <div className="relative flex-1 w-full h-full flex flex-col items-center justify-center bg-[#070b14] overflow-hidden p-3 sm:p-5 select-none">
      {/* Central Viewport Frame */}
      <div
        ref={containerRef}
        className="relative w-full max-w-5xl h-full max-h-[82vh] aspect-video bg-[#050811] rounded-2xl border border-slate-800/80 shadow-2xl shadow-black/60 flex items-center justify-center overflow-hidden"
      >
        {/* HUD Corner Reticles */}
        <div className="hud-corner-tl m-3 z-20 pointer-events-none" />
        <div className="hud-corner-tr m-3 z-20 pointer-events-none" />
        <div className="hud-corner-bl m-3 z-20 pointer-events-none" />
        <div className="hud-corner-br m-3 z-20 pointer-events-none" />

        {/* Ambient Center Optical Crosshair */}
        <div className="absolute inset-0 flex items-center justify-center pointer-events-none opacity-15 z-10">
          <Crosshair className="w-56 h-56 text-cyan-400" strokeWidth={1} />
        </div>

        {/* Real Live MJPEG Stream from Raspberry Pi when active */}
        {!isSimulator && isConnected && !streamError && (
          <img
            src={streamUrl}
            alt="Raspberry Pi Video Feed"
            onError={() => setStreamError(true)}
            className="absolute inset-0 w-full h-full object-contain z-0"
          />
        )}

        {/* Dynamic Canvas (Laser Ribbon + Bounding Boxes + Can Graphic) */}
        <canvas
          ref={canvasRef}
          width={960}
          height={540}
          className="absolute inset-0 w-full h-full object-contain z-10 pointer-events-none"
        />

        {/* Floating Minimalist Verdict Banner on Top Right */}
        {lastPrediction && (
          <div className="absolute top-4 right-4 z-20 transition-all duration-300">
            <div
              className={`px-3.5 py-2 rounded-xl backdrop-blur-md border shadow-xl flex items-center space-x-3 ${
                isDefect
                  ? 'bg-rose-950/80 border-rose-600/80 text-rose-200 shadow-rose-950/50'
                  : 'bg-emerald-950/80 border-emerald-600/80 text-emerald-200 shadow-emerald-950/50'
              }`}
            >
              <div
                className={`w-7 h-7 rounded-lg flex items-center justify-center border ${
                  isDefect
                    ? 'bg-rose-900/60 border-rose-500 text-rose-300'
                    : 'bg-emerald-900/60 border-emerald-500 text-emerald-300'
                }`}
              >
                {isDefect ? (
                  <ShieldAlert className="w-4 h-4" />
                ) : (
                  <ShieldCheck className="w-4 h-4" />
                )}
              </div>

              <div className="flex flex-col">
                <div className="flex items-center space-x-2">
                  <span className="text-xs font-mono font-bold tracking-tight uppercase">
                    {isDefect ? 'LATA RECHAZADA' : 'LATA INTACTA'}
                  </span>
                  <span className="text-[10px] font-mono opacity-80">
                    {(lastPrediction.confidence * 100).toFixed(1)}%
                  </span>
                </div>
                <span className="text-[10px] font-mono opacity-70">
                  {isDefect
                    ? `Defecto: ${lastPrediction.defectType || 'Abolladura'}`
                    : 'Superficie Conforme · OK'}
                </span>
              </div>
            </div>
          </div>
        )}

        {/* Floating Minimalist Camera Diagnostics Pill on Top Left */}
        <div className="absolute top-4 left-4 z-20 flex items-center space-x-2 text-[10px] font-mono text-slate-400 bg-slate-900/70 backdrop-blur-md px-2.5 py-1.5 rounded-lg border border-slate-800/80">
          <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
          <span>MJPEG 60Hz</span>
          <span className="text-slate-600">|</span>
          <span>{modelLatencyMs}ms AI</span>
        </div>

        {/* Floating Bottom Toolbar for Bounding Box / Laser Toggles */}
        <div className="absolute bottom-4 inset-x-4 z-20 flex items-center justify-between pointer-events-none">
          <div className="flex items-center space-x-2 pointer-events-auto">
            {/* Toggle Bounding Box */}
            <button
              onClick={() => setShowOverlays(!showOverlays)}
              className={`px-3 py-1.5 text-xs font-mono rounded-lg flex items-center gap-1.5 transition backdrop-blur-md border ${
                showOverlays
                  ? 'bg-cyan-950/80 text-cyan-300 border-cyan-600/80 shadow-[0_0_10px_rgba(6,182,212,0.2)]'
                  : 'bg-slate-900/80 text-slate-500 border-slate-800'
              }`}
            >
              <Layers className="w-3.5 h-3.5" />
              <span>Bounding Box</span>
            </button>

            {/* Toggle Laser Cinta */}
            <button
              onClick={() => setShowLaser(!showLaser)}
              className={`px-3 py-1.5 text-xs font-mono rounded-lg flex items-center gap-1.5 transition backdrop-blur-md border ${
                showLaser
                  ? 'bg-cyan-950/80 text-cyan-300 border-cyan-600/80 shadow-[0_0_10px_rgba(6,182,212,0.2)]'
                  : 'bg-slate-900/80 text-slate-500 border-slate-800'
              }`}
            >
              <Scan className="w-3.5 h-3.5" />
              <span>Cinta Láser</span>
            </button>
          </div>

          <div className="text-[11px] font-mono text-slate-400 bg-slate-900/70 backdrop-blur-md px-3 py-1.5 rounded-lg border border-slate-800/80 pointer-events-auto">
            <span>Resolución: 1280x720 · YOLOv8 Edge</span>
          </div>
        </div>
      </div>
    </div>
  )
}
