/**
 * SocketIO singleton — single connection, auto-reconnect, room management.
 *
 * Usage:
 *   const socket = useSocketIO()
 *   socket.emit('watch_pending', { id: 42 })
 *   socket.on('pending:update', (data) => { ... })
 *   socket.off('pending:update')
 */
import { io } from 'socket.io-client'

let socket = null

function getSocket() {
  if (!socket) {
    socket = io(window.location.origin, {
      transports: ['polling', 'websocket'],
      reconnection: true,
      reconnectionDelay: 1000,
      reconnectionDelayMax: 5000,
      reconnectionAttempts: Infinity,
    })
    socket.on('connect', () => {
      console.log('[socketio] connected', socket.id)
    })
    socket.on('disconnect', (reason) => {
      console.log('[socketio] disconnected', reason)
    })
    socket.on('connect_error', (err) => {
      console.warn('[socketio] connection error', err.message)
    })
  }
  return socket
}

/**
 * React hook — returns the shared SocketIO instance.
 * Safe to call from multiple components (returns same instance).
 */
export function useSocketIO() {
  return getSocket()
}

/**
 * Send cancel job event.
 */
export function cancelJob(id, table = 'pending_jobs') {
  getSocket().emit('cancel_job', { id, table })
}

/**
 * Send reset job event.
 */
export function resetJob(id, table = 'pending_jobs') {
  getSocket().emit('reset_job', { id, table })
}

/**
 * Watch a pending job for real-time updates.
 */
export function watchPending(id) {
  getSocket().emit('watch_pending', { id })
}

/**
 * Stop watching a pending job.
 */
export function unwatchPending(id) {
  getSocket().emit('unwatch_pending', { id })
}

/**
 * Watch a company for real-time updates.
 */
export function watchCompany(id) {
  getSocket().emit('watch_company', { id })
}

/**
 * Stop watching a company.
 */
export function unwatchCompany(id) {
  getSocket().emit('unwatch_company', { id })
}

/**
 * Watch all skill roadmap progress (single room, all skills).
 */
export function watchSkills() {
  getSocket().emit('watch_skills')
}

/**
 * Stop watching skill roadmap progress.
 */
export function unwatchSkills() {
  getSocket().emit('unwatch_skills')
}

/**
 * Watch career intelligence progress (real-time analysis updates).
 */
export function watchCareerIntel() {
  getSocket().emit('watch_career_intel')
}

/**
 * Stop watching career intelligence progress.
 */
export function unwatchCareerIntel() {
  getSocket().emit('unwatch_career_intel')
}
