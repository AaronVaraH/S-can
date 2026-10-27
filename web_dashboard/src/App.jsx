import React, { useState, useEffect, useRef, useCallback } from 'react'
import Sidebar from './components/Sidebar'
import Navbar from './components/Navbar'
import VideoFeed from './components/VideoFeed'
import HistoryView from './components/HistoryView'
import AuditView from './components/AuditView'
import SettingsModal from './components/SettingsModal'
import { soundFx } from './utils/audio'

export default function App() {
  // Navigation & Layout State
  const [isSidebarOpen, setIsSidebarOpen] = useState(true)
  const [activeTab, setActiveTab] = useState('camara') // 'camara' | 'history' | 'audit'

  // Connection and Mode State
  const [backendUrl, setBackendUrl] = useState(() => {
    return localStorage.getItem('scan_backend_url') || 'http://localhost:8000'
  })
  const [isSimulator, setIsSimulator] = useState(true) // Silent simulator default for realistic preview
  const [connectionStatus, setConnectionStatus] = useState('disconnected')
  const [pingMs, setPingMs] = useState(18)
  const [soundEnabled, setSoundEnabled] = useState(true)
  const [confidenceThreshold, setConfidenceThreshold] = useState(0.75)
  const [isSettingsOpen, setIsSettingsOpen] = useState(false)
  const [isTestingConnection, setIsTestingConnection] = useState(false)

  // Real-time Detection & Telemetry State
  const [lastPrediction, setLastPrediction] = useState({
    id: 28,
    time: '00:15:20',
    class: 'intacta',
    confidence: 0.985,
    defectType: 'Conforme',
    latency: 22.4,
    bbox: [0.32, 0.20, 0.36, 0.60]
  })

  const [metrics, setMetrics] = useState({
    total: 28,
    passed: 24,
    rejected: 4
  })

  const [recentDetections, setRecentDetections] = useState([
    {
      id: 28,
      time: '00:15:20',
      class: 'intacta',
      confidence: 0.985,
      defectType: 'Conforme',
      latency: 22.4,
      bbox: [0.32, 0.20, 0.36, 0.60]
    },
    {
      id: 27,
      time: '00:14:52',
      class: 'intacta',
      confidence: 0.965,
      defectType: 'Conforme',
      latency: 21.8,
      bbox: [0.32, 0.20, 0.36, 0.60]
    },
    {
      id: 26,
      time: '00:14:15',
      class: 'dañada',
      confidence: 0.972,
      defectType: 'Abolladura Lateral',
      latency: 24.2,
      bbox: [0.31, 0.19, 0.37, 0.62]
    },
    {
      id: 25,
      time: '00:13:38',
      class: 'intacta',
      confidence: 0.991,
      defectType: 'Conforme',
      latency: 20.9,
      bbox: [0.32, 0.20, 0.36, 0.60]
    },
    {
      id: 24,
      time: '00:13:02',
      class: 'dañada',
      confidence: 0.948,
      defectType: 'Golpe en Reborde Superior',
      latency: 23.5,
      bbox: [0.31, 0.19, 0.37, 0.62]
    }
  ])

  const [piTelemetry, setPiTelemetry] = useState({
    cpuUsage: 36,
    cpuTemp: 47.8,
    ramUsage: '1.2 / 4.0 GB',
    modelEngine: 'ONNX Runtime (ARM64)',
    modelLatencyMs: 22.4
  })

  const wsRef = useRef(null)
  const scanCounterRef = useRef(29)

  // Save backend URL on change
  const handleSaveBackendUrl = (url) => {
    const cleanUrl = url.trim().replace(/\/+$/, '')
    setBackendUrl(cleanUrl)
    localStorage.setItem('scan_backend_url', cleanUrl)
  }

  // Handle incoming detection event (shared by live WS and simulator)
  const processDetection = useCallback((detection) => {
    setLastPrediction(detection)

    const isDefect =
      detection.class === 'dañada' ||
      detection.class === 'abollada' ||
      detection.class === 'defectuosa'

    // Sound feedback
    if (isDefect) {
      soundFx.playDefect()
    } else {
      soundFx.playPass()
    }

    // Update KPI counters
    setMetrics((prev) => ({
      total: prev.total + 1,
      passed: prev.passed + (isDefect ? 0 : 1),
      rejected: prev.rejected + (isDefect ? 1 : 0)
    }))

    // Append to audit feed (keep max 30)
    setRecentDetections((prev) => [detection, ...prev.slice(0, 29)])
  }, [])

  // 1. Live WebSocket and Health Ping loop when NOT in simulator mode
  useEffect(() => {
    if (isSimulator) {
      if (wsRef.current) {
        wsRef.current.close()
        wsRef.current = null
      }
      return
    }

    let isMounted = true
    const wsUrl = `${backendUrl.replace(/^http/, 'ws')}/ws/telemetry`

    const connectWs = () => {
      try {
        setConnectionStatus('reconnecting')
        const ws = new WebSocket(wsUrl)
        wsRef.current = ws

        ws.onopen = () => {
          if (!isMounted) return
          setConnectionStatus('connected')
        }

        ws.onmessage = (event) => {
          if (!isMounted) return
          try {
            const data = JSON.parse(event.data)
            if (data.type === 'detection') {
              processDetection(data.payload)
            } else if (data.type === 'telemetry') {
              setPiTelemetry(data.payload)
            }
          } catch (e) {
            console.error('Error parsing WebSocket message', e)
          }
        }

        ws.onclose = () => {
          if (!isMounted) return
          setConnectionStatus('disconnected')
        }

        ws.onerror = () => {
          if (!isMounted) return
          setConnectionStatus('disconnected')
        }
      } catch {
        setConnectionStatus('disconnected')
      }
    }

    connectWs()

    // Periodic HTTP ping to check latency and health
    const pingInterval = setInterval(async () => {
      const start = performance.now()
      try {
        const res = await fetch(`${backendUrl}/health`, { method: 'GET' })
        if (res.ok) {
          const rtt = Math.round(performance.now() - start)
          setPingMs(rtt)
        }
      } catch {
        // Ping failed
      }
    }, 4000)

    return () => {
      isMounted = false
      clearInterval(pingInterval)
      if (wsRef.current) {
        wsRef.current.close()
      }
    }
  }, [backendUrl, isSimulator, processDetection])

  // 2. Background simulation loop (subtle, keeps can scanner alive without clutter)
  useEffect(() => {
    if (!isSimulator) return

    const defectTypes = [
      'Abolladura Lateral',
      'Golpe en Reborde Superior',
      'Deformidad por Aplastamiento',
      'Corrosión / Óxido Superficial'
    ]

    const interval = setInterval(() => {
      const nextId = scanCounterRef.current++
      // 80% pass, 20% defect
      const isDefect = Math.random() < 0.20
      const cls = isDefect ? 'dañada' : 'intacta'
      const confidence = isDefect
        ? 0.89 + Math.random() * 0.10
        : 0.95 + Math.random() * 0.048

      const now = new Date()
      const timeStr = now.toTimeString().split(' ')[0]

      const mockEvent = {
        id: nextId,
        time: timeStr,
        class: cls,
        confidence: parseFloat(confidence.toFixed(3)),
        defectType: isDefect
          ? defectTypes[Math.floor(Math.random() * defectTypes.length)]
          : 'Conforme',
        latency: parseFloat((21.5 + Math.random() * 4).toFixed(1)),
        bbox: isDefect
          ? [0.31 + Math.random() * 0.03, 0.19, 0.37, 0.62]
          : [0.32, 0.20, 0.36, 0.60]
      }

      processDetection(mockEvent)

      // Randomize Pi stats slightly
      setPiTelemetry({
        cpuUsage: Math.floor(34 + Math.random() * 8),
        cpuTemp: parseFloat((46.8 + Math.random() * 2.5).toFixed(1)),
        ramUsage: '1.2 / 4.0 GB',
        modelEngine: 'ONNX Runtime (ARM64)',
        modelLatencyMs: mockEvent.latency
      })
    }, 4800)

    return () => clearInterval(interval)
  }, [isSimulator, processDetection])

  // Manual Trigger Button Handler
  const handleManualTrigger = () => {
    const nextId = scanCounterRef.current++
    const isDefect = lastPrediction?.class === 'intacta'
    const now = new Date()

    const manualEvent = {
      id: nextId,
      time: now.toTimeString().split(' ')[0],
      class: isDefect ? 'dañada' : 'intacta',
      confidence: 0.978,
      defectType: isDefect ? 'Abolladura de Prueba' : 'Conforme',
      latency: 22.8,
      bbox: [0.32, 0.20, 0.36, 0.60]
    }

    processDetection(manualEvent)
  }

  // Sound toggle
  const handleToggleSound = () => {
    const enabled = soundFx.toggle()
    setSoundEnabled(enabled)
  }

  // Reset KPI counters
  const handleResetCounters = () => {
    setMetrics({ total: 0, passed: 0, rejected: 0 })
    setRecentDetections([])
    setLastPrediction(null)
  }

  // Ping test for Settings modal
  const handleTestConnection = async (url) => {
    setIsTestingConnection(true)
    try {
      const res = await fetch(`${url}/health`, { method: 'GET' })
      setIsTestingConnection(false)
      if (res.ok) {
        return { success: true, message: '¡Conexión exitosa con FastAPI backend!' }
      } else {
        return { success: false, message: `Error HTTP ${res.status}: Servidor no responde OK` }
      }
    } catch {
      setIsTestingConnection(false)
      return { success: false, message: `No se pudo conectar a ${url}. Revisa la IP.` }
    }
  }

  return (
    <div className="h-screen w-screen max-h-screen overflow-hidden bg-[#080c14] text-slate-100 flex flex-row font-sans selection:bg-cyan-500/20">
      {/* 1. Collapsible Sidebar (Branding Header, Navigation Menu, Compact Metrics) */}
      <Sidebar
        isOpen={isSidebarOpen}
        onToggle={() => setIsSidebarOpen(!isSidebarOpen)}
        activeTab={activeTab}
        onSelectTab={setActiveTab}
        metrics={metrics}
        onResetMetrics={handleResetCounters}
        piTelemetry={piTelemetry}
        connectionStatus={connectionStatus}
        isSimulator={isSimulator}
        onOpenSettings={() => setIsSettingsOpen(true)}
        onManualTrigger={handleManualTrigger}
      />

      {/* 2. Main Content Area */}
      <div className="flex-1 h-screen max-h-screen overflow-hidden flex flex-col min-w-0 bg-[#070b14]">
        {/* Simple Navbar with Hamburger ellipse trigger when sidebar is collapsed, metrics, and actions */}
        <Navbar
          isSidebarOpen={isSidebarOpen}
          onToggleSidebar={() => setIsSidebarOpen(!isSidebarOpen)}
          activeTab={activeTab}
          metrics={metrics}
          connectionStatus={connectionStatus}
          isSimulator={isSimulator}
          onToggleSimulator={() => setIsSimulator(!isSimulator)}
          soundEnabled={soundEnabled}
          onToggleSound={handleToggleSound}
          onOpenSettings={() => setIsSettingsOpen(true)}
          onManualTrigger={handleManualTrigger}
          lastPrediction={lastPrediction}
        />

        {/* View Content (100% viewport, no vertical scroll) */}
        <main className="flex-1 h-[calc(100vh-3.5rem)] overflow-hidden flex flex-col">
          {activeTab === 'camara' && (
            <VideoFeed
              streamUrl={`${backendUrl}/video_feed`}
              isConnected={connectionStatus === 'connected'}
              isSimulator={isSimulator}
              lastPrediction={lastPrediction}
              modelLatencyMs={piTelemetry.modelLatencyMs}
              cameraFps={30}
            />
          )}

          {activeTab === 'history' && (
            <HistoryView recentDetections={recentDetections} />
          )}

          {activeTab === 'audit' && (
            <AuditView
              piTelemetry={piTelemetry}
              metrics={metrics}
              connectionStatus={connectionStatus}
              backendUrl={backendUrl}
            />
          )}
        </main>
      </div>

      {/* Settings Modal */}
      <SettingsModal
        isOpen={isSettingsOpen}
        onClose={() => setIsSettingsOpen(false)}
        backendUrl={backendUrl}
        onSaveBackendUrl={handleSaveBackendUrl}
        confidenceThreshold={confidenceThreshold}
        onSaveThreshold={setConfidenceThreshold}
        onTestConnection={handleTestConnection}
        isTestingConnection={isTestingConnection}
      />
    </div>
  )
}
