import { useCallback, useEffect, useMemo, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'

import { apiClient } from '../api/client'
import { PageHeader } from '../components/PageHeader'
import { useAppContext } from '../context/AppContext'
import { formatCurrency } from '../utils/format'

const EMPTY_SHIPPING = {
  line1: '',
  line2: '',
  city: '',
  state: '',
  zip_code: '',
  country: 'Pakistan',
}

const EMPTY_CARD = {
  name: '',
  number: '',
  expiry: '',
  cvv: '',
}

function formatCardNumber(raw) {
  const digits = raw.replace(/\D/g, '').slice(0, 16)
  return digits.replace(/(.{4})/g, '$1 ').trim()
}

function formatExpiry(raw) {
  const digits = raw.replace(/\D/g, '').slice(0, 4)
  if (digits.length > 2) return `${digits.slice(0, 2)}-${digits.slice(2)}`
  return digits
}

export function CartPage() {
  const navigate = useNavigate()
  const {
    token,
    sessionId,
    user,
    cart,
    refreshCart,
    ensureGuestSession,
    pushToast,
  } = useAppContext()

  const [lineItems, setLineItems] = useState([])
  const [addresses, setAddresses] = useState([])
  const [selectedAddressId, setSelectedAddressId] = useState('')
  const [shippingForm, setShippingForm] = useState(EMPTY_SHIPPING)
  const [cardForm, setCardForm] = useState(EMPTY_CARD)
  const [checkoutResult, setCheckoutResult] = useState(null)
  const [isCheckingOut, setIsCheckingOut] = useState(false)
  const [showAuthPrompt, setShowAuthPrompt] = useState(false)

  const resolveAuthMeta = useCallback(async () => {
    let activeSessionId = sessionId
    if (!token && !activeSessionId) {
      activeSessionId = await ensureGuestSession()
    }
    return {
      token,
      sessionId: activeSessionId,
    }
  }, [token, sessionId, ensureGuestSession])

  const loadAddresses = useCallback(async () => {
    if (!token) {
      setAddresses([])
      return
    }

    try {
      const data = await apiClient.listAddresses(token)
      setAddresses(data)

      const preferred = data.find((address) => address.is_default) || data[0]
      if (preferred) {
        setSelectedAddressId(preferred.id)
      }
    } catch (error) {
      pushToast(error.message || 'Unable to load addresses.', 'error')
    }
  }, [token, pushToast])

  useEffect(() => {
    loadAddresses()
  }, [loadAddresses])

  useEffect(() => {
    let isMounted = true

    async function loadBasketSummaries() {
      if (!cart?.items?.length) {
        setLineItems([])
        return
      }

      const meta = await resolveAuthMeta()

      const itemsWithBaskets = await Promise.all(
        cart.items.map(async (item) => {
          try {
            const basket = await apiClient.getBasketSummary(item.basket_id, meta)
            return {
              ...item,
              basket,
              error: null,
            }
          } catch (error) {
            return {
              ...item,
              basket: null,
              error: error.message,
            }
          }
        }),
      )

      if (!isMounted) return
      setLineItems(itemsWithBaskets)
    }

    loadBasketSummaries()

    return () => {
      isMounted = false
    }
  }, [cart, resolveAuthMeta])

  const updateQuantity = async (itemId, quantity) => {
    const safeQuantity = Number(quantity)
    if (!safeQuantity || safeQuantity < 1) return

    try {
      const meta = await resolveAuthMeta()
      await apiClient.updateCartItem(itemId, { quantity: safeQuantity }, meta)
      await refreshCart()
      pushToast('Cart quantity updated.', 'success')
    } catch (error) {
      pushToast(error.message || 'Unable to update cart item.', 'error')
    }
  }

  const removeItem = async (itemId) => {
    try {
      const meta = await resolveAuthMeta()
      await apiClient.removeCartItem(itemId, meta)
      await refreshCart()
      pushToast('Item removed from cart.', 'success')
    } catch (error) {
      pushToast(error.message || 'Unable to remove cart item.', 'error')
    }
  }

  const selectedAddress = useMemo(
    () => addresses.find((address) => address.id === selectedAddressId) || null,
    [addresses, selectedAddressId],
  )

  const checkout = async (event) => {
    event.preventDefault()

    if (!token || !user) {
      setShowAuthPrompt(true)
      return
    }

    setIsCheckingOut(true)

    try {
      const meta = await resolveAuthMeta()

      const shipping = selectedAddress
        ? {
            line1: selectedAddress.line1,
            line2: selectedAddress.line2,
            city: selectedAddress.city,
            state: selectedAddress.state,
            zip_code: selectedAddress.zip_code,
            country: selectedAddress.country,
          }
        : shippingForm

      const payload = {
        shipping,
        address_id: selectedAddress ? selectedAddress.id : undefined,
      }

      const order = await apiClient.checkout(payload, meta)
      setCheckoutResult(order)
      await refreshCart()
      pushToast('Order placed successfully.', 'success')
    } catch (error) {
      pushToast(error.message || 'Checkout failed.', 'error')
    } finally {
      setIsCheckingOut(false)
    }
  }

  const hasItems = Boolean(cart?.items?.length)

  if (checkoutResult) {
    return (
      <main className="page page-cart">
        <PageHeader eyebrow="Success" title="Order Confirmed!" subtitle="Thank you for shopping with DIY Gift Basket." />
        <section className="panel" style={{ textAlign: 'center', padding: '4rem 2rem', maxWidth: '600px', margin: '0 auto' }}>
          <div style={{ background: 'rgba(45, 192, 175, 0.1)', width: '80px', height: '80px', borderRadius: '50%', margin: '0 auto 1.5rem', display: 'grid', placeItems: 'center', color: 'var(--brand-teal)' }}>
            <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg>
          </div>
          <h2 style={{ marginBottom: '1rem' }}>Order #{checkoutResult.id.slice(0, 8).toUpperCase()}</h2>
          <p style={{ color: 'var(--ink-muted)' }}>We've received your order and are getting it ready to be shipped.</p>

          <div style={{ background: 'rgba(0,0,0,0.2)', padding: '1.5rem', borderRadius: '0.8rem', margin: '2rem 0', textAlign: 'left' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
              <span style={{ color: 'var(--ink-muted)' }}>Date:</span>
              <span>{new Date(checkoutResult.created_at).toLocaleDateString()}</span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
              <span style={{ color: 'var(--ink-muted)' }}>Status:</span>
              <span style={{ color: 'var(--brand-teal)', textTransform: 'capitalize' }}>{checkoutResult.status}</span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.5rem', fontWeight: 'bold' }}>
              <span>Total Paid:</span>
              <span style={{ color: 'var(--brand-amber)' }}>{formatCurrency(checkoutResult.total)}</span>
            </div>
          </div>

          <div style={{ display: 'flex', gap: '1rem', justifyContent: 'center' }}>
            <Link to="/orders" className="button">Track Order</Link>
            <Link to="/" className="button button-secondary">Continue Shopping</Link>
          </div>
        </section>
      </main>
    )
  }

  return (
    <main className="page page-cart">
      <PageHeader
        eyebrow="Secure Checkout"
        title="Review & Complete"
        subtitle="Confirm your shipping details and place your order."
      />

      {!hasItems ? (
        <section className="panel empty-state" style={{ maxWidth: '600px', margin: '0 auto', padding: '4rem 2rem' }}>
          <div style={{ background: 'rgba(212, 225, 255, 0.05)', width: '80px', height: '80px', borderRadius: '50%', margin: '0 auto 1.5rem', display: 'grid', placeItems: 'center', color: 'var(--ink-muted)' }}>
            <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="9" cy="21" r="1"/><circle cx="20" cy="21" r="1"/><path d="M1 1h4l2.68 13.39a2 2 0 0 0 2 1.61h9.72a2 2 0 0 0 2-1.61L23 6H6"/></svg>
          </div>
          <h2>Your cart is empty</h2>
          <p style={{ color: 'var(--ink-muted)', marginBottom: '2rem' }}>Looks like you haven't added any custom baskets yet.</p>
          <Link to="/builder" className="button" style={{ display: 'inline-flex' }}>
            Start Building a Basket
          </Link>
        </section>
      ) : (
        <div style={{ display: 'grid', gridTemplateColumns: '1.5fr 1fr', gap: '2rem', alignItems: 'start' }}>
          {}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '2rem' }}>

            <form id="checkout-form" className="stack-form" onSubmit={checkout}>
              <section className="panel" style={{ padding: '2rem' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', marginBottom: '1.5rem' }}>
                  <span style={{ background: 'var(--brand-teal)', color: '#000', width: '32px', height: '32px', borderRadius: '50%', display: 'grid', placeItems: 'center', fontWeight: 'bold' }}>1</span>
                  <h2 style={{ margin: 0 }}>Shipping Information</h2>
                </div>
                <label>
                  Saved Addresses
                  <select
                    value={selectedAddressId}
                    onChange={(event) => setSelectedAddressId(event.target.value)}
                    style={{ padding: '0.8rem' }}
                  >
                    <option value="">+ Add a new shipping address</option>
                    {addresses.map((address) => (
                      <option key={address.id} value={address.id}>
                        {address.label}: {address.line1}, {address.city}
                      </option>
                    ))}
                  </select>
                </label>

                {!selectedAddress ? (
                  <div style={{ background: 'rgba(0,0,0,0.1)', padding: '1.5rem', borderRadius: '0.8rem', marginTop: '1rem' }}>
                    <h3 style={{ fontSize: '1.1rem', marginBottom: '1rem', color: 'var(--brand-amber)' }}>New Address Details</h3>
                    <div className="inline-grid">
                      <label>
                        Address line 1
                        <input
                          type="text"
                          required
                          placeholder="House 5, Street 3, Block B"
                          value={shippingForm.line1}
                          onChange={(event) =>
                            setShippingForm((current) => ({ ...current, line1: event.target.value }))
                          }
                        />
                      </label>
                      <label>
                        Address line 2
                        <input
                          type="text"
                          placeholder="Near Masjid, optional"
                          value={shippingForm.line2}
                          onChange={(event) =>
                            setShippingForm((current) => ({ ...current, line2: event.target.value }))
                          }
                        />
                      </label>
                    </div>
                    <div className="inline-grid" style={{ gridTemplateColumns: '1.5fr 1fr' }}>
                      <label>
                        City
                        <input
                          type="text"
                          required
                          placeholder="Lahore"
                          value={shippingForm.city}
                          onChange={(event) =>
                            setShippingForm((current) => ({ ...current, city: event.target.value }))
                          }
                        />
                      </label>
                      <label>
                        State / Province
                        <input
                          type="text"
                          required
                          placeholder="Punjab"
                          value={shippingForm.state}
                          onChange={(event) =>
                            setShippingForm((current) => ({ ...current, state: event.target.value }))
                          }
                        />
                      </label>
                    </div>
                    <div className="inline-grid">
                      <label>
                        Zip / Postal Code
                        <input
                          type="text"
                          required
                          placeholder="54000"
                          value={shippingForm.zip_code}
                          onChange={(event) =>
                            setShippingForm((current) => ({ ...current, zip_code: event.target.value }))
                          }
                        />
                      </label>
                      <label>
                        Country
                        <input
                          type="text"
                          required
                          placeholder="Pakistan"
                          value={shippingForm.country}
                          onChange={(event) =>
                            setShippingForm((current) => ({ ...current, country: event.target.value }))
                          }
                        />
                      </label>
                    </div>
                  </div>
                ) : null}
              </section>

              <section className="panel" style={{ padding: '2rem', marginTop: '2rem' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', marginBottom: '1.5rem' }}>
                  <span style={{ background: 'var(--brand-teal)', color: '#000', width: '32px', height: '32px', borderRadius: '50%', display: 'grid', placeItems: 'center', fontWeight: 'bold' }}>2</span>
                  <h2 style={{ margin: 0 }}>Payment Information</h2>
                </div>

                <div style={{ background: 'rgba(0,0,0,0.1)', padding: '1.5rem', borderRadius: '0.8rem' }}>
                  <h3 style={{ fontSize: '1.1rem', marginBottom: '1rem', color: 'var(--brand-amber)' }}>Credit Card Details</h3>
                  <p style={{ color: 'var(--ink-muted)', marginBottom: '1.5rem', fontSize: '0.9rem' }}>
                    Note: This is currently in testing. Your card will not be charged.
                  </p>
                  <div className="inline-grid" style={{ marginBottom: '1rem' }}>
                    <label>
                      Name on Card
                      <input
                        type="text"
                        required
                        placeholder="Muhammad Ali"
                        value={cardForm.name}
                        onChange={(e) => setCardForm((c) => ({ ...c, name: e.target.value }))}
                      />
                    </label>
                    <label>
                      Card Number
                      <input
                        type="text"
                        required
                        placeholder="1234 5678 9012 3456"
                        maxLength="19"
                        value={cardForm.number}
                        onChange={(e) => setCardForm((c) => ({ ...c, number: formatCardNumber(e.target.value) }))}
                      />
                    </label>
                  </div>
                  <div className="inline-grid" style={{ gridTemplateColumns: '1.5fr 1fr' }}>
                    <label>
                      Expiry Date (MM-YY)
                      <input
                        type="text"
                        required
                        placeholder="MM-YY"
                        maxLength="5"
                        value={cardForm.expiry}
                        onChange={(e) => setCardForm((c) => ({ ...c, expiry: formatExpiry(e.target.value) }))}
                      />
                    </label>
                    <label>
                      CVV
                      <input
                        type="text"
                        required
                        pattern="\d{3,4}"
                        title="3 or 4 digit CVV"
                        placeholder="123"
                        maxLength="4"
                        value={cardForm.cvv}
                        onChange={(e) => setCardForm((c) => ({ ...c, cvv: e.target.value.replace(/\D/g, '') }))}
                      />
                    </label>
                  </div>
                </div>
              </section>
            </form>

            <section className="panel" style={{ padding: '2rem' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', marginBottom: '1.5rem' }}>
                <span style={{ background: 'var(--brand-teal)', color: '#000', width: '32px', height: '32px', borderRadius: '50%', display: 'grid', placeItems: 'center', fontWeight: 'bold' }}>3</span>
                <h2 style={{ margin: 0 }}>Review Items</h2>
              </div>

              <div className="stack-list">
                {lineItems.map((item) => (
                  <article key={item.id} className="list-row" style={{ padding: '1rem', background: 'rgba(0,0,0,0.2)' }}>
                    <div style={{ flex: 1 }}>
                      <strong style={{ fontSize: '1.1rem', color: '#fff' }}>{item.basket?.base?.name || 'Custom Basket'}</strong>
                      <p style={{ color: 'var(--ink-muted)', fontSize: '0.9rem', margin: '0.2rem 0 0.5rem' }}>Basket ID: {item.basket_id.slice(0, 8)}</p>
                      {item.error ? <p style={{ color: 'var(--brand-coral)' }}>{item.error}</p> : null}
                    </div>

                    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end', gap: '0.5rem' }}>
                      {item.basket ? (
                        <strong style={{ fontSize: '1.2rem', color: 'var(--brand-amber)' }}>
                          {formatCurrency(item.basket.running_total)}
                        </strong>
                      ) : null}
                      <div className="row-actions" style={{ padding: 0, background: 'transparent', border: 'none' }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', background: 'rgba(255,255,255,0.05)', borderRadius: '999px', padding: '0.2rem 0.5rem' }}>
                          <span style={{ fontSize: '0.8rem', color: 'var(--ink-muted)' }}>Qty:</span>
                          <input
                            type="number"
                            min="1"
                            value={item.quantity}
                            onChange={(event) => updateQuantity(item.id, event.target.value)}
                            style={{ width: '3rem', padding: '0.2rem', minHeight: 'auto', textAlign: 'center', background: 'transparent', border: 'none', color: '#fff' }}
                          />
                        </div>
                        <button
                          type="button"
                          className="ghost-button danger"
                          onClick={() => removeItem(item.id)}
                          title="Remove from cart"
                        >
                          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><polyline points="3 6 5 6 21 6"></polyline><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path></svg>
                        </button>
                      </div>
                    </div>
                  </article>
                ))}
              </div>
            </section>
          </div>

          {}
          <div style={{ position: 'sticky', top: '2rem' }}>
            <section className="panel" style={{ padding: '2rem', borderTop: '4px solid var(--brand-amber)' }}>
              <h2 style={{ marginBottom: '1.5rem', fontSize: '1.4rem' }}>Order Summary</h2>

              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '1rem', color: 'var(--ink-muted)' }}>
                <span>Subtotal ({cart?.items?.length} items)</span>
                <span>{formatCurrency(cart?.subtotal || 0)}</span>
              </div>

              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '1.5rem', color: 'var(--ink-muted)', paddingBottom: '1.5rem', borderBottom: '1px solid rgba(255,255,255,0.1)' }}>
                <span>Shipping Fee</span>
                <span>{formatCurrency(cart?.shipping_fee || 0)}</span>
              </div>

              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '2rem', fontSize: '1.3rem', fontWeight: 'bold' }}>
                <span>Total</span>
                <span style={{ color: 'var(--brand-amber)' }}>{formatCurrency(cart?.total || 0)}</span>
              </div>

              <button
                type="submit"
                form="checkout-form"
                className="button"
                disabled={isCheckingOut || !cart?.items?.length}
                style={{ width: '100%', padding: '1rem', fontSize: '1.1rem', background: 'linear-gradient(135deg, var(--brand-coral), var(--brand-amber))', border: 'none', color: '#fff', fontWeight: 'bold', borderRadius: '0.8rem', cursor: 'pointer', boxShadow: '0 8px 20px rgba(255, 111, 97, 0.3)' }}
              >
                {isCheckingOut ? 'Processing Securely...' : 'Place Order Now'}
              </button>

              <div style={{ textAlign: 'center', marginTop: '1rem', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '0.5rem', color: 'var(--ink-muted)', fontSize: '0.85rem' }}>
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><rect x="3" y="11" width="18" height="11" rx="2" ry="2"></rect><path d="M7 11V7a5 5 0 0 1 10 0v4"></path></svg>
                Secure 256-bit SSL encryption
              </div>
            </section>
          </div>
        </div>
      )}

      {showAuthPrompt ? (
        <section
          className="prebuilt-modal-backdrop"
          role="presentation"
          onClick={() => setShowAuthPrompt(false)}
        >
          <article
            className="panel checkout-auth-dialog"
            role="dialog"
            aria-modal="true"
            aria-label="Sign in required for checkout"
            onClick={(event) => event.stopPropagation()}
            style={{ textAlign: 'center', padding: '3rem 2rem' }}
          >
            <div style={{ background: 'rgba(255, 126, 103, 0.1)', width: '64px', height: '64px', borderRadius: '50%', margin: '0 auto 1rem', display: 'grid', placeItems: 'center', color: 'var(--brand-coral)' }}>
              <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path><circle cx="12" cy="7" r="4"></circle></svg>
            </div>
            <h2 style={{ marginBottom: '1rem' }}>Almost there!</h2>
            <p style={{ color: 'var(--ink-muted)', marginBottom: '2rem' }}>
              To ensure your order is securely tracked and updates can be sent to you, please sign in or create a free account.
            </p>
            <div className="form-actions" style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
              <button
                type="button"
                className="button"
                style={{ width: '100%', padding: '0.8rem' }}
                onClick={() => navigate('/auth?mode=register&redirectTo=/cart&intent=checkout')}
              >
                Create an Account
              </button>
              <button
                type="button"
                className="button button-secondary"
                style={{ width: '100%', padding: '0.8rem' }}
                onClick={() => navigate('/auth?mode=login&redirectTo=/cart&intent=checkout')}
              >
                Sign In
              </button>
              <button
                type="button"
                className="ghost-button"
                style={{ width: '100%' }}
                onClick={() => setShowAuthPrompt(false)}
              >
                Go back to cart
              </button>
            </div>
          </article>
        </section>
      ) : null}
    </main>
  )
}