import { defineStore } from 'pinia'
import { ref } from 'vue'
import { useAuthStore } from './auth'
import type { WsMessage } from '@/types/api'

export const useWebSocketStore = defineStore('websocket', () => {
  const socket = ref<WebSocket | null>(null)
  const connected = ref(false)
  const authenticated = ref(false)
  const reconnectAttempts = ref(0)
  const maxReconnectAttempts = 10

  // Message dispatchers
  type MessageHandler = (msg: WsMessage) => void
  const handlers = new Map<string, MessageHandler[]>()

  let heartbeatTimer: ReturnType<typeof setInterval> | null = null
  let reconnectTimer: ReturnType<typeof setTimeout> | null = null

  function getWsUrl(): string {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const host = window.location.host
    return `${protocol}//${host}/ws/online`
  }

  function on(type: string, handler: MessageHandler) {
    const existing = handlers.get(type) || []
    existing.push(handler)
    handlers.set(type, existing)
  }

  function off(type: string, handler: MessageHandler) {
    const existing = handlers.get(type) || []
    handlers.set(type, existing.filter(h => h !== handler))
  }

  function connect() {
    if (socket.value && (socket.value.readyState === WebSocket.OPEN || socket.value.readyState === WebSocket.CONNECTING)) {
      return
    }

    const auth = useAuthStore()
    if (!auth.token) return

    const ws = new WebSocket(getWsUrl())

    ws.onopen = () => {
      connected.value = true
      reconnectAttempts.value = 0
      // Send auth
      ws.send(JSON.stringify({
        type: 'auth',
        token: auth.token,
      }))
      // Start heartbeat
      heartbeatTimer = setInterval(() => {
        if (ws.readyState === WebSocket.OPEN) {
          ws.send(JSON.stringify({ type: 'heartbeat' }))
        }
      }, 15000)
    }

    ws.onmessage = (event) => {
      try {
        const msg: WsMessage = JSON.parse(event.data)
        // Handle auth state
        if (msg.type === 'auth_state') {
          authenticated.value = msg.status === 'authenticated'
        }
        // Dispatch to registered handlers
        const typeHandlers = handlers.get(msg.type)
        if (typeHandlers) {
          typeHandlers.forEach(h => h(msg))
        }
      } catch {
        // ignore malformed messages
      }
    }

    ws.onclose = (event) => {
      connected.value = false
      authenticated.value = false
      if (heartbeatTimer) {
        clearInterval(heartbeatTimer)
        heartbeatTimer = null
      }
      // Don't reconnect on normal closure or auth failure
      if (event.code !== 1000 && event.code !== 1008 && reconnectAttempts.value < maxReconnectAttempts) {
        const delay = Math.min(1000 * Math.pow(2, reconnectAttempts.value), 30000)
        reconnectAttempts.value++
        reconnectTimer = setTimeout(connect, delay)
      }
    }

    ws.onerror = () => {
      // onclose will fire after this
    }

    socket.value = ws
  }

  function disconnect() {
    if (reconnectTimer) {
      clearTimeout(reconnectTimer)
      reconnectTimer = null
    }
    if (heartbeatTimer) {
      clearInterval(heartbeatTimer)
      heartbeatTimer = null
    }
    reconnectAttempts.value = maxReconnectAttempts // prevent reconnect
    if (socket.value) {
      socket.value.close(1000)
      socket.value = null
    }
    connected.value = false
    authenticated.value = false
  }

  function syncAuth() {
    const auth = useAuthStore()
    if (!auth.token) {
      disconnect()
      return
    }
    if (socket.value && socket.value.readyState === WebSocket.OPEN) {
      socket.value.send(JSON.stringify({
        type: 'auth',
        token: auth.token,
      }))
      return
    }
    reconnectAttempts.value = 0
    connect()
  }

  function send(msg: WsMessage) {
    if (socket.value && socket.value.readyState === WebSocket.OPEN) {
      socket.value.send(JSON.stringify(msg))
    }
  }

  return { connected, authenticated, connect, disconnect, syncAuth, send, on, off }
})
