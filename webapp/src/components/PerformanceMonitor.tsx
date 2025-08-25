'use client'

import { useState, useEffect, useRef } from 'react'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Activity, HardDrive, Monitor } from 'lucide-react'

interface PerformanceMetrics {
  fps: number
  memoryUsage: number | null
  cpuUsage: number | null
  renderTime: number
}

interface PerformanceMonitorProps {
  enabled?: boolean
  showDetails?: boolean
}

export default function PerformanceMonitor({ enabled = false, showDetails = false }: PerformanceMonitorProps) {
  const [metrics, setMetrics] = useState<PerformanceMetrics>({
    fps: 0,
    memoryUsage: null,
    cpuUsage: null,
    renderTime: 0
  })
  
  const frameCountRef = useRef(0)
  const lastTimeRef = useRef(performance.now())
  const animationFrameRef = useRef<number>()

  // FPS monitoring
  const measureFPS = useRef(() => {
    frameCountRef.current++
    const currentTime = performance.now()
    
    if (currentTime - lastTimeRef.current >= 1000) {
      const fps = Math.round((frameCountRef.current * 1000) / (currentTime - lastTimeRef.current))
      setMetrics(prev => ({ ...prev, fps }))
      frameCountRef.current = 0
      lastTimeRef.current = currentTime
    }
    
    animationFrameRef.current = requestAnimationFrame(measureFPS.current)
  })

  // Memory monitoring
  const measureMemory = useRef(() => {
    if ('memory' in performance) {
      const memory = (performance as any).memory
      const memoryUsage = memory ? Math.round(memory.usedJSHeapSize / 1024 / 1024) : null
      setMetrics(prev => ({ ...prev, memoryUsage }))
    }
  })

  // CPU monitoring (simplified)
  const measureCPU = useRef(() => {
    const start = performance.now()
    // Simulate some work to measure CPU impact
    let result = 0
    for (let i = 0; i < 1000; i++) {
      result += Math.random()
    }
    const end = performance.now()
    const cpuUsage = Math.round(end - start)
    setMetrics(prev => ({ ...prev, cpuUsage }))
  })

  // Render time monitoring
  const measureRenderTime = useRef(() => {
    const start = performance.now()
    // This will be called after each render
    const end = performance.now()
    setMetrics(prev => ({ ...prev, renderTime: Math.round(end - start) }))
  })

  useEffect(() => {
    if (!enabled) return

    // Start FPS monitoring
    animationFrameRef.current = requestAnimationFrame(measureFPS.current)

    // Start memory monitoring
    const memoryInterval = setInterval(measureMemory.current, 2000)

    // Start CPU monitoring
    const cpuInterval = setInterval(measureCPU.current, 5000)

    // Measure render time after each render
    measureRenderTime.current()

    return () => {
      if (animationFrameRef.current) {
        cancelAnimationFrame(animationFrameRef.current)
      }
      clearInterval(memoryInterval)
      clearInterval(cpuInterval)
    }
  }, [enabled])

  if (!enabled) return null

  const getFPSColor = (fps: number) => {
    if (fps >= 55) return 'bg-green-100 text-green-800 border-green-200'
    if (fps >= 45) return 'bg-yellow-100 text-yellow-800 border-yellow-200'
    return 'bg-red-100 text-red-800 border-red-200'
  }

  const getMemoryColor = (memory: number | null) => {
    if (!memory) return 'bg-gray-100 text-gray-800 border-gray-200'
    if (memory < 100) return 'bg-green-100 text-green-800 border-green-200'
    if (memory < 200) return 'bg-yellow-100 text-yellow-800 border-yellow-200'
    return 'bg-red-100 text-red-800 border-red-200'
  }

  const getCPUColor = (cpu: number | null) => {
    if (!cpu) return 'bg-gray-100 text-gray-800 border-gray-200'
    if (cpu < 5) return 'bg-green-100 text-green-800 border-green-200'
    if (cpu < 10) return 'bg-yellow-100 text-yellow-800 border-yellow-200'
    return 'bg-red-100 text-red-800 border-red-200'
  }

  if (!showDetails) {
    return (
      <div className="fixed bottom-4 left-4 z-50">
        <div className="flex gap-2">
          <Badge variant="outline" className={getFPSColor(metrics.fps)}>
            <Monitor className="h-3 w-3 mr-1" />
            {metrics.fps} FPS
          </Badge>
          {metrics.memoryUsage && (
            <Badge variant="outline" className={getMemoryColor(metrics.memoryUsage)}>
              <HardDrive className="h-3 w-3 mr-1" />
              {metrics.memoryUsage}MB
            </Badge>
          )}
          {metrics.cpuUsage && (
            <Badge variant="outline" className={getCPUColor(metrics.cpuUsage)}>
              <Activity className="h-3 w-3 mr-1" />
              {metrics.cpuUsage}ms
            </Badge>
          )}
        </div>
      </div>
    )
  }

  return (
    <div className="fixed bottom-4 left-4 z-50">
      <Card className="w-64">
        <CardHeader className="pb-2">
          <CardTitle className="text-sm flex items-center gap-2">
            <Monitor className="h-4 w-4" />
            Performance
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          <div className="flex justify-between items-center">
            <span className="text-sm">Frame Rate:</span>
            <Badge variant="outline" className={getFPSColor(metrics.fps)}>
              {metrics.fps} FPS
            </Badge>
          </div>
          
          {metrics.memoryUsage && (
            <div className="flex justify-between items-center">
              <span className="text-sm">Memory:</span>
              <Badge variant="outline" className={getMemoryColor(metrics.memoryUsage)}>
                {metrics.memoryUsage} MB
              </Badge>
            </div>
          )}
          
          {metrics.cpuUsage && (
            <div className="flex justify-between items-center">
              <span className="text-sm">CPU Load:</span>
              <Badge variant="outline" className={getCPUColor(metrics.cpuUsage)}>
                {metrics.cpuUsage} ms
              </Badge>
            </div>
          )}
          
          <div className="flex justify-between items-center">
            <span className="text-sm">Render Time:</span>
            <Badge variant="outline">
              {metrics.renderTime} ms
            </Badge>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
