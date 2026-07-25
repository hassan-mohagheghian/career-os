/**
 * SocketIO singleton — single connection, auto-reconnect, room management.
 */
import { io, type Socket } from 'socket.io-client'

let socket: Socket | null = null

function getSocket(): Socket {
  if (!socket) {
    socket = io(window.location.origin, {
      transports: ['polling', 'websocket'],
      reconnection: true,
      reconnectionDelay: 1000,
      reconnectionDelayMax: 5000,
      reconnectionAttempts: Infinity,
    })
    socket.on('connect', () => {
      console.log('[socketio] connected', socket!.id)
    })
    socket.on('disconnect', (reason: string) => {
      console.log('[socketio] disconnected', reason)
    })
    socket.on('connect_error', (err: Error) => {
      console.warn('[socketio] connection error', err.message)
    })
  }
  return socket
}

export function useSocketIO(): Socket {
  return getSocket()
}

export function cancelJob(id: number, table = 'pending_jobs'): void {
  getSocket().emit('cancel_job', { id, table })
}

export function resetJob(id: number, table = 'pending_jobs'): void {
  getSocket().emit('reset_job', { id, table })
}

export function watchPending(id: number): void {
  getSocket().emit('watch_pending', { id })
}

export function unwatchPending(id: number): void {
  getSocket().emit('unwatch_pending', { id })
}

export function watchCompany(id: number): void {
  getSocket().emit('watch_company', { id })
}

export function unwatchCompany(id: number): void {
  getSocket().emit('unwatch_company', { id })
}

export function watchSkills(): void {
  getSocket().emit('watch_skills')
}

export function unwatchSkills(): void {
  getSocket().emit('unwatch_skills')
}

export function watchInsights(): void {
  getSocket().emit('watch_insights')
}

export function unwatchInsights(): void {
  getSocket().emit('unwatch_insights')
}

export function watchGeneration(id: number): void {
  getSocket().emit('watch_generation', { id })
}

export function unwatchGeneration(id: number): void {
  getSocket().emit('unwatch_generation', { id })
}
