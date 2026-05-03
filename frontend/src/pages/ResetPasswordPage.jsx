
import { useState } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'

import { apiClient } from '../api/client'
import { PageHeader } from '../components/PageHeader'
import { useAppContext } from '../context/AppContext'

export function ResetPasswordPage() {
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const { pushToast } = useAppContext()

  const token = searchParams.get('token')
  const [password, setPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [isSubmitting, setIsSubmitting] = useState(false)

  const handleSubmit = async (event) => {
    event.preventDefault()

    if (!token) {
      pushToast('Invalid reset link. Please request a new one.', 'error')
      return
    }

    if (password !== confirmPassword) {
      pushToast('Passwords do not match.', 'error')
      return
    }

    setIsSubmitting(true)
    try {
      await apiClient.resetPassword({
        token,
        new_password: password,
      })
      pushToast('Password changed successfully. You can now sign in.', 'success')
      navigate('/auth?mode=login')
    } catch (error) {
      pushToast(error.message || 'Unable to reset password.', 'error')
    } finally {
      setIsSubmitting(false)
    }
  }

  if (!token) {
    return (
      <main className="page">
        <PageHeader
          title="Invalid Link"
          subtitle="This password reset link is invalid or has expired."
        />
        <section className="panel" style={{ textAlign: 'center' }}>
          <button className="button" onClick={() => navigate('/auth?mode=login')}>
            Back to Sign In
          </button>
        </section>
      </main>
    )
  }

  return (
    <main className="page page-reset-password">
      <PageHeader
        eyebrow="Account Security"
        title="Set new password"
        subtitle="Choose a strong password to secure your account."
      />

      <section className="panel" style={{ maxWidth: '480px', margin: '0 auto', border: '1px solid var(--line)' }}>
        <form className="auth-form" onSubmit={handleSubmit}>
          <label>
            New Password
            <input
              type="password"
              required
              placeholder="••••••••"
              minLength={8}
              value={password}
              onChange={(e) => setPassword(e.target.value)}
            />
          </label>

          <label>
            Confirm New Password
            <input
              type="password"
              required
              placeholder="••••••••"
              minLength={8}
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
            />
          </label>

          {password && confirmPassword && password !== confirmPassword && (
            <small style={{ color: 'var(--brand-coral)', marginBottom: '1rem', display: 'block' }}>
              Passwords do not match.
            </small>
          )}

          <button type="submit" className="button" disabled={isSubmitting || !password || password !== confirmPassword}>
            {isSubmitting ? 'Changing password...' : 'Change Password'}
          </button>
        </form>
      </section>
    </main>
  )
}