import { useCallback, useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'

import { apiClient } from '../api/client'
import { PageHeader } from '../components/PageHeader'
import { useAppContext } from '../context/AppContext'
import { formatCurrency, formatDate } from '../utils/format'

function parseShipping(shippingAddressJson) {
  if (!shippingAddressJson) return null
  try {
    return JSON.parse(shippingAddressJson)
  } catch {
    return null
  }
}

export function OrdersPage() {
  const { token, user, pushToast } = useAppContext()

  const [orders, setOrders] = useState([])
  const [detailsById, setDetailsById] = useState({})
  const [expandedOrderIds, setExpandedOrderIds] = useState({})
  const [isLoading, setIsLoading] = useState(false)
  const [loadingDetailId, setLoadingDetailId] = useState('')

  const isAuthenticated = useMemo(() => Boolean(token && user), [token, user])

  const loadOrders = useCallback(async () => {
    if (!token) return

    setIsLoading(true)
    try {
      const data = await apiClient.listOrders(token)
      setOrders(data)
    } catch (error) {
      pushToast(error.message || 'Unable to load your orders.', 'error')
    } finally {
      setIsLoading(false)
    }
  }, [token, pushToast])

  useEffect(() => {
    if (!isAuthenticated) return
    loadOrders()
  }, [isAuthenticated, loadOrders])

  const toggleOrderDetails = async (orderId) => {
    const isExpanded = Boolean(expandedOrderIds[orderId])

    setExpandedOrderIds((current) => ({
      ...current,
      [orderId]: !isExpanded,
    }))

    if (isExpanded || detailsById[orderId] || !token) {
      return
    }

    setLoadingDetailId(orderId)
    try {
      const order = await apiClient.getOrder(orderId, token)
      setDetailsById((current) => ({
        ...current,
        [orderId]: order,
      }))
    } catch (error) {
      pushToast(error.message || 'Unable to load order details.', 'error')
    } finally {
      setLoadingDetailId('')
    }
  }

  if (!isAuthenticated) {
    return (
      <main className="page page-orders">
        <PageHeader
          eyebrow="Orders"
          title="Sign in to view orders"
          subtitle="Track your purchases, delivery updates, and complete order history in one place."
        />

        <section className="panel orders-empty-panel">
          <h2>Your order history is private</h2>
          <p>
            Please sign in or create an account to see all past orders and payment details.
          </p>
          <div className="form-actions">
            <Link to="/auth?mode=login&redirectTo=/orders" className="button">
              Sign in
            </Link>
            <Link to="/auth?mode=register&redirectTo=/orders" className="button button-secondary">
              Create account
            </Link>
          </div>
        </section>
      </main>
    )
  }

  return (
    <main className="page page-orders">
      <PageHeader
        eyebrow="Orders"
        title="Your order history"
        subtitle="Open any order card to view shipping, totals, and item-level details."
      />

      {isLoading ? <p className="empty-state">Loading your orders...</p> : null}

      {!isLoading && orders.length === 0 ? (
        <section className="panel orders-empty-panel">
          <h2>No orders yet</h2>
          <p>Your completed checkouts will appear here in a premium timeline view.</p>
          <div className="form-actions">
            <Link to="/builder" className="button">
              Start your first basket
            </Link>
            <Link to="/cart" className="button button-secondary">
              Go to cart
            </Link>
          </div>
        </section>
      ) : null}

      {!isLoading && orders.length > 0 ? (
        <section className="orders-grid">
          {orders.map((order) => {
            const isExpanded = Boolean(expandedOrderIds[order.id])
            const details = detailsById[order.id]
            const detailsShipping = parseShipping(details?.shipping_address_json)

            return (
              <article key={order.id} className="panel order-card">
                <header className="order-card-header">
                  <div>
                    <h2>Order {order.id}</h2>
                    <p className="compact-copy">Placed on {formatDate(order.created_at)}</p>
                  </div>
                  <span className="pill subtle-pill">{order.status}</span>
                </header>

                <div className="order-card-summary">
                  <p>
                    Total: <strong>{formatCurrency(order.total)}</strong>
                  </p>
                  <p>Items: {order.items.length}</p>
                </div>

                <div className="form-actions">
                  <button
                    type="button"
                    className="button button-secondary"
                    onClick={() => toggleOrderDetails(order.id)}
                  >
                    {isExpanded ? 'Hide details' : 'View details'}
                  </button>
                </div>

                {isExpanded ? (
                  <section className="order-card-details">
                    {loadingDetailId === order.id ? (
                      <p className="compact-copy">Loading order details...</p>
                    ) : null}

                    {!loadingDetailId && details ? (
                      <>
                        <div className="order-detail-grid">
                          <p>
                            Subtotal: <strong>{formatCurrency(details.subtotal)}</strong>
                          </p>
                          <p>
                            Shipping fee: <strong>{formatCurrency(details.shipping_fee)}</strong>
                          </p>
                          <p>
                            Grand total: <strong>{formatCurrency(details.total)}</strong>
                          </p>
                          <p>
                            Payment ref: <strong>{details.payment_ref || 'N/A'}</strong>
                          </p>
                        </div>

                        {detailsShipping ? (
                          <div className="order-shipping-block">
                            <h3>Shipping address</h3>
                            <p>
                              {detailsShipping.line1}
                              {detailsShipping.line2 ? `, ${detailsShipping.line2}` : ''}
                            </p>
                            <p>
                              {detailsShipping.city}, {detailsShipping.state} {detailsShipping.zip_code}, {detailsShipping.country}
                            </p>
                          </div>
                        ) : null}

                        <div className="order-items-block">
                          <h3>Items</h3>
                          <div className="stack-list">
                            {details.items.map((item) => (
                              <article key={item.id} className="list-row">
                                <div>
                                  <strong>Basket {item.basket_id || 'N/A'}</strong>
                                  <p>Quantity: {item.quantity}</p>
                                </div>
                                <p>{formatCurrency(item.unit_price)}</p>
                              </article>
                            ))}
                          </div>
                        </div>
                      </>
                    ) : null}
                  </section>
                ) : null}
              </article>
            )
          })}
        </section>
      ) : null}
    </main>
  )
}