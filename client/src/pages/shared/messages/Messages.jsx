import { useEffect, useMemo, useRef, useState } from 'react'
import { useLocation, useNavigate } from 'react-router-dom'
import { CheckCircle2, Home, MessageCircle, Send, Sparkles, XCircle } from 'lucide-react'
import {
  acceptRentalRequest,
  getRentalConversations,
  rejectRentalRequest,
  sendRentalRequestMessage,
} from '../../../services/listingService'
import { useAuthStore } from '../../../store/authStore'
import './Messages.scss'

const formatTime = (value) => {
  if (!value) return ''
  return new Intl.DateTimeFormat('uz-UZ', { day: '2-digit', month: 'short', hour: '2-digit', minute: '2-digit' }).format(new Date(value))
}

const listingTitle = (listing = {}) => [listing.address, listing.district, listing.region].filter(Boolean).join(', ') || 'Kvartira'

export function Messages() {
  const navigate = useNavigate()
  const location = useLocation()
  const accessToken = useAuthStore((s) => s.accessToken)
  const userId = Number(useAuthStore((s) => s.userId))
  const [conversations, setConversations] = useState([])
  const [activeId, setActiveId] = useState(null)
  const [text, setText] = useState('')
  const [loading, setLoading] = useState(true)
  const [sending, setSending] = useState(false)
  const messagesEndRef = useRef(null)

  const requestedId = useMemo(() => new URLSearchParams(location.search).get('request'), [location.search])

  const load = async () => {
    setLoading(true)
    try {
      const data = await getRentalConversations()
      const list = Array.isArray(data) ? data : []
      setConversations(list)
      setActiveId((current) => requestedId || current || list[0]?.id || null)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    if (!accessToken) {
      navigate('/login')
      return
    }
    void load()
  }, [accessToken, navigate, requestedId])

  const active = conversations.find((item) => item.id === activeId) || conversations[0]
  const canDecide = active?.recipient?.id === userId && active?.status === 'pending'

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth', block: 'end' })
  }, [active?.id, active?.messages?.length])

  const handleSend = async () => {
    if (!active || !text.trim() || sending) return
    setSending(true)
    try {
      const message = await sendRentalRequestMessage(active.id, text.trim())
      setConversations((prev) => prev.map((item) => (
        item.id === active.id
          ? { ...item, messages: [...(item.messages || []), message], last_message: message }
          : item
      )))
      setText('')
    } finally {
      setSending(false)
    }
  }

  const decide = async (action) => {
    if (!active) return
    await (action === 'accept' ? acceptRentalRequest(active.id) : rejectRentalRequest(active.id))
    await load()
  }

  return (
    <main className="messages-page">
      <div className="messages-shell">
        <aside className="conversation-list">
          <div className="messages-title">
            <MessageCircle size={22} />
            <div>
              <h1>Messages</h1>
              <span>{conversations.length || 0} ta suhbat</span>
            </div>
          </div>
          {loading ? (
            <div className="conversation-skeletons">
              <span /><span /><span />
            </div>
          ) : conversations.length === 0 ? (
            <div className="conversation-empty">Hali chat yo'q.</div>
          ) : conversations.map((item) => (
            <button
              type="button"
              key={item.id}
              className={`conversation-item ${item.id === active?.id ? 'active' : ''}`}
              onClick={() => {
                setActiveId(item.id)
                navigate(`/messages?request=${item.id}`, { replace: true })
              }}
            >
              <span className="conversation-avatar">{item.other_user?.full_name?.charAt(0)?.toUpperCase() || 'U'}</span>
              <span className="conversation-copy">
                <strong>{item.other_user?.full_name || 'User'}</strong>
                <small>{item.last_message?.text || listingTitle(item.listing)}</small>
              </span>
              <span className={`conversation-status ${item.status}`}>{item.status}</span>
            </button>
          ))}
        </aside>

        <section className="chat-panel">
          {active ? (
            <>
              <div className="chat-header">
                <div>
                  <span className="chat-kicker"><Sparkles size={14} /> Smooth secure chat</span>
                  <h2>{active.other_user?.full_name}</h2>
                  <p><Home size={14} /> {listingTitle(active.listing)}</p>
                </div>
                <span className={`conversation-status ${active.status}`}>{active.status}</span>
              </div>

              {canDecide && (
                <div className="request-actions-strip">
                  <span>{active.requester?.full_name} bu kvartirani band qilmoqchi.</span>
                  <button type="button" onClick={() => decide('accept')}><CheckCircle2 size={17} /> Qabul qilish</button>
                  <button type="button" className="reject" onClick={() => decide('reject')}><XCircle size={17} /> Atkaz</button>
                </div>
              )}

              <div className="chat-messages">
                {(active.messages || []).length === 0 ? (
                  <div className="conversation-empty">Hali xabar yo'q.</div>
                ) : active.messages.map((message) => (
                  <div className={`chat-bubble ${Number(message.sender_id) === userId ? 'mine' : ''}`} key={message.id}>
                    <strong>{message.sender_name}</strong>
                    <span>{message.text}</span>
                    <small>{formatTime(message.created_at)}</small>
                  </div>
                ))}
                <div ref={messagesEndRef} />
              </div>

              <form className="chat-compose" onSubmit={(event) => { event.preventDefault(); void handleSend() }}>
                <input
                  value={text}
                  onChange={(event) => setText(event.target.value)}
                  disabled={sending}
                  placeholder="Xabar yozing..."
                />
                <button type="submit" disabled={!text.trim() || sending}>
                  <Send size={18} />
                </button>
              </form>
            </>
          ) : (
            <div className="chat-empty-state">
              <MessageCircle size={36} />
              <h2>Chat tanlang</h2>
              <p>Owner, broker yoki guest bilan yozishmalar shu yerda ochiladi.</p>
            </div>
          )}
        </section>
      </div>
    </main>
  )
}
