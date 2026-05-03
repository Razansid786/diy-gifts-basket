import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'

import { NavBar } from './components/NavBar'
import { ToastTray } from './components/ToastTray'
import { AppProvider, useAppContext } from './context/AppContext'
import { AdminPage } from './pages/AdminPage'
import { AccountPage } from './pages/AccountPage'
import { AuthPage } from './pages/AuthPage'
import { BasketBuilderPage } from './pages/BasketBuilderPage'
import { CartPage } from './pages/CartPage'
import { HomePage } from './pages/HomePage'
import { NotFoundPage } from './pages/NotFoundPage'
import { OrdersPage } from './pages/OrdersPage'
import { ProductPage } from './pages/ProductPage'
import { ResetPasswordPage } from './pages/ResetPasswordPage'

function NonAdminRoute({ children }) {
  const { user, isAuthLoading } = useAppContext()
  if (isAuthLoading) return null
  if (user?.role === 'admin') {
    return <Navigate to="/admin" replace />
  }
  return children
}

function AppShell() {
  const { dismissToast, isAuthLoading, toasts } = useAppContext()

  return (
    <div className="app-shell">
      <NavBar />

      <div className="ambient-shape ambient-one" aria-hidden="true" />
      <div className="ambient-shape ambient-two" aria-hidden="true" />
      <div className="ambient-shape ambient-three" aria-hidden="true" />

      {isAuthLoading ? <p className="auth-loading">Preparing your experience...</p> : null}

      <Routes>
        <Route path="/" element={<HomePage />} />
        <Route path="/products/:productId" element={<ProductPage />} />
        <Route path="/builder" element={<NonAdminRoute><BasketBuilderPage /></NonAdminRoute>} />
        <Route path="/cart" element={<NonAdminRoute><CartPage /></NonAdminRoute>} />
        <Route path="/auth" element={<AuthPage />} />
        <Route path="/account" element={<AccountPage />} />
        <Route path="/reset-password" element={<ResetPasswordPage />} />
        <Route path="/orders" element={<NonAdminRoute><OrdersPage /></NonAdminRoute>} />
        <Route path="/admin" element={<AdminPage />} />
        <Route path="/home" element={<Navigate to="/" replace />} />
        <Route path="*" element={<NotFoundPage />} />
      </Routes>

      <footer className="app-footer">
        <p>DIY Gifts Basket | Built for premium custom gifting workflows.</p>
      </footer>

      <ToastTray toasts={toasts} onDismiss={dismissToast} />
      <ChatWidget />
    </div>
  )
}

import { ChatProvider } from './context/ChatContext'
import { ChatWidget } from './components/ChatWidget'

export default function App() {
  return (
    <AppProvider>
      <ChatProvider>
        <BrowserRouter>
          <AppShell />
        </BrowserRouter>
      </ChatProvider>
    </AppProvider>
  )
}