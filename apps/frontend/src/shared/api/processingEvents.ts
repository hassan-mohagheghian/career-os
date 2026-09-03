import type { SSEEventEnvelope, SSEEventType } from '@/entities/processing/types'

const SSE_URL = '/events/processing'

const EVENT_TYPES: SSEEventType[] = [
  'execution.created',
  'execution.started',
  'execution.completed',
  'execution.failed',
  'execution.cancelled',
  'queue.entry.removed',
  'workflow.step.started',
  'workflow.step.progress',
  'workflow.step.completed',
  'workflow.step.failed',
]

type Listener = (type: SSEEventType, data: SSEEventEnvelope) => void

let es: EventSource | null = null
let listeners = new Set<Listener>()
let reconnectTimeout: ReturnType<typeof setTimeout> | null = null
let reconnectAttempts = 0

function connect() {
  if (es || reconnectTimeout) return

  const socket = new EventSource(SSE_URL)
  es = socket

  for (const type of EVENT_TYPES) {
    socket.addEventListener(type, (e) => {
      try {
        const data: SSEEventEnvelope = JSON.parse((e as MessageEvent).data)
        listeners.forEach((listener) => listener(type, data))
      } catch {
        // ignore malformed events
      }
    })
  }

  socket.onopen = () => {
    reconnectAttempts = 0
  }

  socket.onerror = () => {
    socket.close()
    if (es === socket) es = null
    if (listeners.size === 0) return
    reconnectAttempts += 1
    const delay = Math.min(3000 * Math.pow(2, reconnectAttempts - 1), 30000)
    reconnectTimeout = setTimeout(() => {
      reconnectTimeout = null
      connect()
    }, delay)
  }
}

function disconnect() {
  if (reconnectTimeout) {
    clearTimeout(reconnectTimeout)
    reconnectTimeout = null
  }
  if (es) {
    es.close()
    es = null
  }
  reconnectAttempts = 0
}

export function subscribeProcessingEvents(listener: Listener): () => void {
  listeners.add(listener)
  connect()
  return () => {
    listeners.delete(listener)
    if (listeners.size === 0) {
      disconnect()
    }
  }
}
