import { useEffect, useRef, useState, type FormEvent } from 'react'
import { Link, useParams } from 'react-router-dom'
import { groupsApi, type ChatMessage } from '../lib/api'
import { connectGroupChat, sendChatMessage } from '../lib/ws'

export default function GroupChatPage() {
  const { id: groupId } = useParams<{ id: string }>()
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [input, setInput] = useState('')
  const [error, setError] = useState<string | null>(null)
  const bottomRef = useRef<HTMLDivElement>(null)
  const wsRef = useRef<WebSocket | null>(null)

  useEffect(() => {
    if (!groupId) return
    groupsApi
      .messages(groupId)
      .then(({ data }) => setMessages(data))
      .catch(() => setError('Could not load messages'))

    const token = localStorage.getItem('token')
    if (!token) return

    const ws = connectGroupChat(groupId, token, {
      onMessage: (msg) => {
        if (msg.type === 'error') {
          setError(msg.content)
          return
        }
        if (msg.type === 'message' && msg.pseudonym && msg.timestamp) {
          setMessages((prev) => [
            ...prev,
            {
              content: msg.content,
              pseudonym: msg.pseudonym ?? 'Unknown',
              created_at: msg.timestamp ?? new Date().toISOString(),
            },
          ])
        }
      },
      onClose: () => setError('Disconnected from chat'),
    })
    wsRef.current = ws

    return () => {
      ws.close()
      wsRef.current = null
    }
  }, [groupId])

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  function handleSend(e: FormEvent) {
    e.preventDefault()
    const text = input.trim()
    if (!text || !wsRef.current) return
    sendChatMessage(wsRef.current, text)
    setInput('')
    setError(null)
  }

  return (
    <div className="flex h-[calc(100vh)] flex-col">
      <div className="border-b border-slate-200 px-6 py-4">
        <Link to="/groups" className="text-sm text-slate-500 hover:text-slate-800">
          ← Groups
        </Link>
        <h1 className="mt-1 text-lg font-semibold text-slate-900">Group chat</h1>
      </div>

      <div className="flex-1 overflow-y-auto px-6 py-4">
        {messages.map((m, i) => (
          <div key={`${m.created_at}-${i}`} className="mb-3">
            <div className="flex items-baseline gap-2">
              <span className="text-sm font-medium text-slate-800">{m.pseudonym}</span>
              <time className="text-xs text-slate-400">
                {new Date(m.created_at).toLocaleString()}
              </time>
            </div>
            <p className="mt-0.5 text-sm text-slate-700">{m.content}</p>
          </div>
        ))}
        <div ref={bottomRef} />
      </div>

      {error && (
        <p className="border-t border-red-100 bg-red-50 px-6 py-2 text-sm text-red-700">{error}</p>
      )}

      <form onSubmit={handleSend} className="border-t border-slate-200 p-4">
        <div className="flex gap-2">
          <input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Message…"
            className="flex-1 rounded-lg border border-slate-200 px-3 py-2 text-sm outline-none focus:border-slate-400"
          />
          <button
            type="submit"
            className="rounded-lg bg-slate-900 px-4 py-2 text-sm font-medium text-white hover:bg-slate-800"
          >
            Send
          </button>
        </div>
      </form>
    </div>
  )
}
