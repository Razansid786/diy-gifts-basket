import { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react'

import { apiClient } from '../api/client'
import {
  getStoredSessionId,
  getStoredToken,
  setStoredSessionId,
  setStoredToken,
} from '../utils/storage'

const AppContext = createContext(null)

function createToast(message, type = 'info') {
  return {
    id: crypto.randomUUID(),
    message,
    type,
  }
}

export function AppProvider({ children }) {
  const [token, setTokenState] = useState(() => getStoredToken())
  const [sessionId, setSessionIdState] = useState(() => getStoredSessionId())
  const [user, setUser] = useState(null)
  const [isAuthLoading, setIsAuthLoading] = useState(true)
  const [cart, setCart] = useState(null)
  const [toasts, setToasts] = useState([])

  const pushToast = useCallback((message, type = 'info') => {
    const toast = createToast(message, type)
    setToasts((current) => [...current, toast])

    window.setTimeout(() => {
      setToasts((current) => current.filter((item) => item.id !== toast.id))
    }, 4200)
  }, [])

  const dismissToast = useCallback((toastId) => {
    setToasts((current) => current.filter((item) => item.id !== toastId))
  }, [])

  const setToken = useCallback((nextToken) => {
    setStoredToken(nextToken)
    setTokenState(nextToken || null)
  }, [])

  const setSessionId = useCallback((nextSessionId) => {
    setStoredSessionId(nextSessionId)
    setSessionIdState(nextSessionId || null)
  }, [])

  const ensureGuestSession = useCallback(async () => {
    if (sessionId) {
      return sessionId
    }

    const payload = await apiClient.createGuestSession()
    setSessionId(payload.session_id)
    return payload.session_id
  }, [sessionId, setSessionId])

  const refreshUser = useCallback(async () => {
    if (!token) {
      setUser(null)
      setIsAuthLoading(false)
      return null
    }

    try {
      const profile = await apiClient.getMe(token)
      setUser(profile)
      return profile
    } catch (error) {
      setToken(null)
      setUser(null)
      pushToast(error.message || 'Your session expired. Please log in again.', 'error')
      return null
    } finally {
      setIsAuthLoading(false)
    }
  }, [token, setToken, pushToast])

  const refreshCart = useCallback(async () => {
    try {
      const latestCart = await apiClient.getCart({ token, sessionId })
      setCart(latestCart)
      return latestCart
    } catch (error) {
      pushToast(error.message || 'Unable to refresh cart.', 'error')
      return null
    }
  }, [token, sessionId, pushToast])

  const logout = useCallback(() => {
    setToken(null)
    setUser(null)
    pushToast('You have been logged out.', 'info')
  }, [setToken, pushToast])

  useEffect(() => {
    ensureGuestSession().catch((error) => {
      pushToast(error.message || 'Failed to initialize guest session.', 'error')
    })
  }, [ensureGuestSession, pushToast])

  useEffect(() => {
    const handleAuthExpired = () => {
      setToken(null)
      setUser(null)
      pushToast('Your session has expired. Please sign in again.', 'error')
      if (window.location.pathname !== '/auth') {
        window.location.href = '/auth?mode=login'
      }
    }

    window.addEventListener('auth:expired', handleAuthExpired)
    return () => window.removeEventListener('auth:expired', handleAuthExpired)
  }, [setToken, pushToast])

  useEffect(() => {
    refreshUser()
  }, [refreshUser])

  useEffect(() => {
    if (!sessionId && !token) {
      return
    }
    refreshCart()
  }, [sessionId, token, refreshCart])

  const value = useMemo(
    () => ({
      token,
      sessionId,
      user,
      cart,
      toasts,
      isAuthLoading,
      pushToast,
      dismissToast,
      setToken,
      setSessionId,
      ensureGuestSession,
      refreshUser,
      refreshCart,
      logout,
      authMeta: {
        token,
        sessionId,
      },
    }),
    [
      token,
      sessionId,
      user,
      cart,
      toasts,
      isAuthLoading,
      pushToast,
      dismissToast,
      setToken,
      setSessionId,
      ensureGuestSession,
      refreshUser,
      refreshCart,
      logout,
    ],
  )

  return <AppContext.Provider value={value}>{children}</AppContext.Provider>
}

export function useAppContext() {
  const context = useContext(AppContext)
  if (!context) {
    throw new Error('useAppContext must be used inside AppProvider')
  }
  return context
}