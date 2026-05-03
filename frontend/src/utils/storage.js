const TOKEN_KEY = 'diy_gifts_access_token'
const SESSION_KEY = 'diy_gifts_guest_session'

export function getStoredToken() {
  return window.localStorage.getItem(TOKEN_KEY)
}

export function setStoredToken(token) {
  if (token) {
    window.localStorage.setItem(TOKEN_KEY, token)
    return
  }
  window.localStorage.removeItem(TOKEN_KEY)
}

export function getStoredSessionId() {
  return window.localStorage.getItem(SESSION_KEY)
}

export function setStoredSessionId(sessionId) {
  if (sessionId) {
    window.localStorage.setItem(SESSION_KEY, sessionId)
    return
  }
  window.localStorage.removeItem(SESSION_KEY)
}