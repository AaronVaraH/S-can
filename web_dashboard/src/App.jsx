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

  // Connection State
  const [backendUrl, setBackendUrl] = useState(() => {
    return localStorage.getItem('scan_backend_url') || 'http://localhost:8000'
  })
  const [connectionStatus, setConnectionStatus] = useState('disconnected') // 'connected' | 'reconnecting' | 'disconnected'
  const [pingMs, setPingMs] = useState(null)
  const [soundEnabled, setSoundEnabled] = useState(true)
  const [confidenceThreshold, setConfidenceThreshold] = useState(0.75)
  const [isSettingsOpen, setIsSettingsOpen] = useState(false)
  const [isTestingConnection, setIsTestingConnection] = useState(false)
  const [isTriggering, setIsTriggering] = useState(false)

  // Real-time Detection & Telemetry State (NO MOCK DATA)
  const [lastPrediction, setLastPrediction] = useState(null)
  const [metrics, setMetrics] = useState({
    total: 0,
    passed: 0,
    rejected: 0
  })
  const [recentDetections, setRecentDetections] = useState([])
  const [piTelemetry, setPiTelemetry] = useState({
    cpuUsage: 0,
    cpuTemp: 0,
    ramUsage: '--',
    modelEngine: 'ONNX Runtime',
    modelLatencyMs: 0
  })

  const wsRef = useRef(null)
  const reconnectTimeoutRef = useRef(null)

  // Save backend URL on change
  const handleSaveBackendUrl = (url) => {
    const cleanUrl = url.trim().replace(/\/+$/, '')
    setBackendUrl(cleanUrl)
    localStorage.setItem('scan_backend_url', cleanUrl)
  }

  // Handle incoming detection event from real WebSocket
  const processDetection = useCallback((detection) => {
    if (!detection) return
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

    // Append to history feed (keep up to 50 real entries)
    setRecentDetections((prev) => [detection, ...prev.slice(0, 49)])
  }, [])

  // 1. Live WebSocket and Health Ping loop (Continuous Real Connection)
  useEffect(() => {
    let isMounted = true
    const wsUrl = `${backendUrl.replace(/^http/, 'ws')}/ws/telemetry`

    const connectWs = () => {
      if (!isMounted) return
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
            if (data.type === 'detection' && data.payload) {
              processDetection(data.payload)
            } else if (data.type === 'telemetry' && data.payload) {
              setPiTelemetry((prev) => ({
                ...prev,
                ...data.payload
              }))
            }
          } catch (e) {
            console.error('Error parsing WebSocket message', e)
          }
        }

        ws.onclose = () => {
          if (!isMounted) return
          setConnectionStatus('disconnected')
          // Auto-reconnect after 3.5 seconds
          reconnectTimeoutRef.current = setTimeout(connectWs, 3500)
        }

        ws.onerror = () => {
          if (!isMounted) return
          setConnectionStatus('disconnected')
        }
      } catch {
        if (!isMounted) return
        setConnectionStatus('disconnected')
        reconnectTimeoutRef.current = setTimeout(connectWs, 3500)
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
        } else {
          setPingMs(null)
        }
      } catch {
        setPingMs(null)
      }
    }, 4000)

    return () => {
      isMounted = false
      clearInterval(pingInterval)
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current)
      }
      if (wsRef.current) {
        wsRef.current.close()
      }
    }
  }, [backendUrl, processDetection])

  // Real Manual Trigger Button Handler (communicates with Raspberry Pi)
  const handleManualTrigger = async () => {
    setIsTriggering(true)
    try {
      // If WebSocket is open, send trigger command
      if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
        wsRef.current.send(JSON.stringify({ action: 'trigger' }))
      }
      
      // Also request camera status / trigger endpoint
      await fetch(`${backendUrl}/camera/status`, { method: 'GET' }).catch(() => {})
    } catch (e) {
      console.warn('Trigger dispatch error', e)
    } finally {
      setTimeout(() => setIsTriggering(false), 300)
    }
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
        return { success: true, message: '¡Conexión establecida con la Raspberry Pi!' }
      } else {
        return { success: false, message: `Error HTTP ${res.status}: Servidor no responde OK` }
      }
    } catch {
      setIsTestingConnection(false)
      return { success: false, message: `No se pudo conectar a ${url}. Verifica IP y puerto.` }
    }
  }

  return (
    <div className="h-screen w-screen max-h-screen overflow-hidden ambient-bg text-slate-100 flex flex-row font-sans selection:bg-cyan-500/20">
      {/* 1. Glassmorphic Collapsible Sidebar */}
      <Sidebar
        isOpen={isSidebarOpen}
        onToggle={() => setIsSidebarOpen(!isSidebarOpen)}
        activeTab={activeTab}
        onSelectTab={setActiveTab}
        metrics={metrics}
        onResetMetrics={handleResetCounters}
        piTelemetry={piTelemetry}
        connectionStatus={connectionStatus}
        pingMs={pingMs}
        onOpenSettings={() => setIsSettingsOpen(true)}
        onManualTrigger={handleManualTrigger}
        isTriggering={isTriggering}
      />

      {/* 2. Main Content Area */}
      <div className="flex-1 h-screen max-h-screen overflow-hidden flex flex-col min-w-0">
        {/* Glassmorphic Top Navbar */}
        <Navbar
          isSidebarOpen={isSidebarOpen}
          onToggleSidebar={() => setIsSidebarOpen(!isSidebarOpen)}
          activeTab={activeTab}
          metrics={metrics}
          connectionStatus={connectionStatus}
          pingMs={pingMs}
          soundEnabled={soundEnabled}
          onToggleSound={handleToggleSound}
          onOpenSettings={() => setIsSettingsOpen(true)}
          onManualTrigger={handleManualTrigger}
          isTriggering={isTriggering}
          lastPrediction={lastPrediction}
        />

        {/* View Content (100% viewport, no vertical page overflow) */}
        <main className="flex-1 h-[calc(100vh-3.5rem)] overflow-hidden flex flex-col p-3 sm:p-4">
          {activeTab === 'camara' && (
            <VideoFeed
              streamUrl={`${backendUrl}/video_feed`}
              isConnected={connectionStatus === 'connected'}
              lastPrediction={lastPrediction}
              modelLatencyMs={piTelemetry.modelLatencyMs}
              recentDetections={recentDetections}
              onManualTrigger={handleManualTrigger}
              isTriggering={isTriggering}
            />
          )}

          {activeTab === 'history' && (
            <HistoryView
              recentDetections={recentDetections}
              onResetMetrics={handleResetCounters}
            />
          )}

          {activeTab === 'audit' && (
            <AuditView
              piTelemetry={piTelemetry}
              metrics={metrics}
              connectionStatus={connectionStatus}
              backendUrl={backendUrl}
              pingMs={pingMs}
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
