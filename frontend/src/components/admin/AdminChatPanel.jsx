import { useState, useEffect, useRef } from 'react'
import { apiClient } from '../../api/client'
import { useAppContext } from '../../context/AppContext'
import { useChat } from '../../context/ChatContext'

export function AdminChatPanel() {
  const { token } = useAppContext()
  const { adminMessages, setAdminMessages, sendMessage } = useChat()
  const [rooms, setRooms] = useState([])
  const [activeRoomId, setActiveRoomId] = useState(null)
  const [input, setInput] = useState('')
  const messagesEndRef = useRef(null)

  useEffect(() => {
    if (token) {
      apiClient.getAdminRooms(token).then(setRooms).catch(console.error)
    }
  }, [token, adminMessages])

  useEffect(() => {
    if (activeRoomId && token && !adminMessages[activeRoomId]) {
      apiClient.getAdminRoomMessages(activeRoomId, token).then(msgs => {
        setAdminMessages(prev => ({ ...prev, [activeRoomId]: msgs }))
      }).catch(console.error)
    }

    if (activeRoomId && token) {

      apiClient.markAdminChatRead(activeRoomId, token).catch(console.error)

      setAdminMessages(prev => {
        const msgs = prev[activeRoomId] || []
        if (msgs.some(m => !m.is_admin && !m.is_read)) {
          return {
            ...prev,
            [activeRoomId]: msgs.map(m => (!m.is_admin ? { ...m, is_read: true } : m))
          }
        }
        return prev
      })
    }
  }, [activeRoomId, token, adminMessages, setAdminMessages])

  useEffect(() => {
    if (messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior: 'smooth' })
    }
  }, [adminMessages, activeRoomId])

  const handleSend = (e) => {
    e.preventDefault()
    if (!input.trim() || !activeRoomId) return
    sendMessage(input.trim(), activeRoomId)
    setInput('')
  }

  const activeMessages = activeRoomId ? (adminMessages[activeRoomId] || []) : []

  return (
    <div style={{ display: 'grid', gridTemplateColumns: '300px 1fr', gap: '1rem', height: '600px' }}>
      <div className="panel" style={{ overflowY: 'auto', padding: '1rem' }}>
        <h3>Active Chats</h3>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem', marginTop: '1rem' }}>
          {rooms.length === 0 ? <p style={{ color: 'var(--ink-muted)' }}>No active chats.</p> : null}
          {rooms.map(room => {
            const msgs = adminMessages[room.id] || []
            const hasUnread = msgs.some(m => !m.is_admin && !m.is_read)
            return (
              <button
                key={room.id}
                onClick={() => setActiveRoomId(room.id)}
                style={{
                  padding: '1rem',
                  background: activeRoomId === room.id ? 'rgba(255,255,255,0.1)' : 'transparent',
                  border: '1px solid var(--border-color)',
                  borderRadius: '8px',
                  textAlign: 'left',
                  cursor: 'pointer',
                  color: '#fff',
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center'
                }}
              >
                <div>
                  <strong>{room.user_name || 'Customer'}</strong>
                  <p style={{ margin: '0.2rem 0 0', fontSize: '0.8rem', color: 'var(--ink-muted)' }}>{room.user_email}</p>
                </div>
                {hasUnread && <div style={{ width: '10px', height: '10px', borderRadius: '50%', background: 'var(--brand-coral)' }} title="Unread messages" />}
              </button>
            )
          })}
        </div>
      </div>

      <div className="panel" style={{ display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
        {activeRoomId ? (
          <>
            <div style={{ padding: '1rem', borderBottom: '1px solid var(--border-color)', background: 'rgba(0,0,0,0.2)' }}>
              <h3 style={{ margin: 0 }}>{rooms.find(r => r.id === activeRoomId)?.user_name || 'Customer'}</h3>
            </div>

            <div style={{ flex: 1, overflowY: 'auto', padding: '1.5rem', display: 'flex', flexDirection: 'column', gap: '1rem' }}>
              {activeMessages.length === 0 ? (
                <p style={{ textAlign: 'center', color: 'var(--ink-muted)' }}>No messages yet.</p>
              ) : (
                activeMessages.map(msg => (
                  <div
                    key={msg.id}
                    style={{
                      maxWidth: '70%',
                      padding: '0.8rem 1rem',
                      borderRadius: '12px',
                      alignSelf: msg.is_admin ? 'flex-end' : 'flex-start',
                      background: msg.is_admin ? 'rgba(45, 192, 175, 0.2)' : 'rgba(255,255,255,0.1)',
                      color: msg.is_admin ? 'var(--brand-teal)' : '#fff',
                      borderBottomRightRadius: msg.is_admin ? 0 : '12px',
                      borderBottomLeftRadius: msg.is_admin ? '12px' : 0
                    }}
                  >
                    {msg.content}
                  </div>
                ))
              )}
              <div ref={messagesEndRef} />
            </div>

            <form onSubmit={handleSend} style={{ display: 'flex', gap: '0.5rem', padding: '1rem', borderTop: '1px solid var(--border-color)' }}>
              <input
                type="text"
                placeholder="Type a reply..."
                value={input}
                onChange={(e) => setInput(e.target.value)}
                style={{ flex: 1, padding: '0.8rem', borderRadius: '8px', border: '1px solid var(--border-color)', background: 'rgba(0,0,0,0.2)', color: '#fff' }}
              />
              <button type="submit" disabled={!input.trim()} className="button">Reply</button>
            </form>
          </>
        ) : (
          <div style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--ink-muted)' }}>
            <p>Select a chat from the sidebar to view messages.</p>
          </div>
        )}
      </div>
    </div>
  )
}