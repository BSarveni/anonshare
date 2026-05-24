/**
 * Group chat uses the API's native WebSocket endpoint (not the Socket.IO protocol).
 * socket.io-client is listed for optional future use; this client uses the browser WebSocket API.
 */
export type WsMessage = {
  type: 'message' | 'error'
  content: string
  pseudonym?: string
  timestamp?: string
}

export function groupWebSocketUrl(groupId: string, token: string): string {
  const base = import.meta.env.VITE_WS_URL.replace(/\/$/, '')
  return `${base}/ws/${groupId}?token=${encodeURIComponent(token)}`
}

export function connectGroupChat(
  groupId: string,
  token: string,
  handlers: {
    onMessage: (msg: WsMessage) => void
    onClose?: () => void
    onError?: () => void
  },
): WebSocket {
  const ws = new WebSocket(groupWebSocketUrl(groupId, token))

  ws.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data) as WsMessage
      handlers.onMessage(data)
    } catch {
      /* ignore malformed */
    }
  }

  ws.onerror = () => handlers.onError?.()
  ws.onclose = () => handlers.onClose?.()

  return ws
}

export function sendChatMessage(ws: WebSocket, content: string) {
  if (ws.readyState === WebSocket.OPEN) {
    ws.send(JSON.stringify({ content }))
  }
}
