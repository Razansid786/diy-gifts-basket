import { createContext, useContext, useEffect, useState, useCallback } from 'react'
import { useAppContext } from './AppContext'

const ChatContext = createContext(null)

export function ChatProvider({ children }) {
  const { user, token } = useAppContext()
  const [ws, setWs] = useState(null)

  const [userMessages, setUserMessages] = useState([])
  const [hasUnread, setHasUnread] = useState(false)

  const [adminMessages, setAdminMessages] = useState({})

  const connectWs = useCallback(() => {
    if (!token || !user) return

    const apiBaseUrl = (import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1').replace(/\/$/, '')
    const wsUrl = apiBaseUrl.replace('http', 'ws') + `/chat/ws?token=${token}`

    let socket = null
    try {
        socket = new WebSocket(wsUrl)
    } catch (e) {
        console.error("Failed to connect WS", e)
        return
    }

    socket.onopen = () => {
      console.log('Chat connected')
    }

    socket.onmessage = (event) => {
      try {
        const msg = JSON.parse(event.data)

        if (user.role === 'admin') {
          setAdminMessages(prev => {
            const roomMsgs = prev[msg.room_id] || []
            if (roomMsgs.find(m => m.id === msg.id)) return prev
            return {
              ...prev,
              [msg.room_id]: [...roomMsgs, msg]
            }
          })
        } else {
          setUserMessages(prev => {
            if (prev.find(m => m.id === msg.id)) return prev
            if (msg.is_admin && !msg.is_read) {
              setHasUnread(true)
            }
            return [...prev, msg]
          })
        }
      } catch (err) {
        console.error("WS Message Error", err)
      }
    }

    socket.onclose = () => {

      setTimeout(connectWs, 3000)
    }

    setWs(socket)

    return () => {
      socket.onclose = null
      socket.close()
    }
  }, [token, user])

  useEffect(() => {
    const cleanup = connectWs()
    return () => {
      if (cleanup) cleanup()
    }
  }, [connectWs])

  const sendMessage = useCallback((content, roomId = null) => {
    if (ws && ws.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify({ content, room_id: roomId }))
    }
  }, [ws])

  return (
    <ChatContext.Provider value={{
      userMessages,
      setUserMessages,
      adminMessages,
      setAdminMessages,
      hasUnread,
      setHasUnread,
      sendMessage,
    }}>
      {children}
    </ChatContext.Provider>
  )
}

export const useChat = () => useContext(ChatContext)