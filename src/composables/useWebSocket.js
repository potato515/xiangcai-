import { ref, onUnmounted } from 'vue'

export function useWebSocket(url, options = {}) {
  const {
    autoReconnect = true,
    reconnectInterval = 3000,
    maxReconnectAttempts = 10,
    onMessage,
    onOpen,
    onClose,
    onError
  } = options

  const ws = ref(null)
  const connected = ref(false)
  const lastMessage = ref(null)
  const reconnectAttempts = ref(0)
  const shouldReconnect = ref(true)

  let reconnectTimer = null

  const connect = () => {
    if (ws.value && ws.value.readyState === WebSocket.OPEN) return

    try {
      ws.value = new WebSocket(url)
    } catch (e) {
      console.error('WebSocket connection failed:', e)
      scheduleReconnect()
      return
    }

    ws.value.onopen = () => {
      connected.value = true
      reconnectAttempts.value = 0
      onOpen?.()
    }

    ws.value.onmessage = (event) => {
      try {
        lastMessage.value = JSON.parse(event.data)
      } catch {
        lastMessage.value = event.data
      }
      onMessage?.(lastMessage.value)
    }

    ws.value.onclose = () => {
      connected.value = false
      onClose?.()
      if (shouldReconnect.value && autoReconnect) {
        scheduleReconnect()
      }
    }

    ws.value.onerror = (error) => {
      onError?.(error)
    }
  }

  const scheduleReconnect = () => {
    if (reconnectAttempts.value >= maxReconnectAttempts) {
      console.warn('WebSocket max reconnect attempts reached')
      return
    }
    reconnectAttempts.value++
    clearTimeout(reconnectTimer)
    reconnectTimer = setTimeout(() => {
      if (shouldReconnect.value) connect()
    }, reconnectInterval)
  }

  const send = (data) => {
    if (ws.value && ws.value.readyState === WebSocket.OPEN) {
      ws.value.send(typeof data === 'string' ? data : JSON.stringify(data))
      return true
    }
    return false
  }

  const disconnect = () => {
    shouldReconnect.value = false
    clearTimeout(reconnectTimer)
    if (ws.value) {
      ws.value.close()
      ws.value = null
    }
    connected.value = false
  }

  onUnmounted(() => {
    disconnect()
  })

  return {
    ws,
    connected,
    lastMessage,
    reconnectAttempts,
    connect,
    disconnect,
    send
  }
}
