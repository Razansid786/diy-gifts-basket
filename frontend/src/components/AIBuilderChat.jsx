
import { useState, useRef, useEffect } from 'react'
import { apiClient } from '../api/client'
import { formatCurrency } from '../utils/format'

export function AIBuilderChat({
  isOpen,
  onClose,
  onAddProduct,
  onSelectBase,
  onRecommendations,
  context = {},
  initialMessage = null
}) {
  const { currentStep = 1, selectedBaseId = null, selectedProductIds = [] } = context
  
  const [messages, setMessages] = useState([
    {
      id: 'welcome',
      role: 'assistant',
      content: "Hello! I'm your AI Gift Guide. What's the occasion? I'll help you build something special step-by-step."
    }
  ])
  const [input, setInput] = useState('')
  const [isTyping, setIsTyping] = useState(false)
  const scrollRef = useRef(null)
  const hasSentInitial = useRef(false)
  const lastStepRef = useRef(currentStep)

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight
    }
  }, [messages, isTyping])

  // Handle initial message from redirect
  useEffect(() => {
    if (initialMessage && !hasSentInitial.current && isOpen) {
      hasSentInitial.current = true
      handleSend(null, initialMessage)
    }
  }, [initialMessage, isOpen])

  // Handle automatic step transitions
  useEffect(() => {
    if (currentStep !== lastStepRef.current && isOpen) {
      lastStepRef.current = currentStep
      const stepNames = {
        1: "Base Selection",
        2: "Product Selection",
        3: "Personalization",
        4: "Final Review"
      }
      handleSend(null, `I've moved to Step ${currentStep}: ${stepNames[currentStep]}. What should I do now?`)
    }
  }, [currentStep, isOpen])

  const handleSend = async (e, forcedMessage = null) => {
    if (e) e.preventDefault()
    const content = forcedMessage || input
    if (!content.trim() || isTyping) return

    // If it's a step change, we might want to hide the user message to keep it clean
    const isStepChange = forcedMessage && forcedMessage.includes("I've moved to Step")
    
    if (!isStepChange) {
      const userMsg = { id: Date.now().toString(), role: 'user', content }
      setMessages(prev => [...prev, userMsg])
    }
    
    setInput('')
    setIsTyping(true)

    try {
      const response = await apiClient.post('/ai/chat', { 
        message: content,
        current_step: currentStep,
        selected_base_id: selectedBaseId,
        selected_product_ids: selectedProductIds
      })
      
      const botMsg = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: response.reply,
        recommendations: response.recommendations,
        suggestedStep: response.suggested_step
      }
      setMessages(prev => [...prev, botMsg])
      if (response.recommendations?.length && onRecommendations) {
        onRecommendations(response.recommendations.map(r => r.id))
      }
    } catch (error) {
      // Only show error for real user messages
      if (!isStepChange) {
        setMessages(prev => [...prev, {
          id: 'error',
          role: 'assistant',
          content: "I'm having a little trouble thinking. Could you try that again?"
        }])
      }
    } finally {
      setIsTyping(false)
    }
  }

  return (
    <div className={`ai-builder-chat`}>
      <header className="ai-chat-header">
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.8rem' }}>
          <span style={{ fontSize: '1.4rem' }}>✨</span>
          <div>
            <h3 style={{ margin: 0, fontSize: '1.05rem', fontWeight: 700 }}>AI Assistant</h3>
            <div style={{ fontSize: '0.75rem', opacity: 0.7, display: 'flex', alignItems: 'center', gap: '0.3rem' }}>
              <span className="pulse-dot"></span> Online Guide
            </div>
          </div>
        </div>
        <button type="button" className="ghost-button" onClick={onClose} style={{ fontSize: '1.5rem', padding: '0.5rem' }}>&times;</button>
      </header>

      <div className="ai-chat-messages" ref={scrollRef}>
        {messages.map(m => (
          <div key={m.id} className={`ai-message ${m.role}`}>
            <div className="message-content">{m.content}</div>
            {m.recommendations && m.recommendations.length > 0 && (
              <div className="ai-recommendations" style={{ marginTop: '0.8rem', display: 'flex', flexDirection: 'column', gap: '0.6rem' }}>
                {m.recommendations.map(p => {
                  const isBase = p.id.startsWith('box-') || p.id.startsWith('basket-')
                  return (
                    <div key={p.id} className="ai-recommendation-card" style={{ 
                      padding: '0.6rem', 
                      background: 'rgba(255,255,255,0.04)', 
                      borderRadius: '8px',
                      border: '1px solid rgba(255,255,255,0.08)'
                    }}>
                      <div style={{ display: 'flex', gap: '0.8rem', alignItems: 'center' }}>
                        <img 
                          src={p.imageUrl || p.image_url} 
                          alt={p.title || p.name} 
                          style={{ width: '40px', height: '40px', objectFit: 'contain', borderRadius: '4px' }} 
                        />
                        <div style={{ flex: 1, minWidth: 0 }}>
                          <div style={{ fontSize: '0.8rem', fontWeight: 600, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                            {p.title || p.name}
                          </div>
                          <div style={{ fontSize: '0.75rem', opacity: 0.8 }}>{formatCurrency(p.price)}</div>
                        </div>
                        <button 
                          type="button" 
                          className="button" 
                          style={{ fontSize: '0.65rem', padding: '0.3rem 0.6rem', height: 'auto' }}
                          onClick={() => isBase ? onSelectBase?.(p) : onAddProduct?.(p)}
                        >
                          {isBase ? 'Select' : 'Add'}
                        </button>
                      </div>
                    </div>
                  )
                })}
              </div>
            )}
          </div>
        ))}
        {isTyping && (
          <div className="ai-message assistant">
            <div className="typing-indicator">
              <span></span><span></span><span></span>
            </div>
          </div>
        )}
      </div>

      <form className="ai-chat-input-wrap" onSubmit={handleSend}>
        <div className="ai-chat-input-group">
          <input
            type="text"
            placeholder="Ask me anything..."
            value={input}
            onChange={e => setInput(e.target.value)}
            disabled={isTyping}
          />
          <button type="submit" className="button" disabled={isTyping || !input.trim()}>
            Send
          </button>
        </div>
      </form>
    </div>
  )
}
