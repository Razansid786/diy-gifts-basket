import { useState, useEffect, useRef } from 'react'
import { useAppContext } from '../context/AppContext'
import { useChat } from '../context/ChatContext'
import { apiClient } from '../api/client'

export function ChatWidget() {
  const { user, token } = useAppContext()
  const { userMessages, setUserMessages, hasUnread, setHasUnread, sendMessage } = useChat()
  const [isOpen, setIsOpen] = useState(false)
  const [input, setInput] = useState('')
  const [isLoaded, setIsLoaded] = useState(false)
  const messagesEndRef = useRef(null)

  useEffect(() => {
    if (isOpen && messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior: 'smooth' })
    }
  }, [userMessages, isOpen])

  useEffect(() => {
    if (isOpen && !isLoaded && token) {
      apiClient.getChatHistory(token).then((history) => {
        setUserMessages(history)
        setIsLoaded(true)
        if (hasUnread) {
          apiClient.markChatRead(token).catch(console.error)
          setHasUnread(false)
        }
      }).catch(console.error)
    }
    if (isOpen && hasUnread && token) {
      apiClient.markChatRead(token).catch(console.error)
      setHasUnread(false)
    }
  }, [isOpen, isLoaded, token, hasUnread, setUserMessages, setHasUnread])

  if (!user || user.role === 'admin') return null

  const handleSend = (e) => {
    e.preventDefault()
    if (!input.trim()) return
    sendMessage(input.trim())
    setInput('')
  }

  return (
    <>
      {isOpen && (
        <div className="chat-widget-window">
          <div className="chat-header">
            <h3>Support Chat</h3>
            <button className="close-btn" onClick={() => setIsOpen(false)}>&times;</button>
          </div>
          <div className="chat-messages">
            {userMessages.length === 0 ? (
              <p className="chat-empty">How can we help you today?</p>
            ) : (
              userMessages.map((msg) => (
                <div key={msg.id} className={`chat-bubble ${msg.is_admin ? 'admin' : 'user'}`}>
                  {msg.content}
                </div>
              ))
            )}
            <div ref={messagesEndRef} />
          </div>
          <form className="chat-input-area" onSubmit={handleSend}>
            <input
              type="text"
              placeholder="Type a message..."
              value={input}
              onChange={(e) => setInput(e.target.value)}
            />
            <button type="submit" disabled={!input.trim()}>Send</button>
          </form>
        </div>
      )}

      <button
        className={`chat-widget-fab ${hasUnread && !isOpen ? 'has-unread' : ''}`}
        onClick={() => setIsOpen(!isOpen)}
        aria-label="Chat with support"
      >
        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path>
        </svg>
      </button>

      <style>{`
        .chat-widget-fab {
          position: fixed;
          bottom: 2rem;
          right: 2rem;
          width: 60px;
          height: 60px;
          border-radius: 50%;
          background: linear-gradient(135deg, var(--brand-teal), var(--brand-amber));
          color: #000;
          border: none;
          display: grid;
          place-items: center;
          cursor: pointer;
          box-shadow: 0 4px 15px rgba(0,0,0,0.3);
          z-index: 9999;
          transition: transform 0.2s ease;
        }
        .chat-widget-fab:hover { transform: scale(1.05); }
        .chat-widget-fab.has-unread::after {
          content: ''; position: absolute; top: 0; right: 0; width: 14px; height: 14px;
          background: var(--brand-coral); border-radius: 50%; border: 2px solid #000;
        }
        .chat-widget-window {
          position: fixed; bottom: 6rem; right: 2rem; width: 350px; height: 500px;
          background: rgba(18, 23, 34, 0.98); border: 1px solid var(--line);
          border-radius: 12px; display: flex; flex-direction: column; z-index: 9998;
          box-shadow: 0 10px 30px rgba(0,0,0,0.5); overflow: hidden; backdrop-filter: blur(10px);
        }
        .chat-header {
          background: rgba(0,0,0,0.3); padding: 1rem; display: flex; justify-content: space-between;
          align-items: center; border-bottom: 1px solid var(--border-color);
        }
        .chat-header h3 { margin: 0; font-size: 1.1rem; }
        .close-btn { background: none; border: none; color: #fff; font-size: 1.5rem; cursor: pointer; }
        .chat-messages {
          flex: 1; padding: 1rem; overflow-y: auto; display: flex; flex-direction: column; gap: 0.8rem;
        }
        .chat-empty { text-align: center; color: var(--ink-muted); margin-top: 2rem; }
        .chat-bubble { max-width: 80%; padding: 0.8rem 1rem; border-radius: 12px; font-size: 0.95rem; word-wrap: break-word; }
        .chat-bubble.admin { align-self: flex-start; background: rgba(255,255,255,0.1); border-bottom-left-radius: 0; }
        .chat-bubble.user { align-self: flex-end; background: rgba(45, 192, 175, 0.2); color: var(--brand-teal); border-bottom-right-radius: 0; }
        .chat-input-area { display: flex; padding: 1rem; gap: 0.5rem; border-top: 1px solid var(--border-color); background: rgba(0,0,0,0.2); }
        .chat-input-area input { flex: 1; padding: 0.8rem; border-radius: 8px; border: 1px solid rgba(255,255,255,0.1); background: rgba(0,0,0,0.3); color: #fff; }
        .chat-input-area button { background: var(--brand-teal); color: #000; border: none; border-radius: 8px; padding: 0 1rem; cursor: pointer; font-weight: bold; }
        .chat-input-area button:disabled { opacity: 0.5; cursor: not-allowed; }
      `}</style>
    </>
  )
}