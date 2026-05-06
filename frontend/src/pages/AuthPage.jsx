import { useMemo, useState } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'

import { apiClient } from '../api/client'
import { PageHeader } from '../components/PageHeader'
import { useAppContext } from '../context/AppContext'

const LOGIN_DEFAULTS = {
  email: '',
  password: '',
}

const REGISTER_DEFAULTS = {
  full_name: '',
  email: '',
  phone_number: '',
  password: '',
  confirm_password: '',
}

export function AuthPage() {
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const { setToken, refreshUser, pushToast, token, user } = useAppContext()

  const redirectTo = searchParams.get('redirectTo') || '/builder'
  const intent = searchParams.get('intent') || ''
  const defaultMode = searchParams.get('mode') === 'register' ? 'register' : 'login'

  const [mode, setMode] = useState(defaultMode)
  const [loginForm, setLoginForm] = useState(LOGIN_DEFAULTS)
  const [registerForm, setRegisterForm] = useState(REGISTER_DEFAULTS)
  const [forgotEmail, setForgotEmail] = useState('')
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [isForgotPassword, setIsForgotPassword] = useState(false)

  const isLoggedIn = useMemo(() => Boolean(token && user), [token, user])

  const handleLogin = async (event) => {
    event.preventDefault()
    setIsSubmitting(true)

    try {
      const data = await apiClient.login(loginForm)
      setToken(data.access_token)
      await refreshUser()
      if (intent === 'checkout') {
        pushToast('Signed in. You can now complete checkout.', 'success')
      } else {
        pushToast('Signed in successfully.', 'success')
      }
      navigate(redirectTo)
    } catch (error) {
      pushToast(error.message || 'Unable to sign in.', 'error')
    } finally {
      setIsSubmitting(false)
    }
  }

  const handleRegister = async (event) => {
    event.preventDefault()

    if (registerForm.password !== registerForm.confirm_password) {
      pushToast('Passwords do not match.', 'error')
      return
    }

    setIsSubmitting(true)

    try {
      const payload = {
        full_name: registerForm.full_name,
        email: registerForm.email,
        phone_number: registerForm.phone_number,
        password: registerForm.password,
      }

      const data = await apiClient.register(payload)
      setToken(data.access_token)
      await refreshUser()
      if (intent === 'checkout') {
        pushToast('Account created. You can now complete checkout.', 'success')
      } else {
        pushToast('Account created successfully.', 'success')
      }
      navigate(redirectTo)
    } catch (error) {
      pushToast(error.message || 'Unable to create account.', 'error')
    } finally {
      setIsSubmitting(false)
    }
  }

  const handleForgotPassword = async (event) => {
    event.preventDefault()
    setIsSubmitting(true)

    try {
      await apiClient.forgotPassword({ email: forgotEmail })
      pushToast('If this email is registered, a reset link will be sent.', 'success')
      setIsForgotPassword(false)
    } catch (error) {
      pushToast(error.message || 'Unable to request password reset.', 'error')
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <main className="page page-auth">
      <PageHeader
        eyebrow="Customer Portal"
        title={mode === 'login' ? 'Welcome back' : 'Create an account'}
        subtitle={mode === 'login' ? 'Sign in to access your saved baskets and track orders.' : 'Join DIY Gift Basket to save addresses and track your orders.'}
      />

      {isLoggedIn ? (
        <section className="panel auth-panel" style={{ textAlign: 'center', padding: '3rem 2rem' }}>
          <div style={{ background: 'rgba(45, 192, 175, 0.1)', width: '64px', height: '64px', borderRadius: '50%', margin: '0 auto 1rem', display: 'grid', placeItems: 'center', color: 'var(--brand-teal)' }}>
            <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M20 6L9 17l-5-5"/></svg>
          </div>
          <h2>You are signed in</h2>
          <p style={{ color: 'var(--ink-muted)', marginBottom: '2rem' }}>You are currently signed in as <strong>{user.email}</strong>.</p>
          <button type="button" className="button" onClick={() => navigate(redirectTo)}>
            Continue to site
          </button>
        </section>
      ) : (
        <section className="panel auth-panel" style={{ maxWidth: '480px', margin: '0 auto', border: '1px solid var(--line)' }}>
          <div className="auth-tabs" role="tablist" aria-label="Auth mode selector" style={{ width: '100%', display: 'flex' }}>
            <button
              type="button"
              className={mode === 'login' ? 'active' : ''}
              style={{ flex: 1, borderRadius: '999px 0 0 999px' }}
              onClick={() => setMode('login')}
            >
              Sign In
            </button>
            <button
              type="button"
              className={mode === 'register' ? 'active' : ''}
              style={{ flex: 1, borderRadius: '0 999px 999px 0' }}
              onClick={() => setMode('register')}
            >
              Register
            </button>
          </div>

          {mode === 'login' ? (
            isForgotPassword ? (
              <form className="auth-form" onSubmit={handleForgotPassword} style={{ marginTop: '1.5rem' }}>
                <p style={{ fontSize: '0.9rem', color: 'var(--ink-muted)', marginBottom: '1.5rem' }}>
                  Enter your email address and we'll send you a link to reset your password.
                </p>
                <label>
                  Email Address
                  <input
                    type="email"
                    required
                    placeholder="ali@example.com"
                    value={forgotEmail}
                    onChange={(event) => setForgotEmail(event.target.value)}
                  />
                </label>

                <button type="submit" className="button" disabled={isSubmitting} style={{ marginTop: '1rem', padding: '0.8rem' }}>
                  {isSubmitting ? 'Sending link...' : 'Send Reset Link'}
                </button>

                <button
                  type="button"
                  className="ghost-button"
                  style={{ width: '100%', marginTop: '0.5rem' }}
                  onClick={() => setIsForgotPassword(false)}
                >
                  Back to Sign In
                </button>
              </form>
            ) : (
              <form className="auth-form" onSubmit={handleLogin} style={{ marginTop: '1.5rem' }}>
                <label>
                  Email Address
                  <input
                    type="email"
                    required
                    placeholder="ali@example.com"
                    value={loginForm.email}
                    onChange={(event) =>
                      setLoginForm((current) => ({ ...current, email: event.target.value }))
                    }
                  />
                </label>

                <label>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    Password
                    <button
                      type="button"
                      className="ghost-button"
                      style={{ fontSize: '0.8rem', padding: 0, height: 'auto', fontWeight: 500 }}
                      onClick={() => setIsForgotPassword(true)}
                    >
                      Forgot Password?
                    </button>
                  </div>
                  <input
                    type="password"
                    required
                    placeholder="••••••••"
                    minLength={8}
                    value={loginForm.password}
                    onChange={(event) =>
                      setLoginForm((current) => ({ ...current, password: event.target.value }))
                    }
                  />
                </label>

                <button type="submit" className="button" disabled={isSubmitting} style={{ marginTop: '1rem', padding: '0.8rem' }}>
                  {isSubmitting ? 'Signing in...' : 'Sign In'}
                </button>
              </form>
            )
          ) : (
            <form className="auth-form" onSubmit={handleRegister} style={{ marginTop: '1.5rem' }}>
              <label>
                Full Name
                <input
                  type="text"
                  required
                  placeholder="Muhammad Ali"
                  value={registerForm.full_name}
                  onChange={(event) =>
                    setRegisterForm((current) => ({ ...current, full_name: event.target.value }))
                  }
                />
              </label>

              <div className="inline-grid" style={{ gridTemplateColumns: '1fr 1fr' }}>
                <label>
                  Email Address
                  <input
                    type="email"
                    required
                    placeholder="ali@example.com"
                    value={registerForm.email}
                    onChange={(event) =>
                      setRegisterForm((current) => ({ ...current, email: event.target.value }))
                    }
                  />
                </label>

                <label>
                  Phone Number
                  <input
                    type="tel"
                    required
                    placeholder="+92 300 1234567"
                    value={registerForm.phone_number}
                    onChange={(event) =>
                      setRegisterForm((current) => ({ ...current, phone_number: event.target.value }))
                    }
                  />
                </label>
              </div>

              <div className="inline-grid" style={{ gridTemplateColumns: '1fr 1fr' }}>
                <label>
                  Password
                  <input
                    type="password"
                    required
                    placeholder="••••••••"
                    minLength={8}
                    value={registerForm.password}
                    onChange={(event) =>
                      setRegisterForm((current) => ({ ...current, password: event.target.value }))
                    }
                  />
                </label>

                <label>
                  Confirm Password
                  <input
                    type="password"
                    required
                    placeholder="••••••••"
                    minLength={8}
                    value={registerForm.confirm_password}
                    onChange={(event) =>
                      setRegisterForm((current) => ({ ...current, confirm_password: event.target.value }))
                    }
                  />
                </label>
              </div>

              {registerForm.password && registerForm.confirm_password && registerForm.password !== registerForm.confirm_password && (
                <small style={{ color: 'var(--brand-coral)', marginTop: '-0.5rem' }}>Passwords do not match.</small>
              )}

              <button type="submit" className="button" disabled={isSubmitting || (registerForm.password !== registerForm.confirm_password)} style={{ marginTop: '1rem', padding: '0.8rem' }}>
                {isSubmitting ? 'Creating account...' : 'Create Account'}
              </button>
            </form>
          )}
        </section>
      )}
    </main>
  )
}