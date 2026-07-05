import './MyRoom.scss'
import { useEffect, useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  AlertTriangle,
  CalendarDays,
  Home,
  MessageCircle,
  Megaphone,
  Send,
  Users,
  Wallet,
} from 'lucide-react'
import {
  createMaintenanceReport,
  getMyRentalRequests,
  getMyRooms,
  getRoomMessages,
  repostVacancy,
  sendRoomMessage,
} from '../../../services/listingService'
import { useAuthStore } from '../../../store/authStore'

const formatDate = (value) => {
  if (!value) return '-'
  return new Intl.DateTimeFormat('uz-UZ', { day: '2-digit', month: 'short', year: 'numeric' }).format(new Date(value))
}

export function MyRoom() {
  const navigate = useNavigate()
  const accessToken = useAuthStore((s) => s.accessToken)
  const userId = Number(useAuthStore((s) => s.userId))
  const [rooms, setRooms] = useState([])
  const [requests, setRequests] = useState([])
  const [activeRoomId, setActiveRoomId] = useState(null)
  const [messages, setMessages] = useState([])
  const [chatText, setChatText] = useState('')
  const [issueText, setIssueText] = useState('')
  const [issueImage, setIssueImage] = useState('')
  const [vacancySpaces, setVacancySpaces] = useState(1)
  const [notice, setNotice] = useState('')
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const load = async () => {
      try {
        setLoading(true)
        const [roomData, requestData] = await Promise.all([getMyRooms(), getMyRentalRequests()])
        setRooms(Array.isArray(roomData) ? roomData : [])
        setRequests(Array.isArray(requestData) ? requestData : [])
        setActiveRoomId(roomData?.[0]?.id || null)
      } finally {
        setLoading(false)
      }
    }

    if (!accessToken) {
      navigate('/login')
      return
    }
    void load()
  }, [accessToken, navigate])

  useEffect(() => {
    if (!activeRoomId) {
      setMessages([])
      return
    }
    void getRoomMessages(activeRoomId).then((data) => setMessages(Array.isArray(data) ? data : []))
  }, [activeRoomId])

  const activeRoom = useMemo(
    () => rooms.find((room) => room.id === activeRoomId) || rooms[0],
    [activeRoomId, rooms],
  )

  const sendMessage = async () => {
    if (!activeRoom || !chatText.trim()) return
    const message = await sendRoomMessage(activeRoom.id, chatText.trim())
    setMessages((prev) => [...prev, message])
    setChatText('')
  }

  const sendIssue = async () => {
    if (!activeRoom || !issueText.trim()) return
    await createMaintenanceReport(activeRoom.id, { text: issueText.trim(), image_url: issueImage || null })
    setNotice('Muammo xabari egasi yoki brokerga yuborildi.')
    setIssueText('')
    setIssueImage('')
  }

  const createVacancy = async () => {
    if (!activeRoom) return
    const response = await repostVacancy(activeRoom.id, {
      available_spaces: Number(vacancySpaces),
      description: `${activeRoom.listing.address || activeRoom.listing.district} kvartirasida ${vacancySpaces} ta bo'sh joy bor.`,
    })
    setNotice(response.message || 'Reklama joylandi.')
  }

  if (loading) {
    return (
      <main className="my-room-page">
        <div className="my-room-shell">
          <div className="room-empty">My Room yuklanmoqda...</div>
        </div>
      </main>
    )
  }

  return (
    <main className="my-room-page">
      <div className="my-room-shell">
        <section className="room-header">
          <div>
            <p>Mening joyim</p>
            <h1>My Room</h1>
            <span>Band qilingan kvartira, qo'shnilar, chat va to'lov eslatmalari shu yerda.</span>
          </div>
          <div className="room-header__stat">
            <strong>{rooms.length}</strong>
            <small>faol xona</small>
          </div>
        </section>

        {notice && <div className="room-notice">{notice}</div>}

        <section className="room-grid">
          <aside className="room-panel">
            <div className="room-panel__head">
              <h2>Kvartiralarim</h2>
              <Home size={20} />
            </div>
            {rooms.length === 0 ? (
              <div className="room-empty">Hali qabul qilingan xona yo'q. So'rov qabul qilinsa, shu yerda chiqadi.</div>
            ) : (
              <div className="room-list">
                {rooms.map((room) => (
                  <button
                    type="button"
                    className={room.id === activeRoom?.id ? 'active' : ''}
                    key={room.id}
                    onClick={() => setActiveRoomId(room.id)}
                  >
                    <strong>{room.listing.address || `${room.listing.district}, ${room.listing.region}`}</strong>
                    <span>${room.price_usd}/oy</span>
                  </button>
                ))}
              </div>
            )}

            <div className="request-list">
              <h3>So'rovlarim</h3>
              {requests.slice(0, 3).map((request) => (
                <div className="request-row" key={request.id}>
                  <span>{request.listing.address || request.listing.district}</span>
                  <strong>{request.status}</strong>
                </div>
              ))}
            </div>
          </aside>

          <section className="room-panel room-panel--main">
            {activeRoom ? (
              <>
                <div className="current-room">
                  <div>
                    <p>{activeRoom.listing.district}, {activeRoom.listing.region}</p>
                    <h2>{activeRoom.listing.address || 'Manzil kiritilmagan'}</h2>
                    <span>Egasi/broker: {activeRoom.owner.full_name} · {activeRoom.owner.phone}</span>
                  </div>
                  <div className="payment-card">
                    <Wallet size={20} />
                    <strong>{activeRoom.payment_days_left} kun qoldi</strong>
                    <span>Keyingi to'lov: {formatDate(activeRoom.next_payment_date)}</span>
                  </div>
                </div>

                <div className="room-facts">
                  <span><CalendarDays size={16} /> Boshlangan: {formatDate(activeRoom.start_date)}</span>
                  <span><Users size={16} /> Qo'shnilar: {activeRoom.neighbors.length}</span>
                  <span><Home size={16} /> Bo'sh joy: {activeRoom.listing.available_spaces}</span>
                </div>

                <div className="neighbors">
                  <h3>Mening qo'shnilarim</h3>
                  {activeRoom.neighbors.length === 0 ? (
                    <p>Hozircha boshqa ijarachi ko'rinmayapti.</p>
                  ) : (
                    activeRoom.neighbors.map((neighbor) => (
                      <span key={neighbor.id}>{neighbor.full_name} · {neighbor.phone}</span>
                    ))
                  )}
                </div>

                <div className="room-chat">
                  <div className="room-chat__head">
                    <h3>Guruh chat</h3>
                    <MessageCircle size={18} />
                  </div>
                  <div className="room-chat__messages">
                    {messages.length === 0 ? (
                      <p>Hali xabar yo'q.</p>
                    ) : (
                      messages.map((message) => (
                        <div className={message.sender_id === userId ? 'mine' : ''} key={message.id}>
                          <strong>{message.sender_name}</strong>
                          <span>{message.text}</span>
                        </div>
                      ))
                    )}
                  </div>
                  <div className="room-chat__send">
                    <input value={chatText} onChange={(event) => setChatText(event.target.value)} placeholder="Xabar yozing..." />
                    <button type="button" onClick={sendMessage}><Send size={17} /></button>
                  </div>
                </div>
              </>
            ) : (
              <div className="room-empty">Kvartira tanlanmagan.</div>
            )}
          </section>

          <aside className="room-panel">
            <div className="room-panel__head">
              <h2>Muammo</h2>
              <AlertTriangle size={20} />
            </div>
            <textarea value={issueText} onChange={(event) => setIssueText(event.target.value)} placeholder="Masalan: suv oqyapti, eshik buzilgan..." rows={4} />
            <input value={issueImage} onChange={(event) => setIssueImage(event.target.value)} placeholder="Rasm URL (ixtiyoriy)" />
            <button type="button" className="room-primary" onClick={sendIssue} disabled={!activeRoom}>Yuborish</button>

            <div className="vacancy-box">
              <Megaphone size={20} />
              <h3>Bo'sh joy reklamasi</h3>
              <p>1 yoki 2 ta joy bo'shasa, birinchi martasiga bepul e'lon qiling.</p>
              <select value={vacancySpaces} onChange={(event) => setVacancySpaces(event.target.value)}>
                <option value={1}>1 ta joy</option>
                <option value={2}>2 ta joy</option>
              </select>
              <button type="button" className="room-secondary" onClick={createVacancy} disabled={!activeRoom}>Reklamaga qo'yish</button>
            </div>
          </aside>
        </section>
      </div>
    </main>
  )
}
