import { useCallback, useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'

import { apiClient } from '../api/client'
import { PageHeader } from '../components/PageHeader'
import { AdminChatPanel } from '../components/admin/AdminChatPanel'
import { useAppContext } from '../context/AppContext'
import { formatCurrency, formatDate } from '../utils/format'

const EMPTY_CATEGORY = {
  name: '',
  slug: '',
  description: '',
  image_url: '',
}

const EMPTY_PRODUCT = {
  sku: '',
  title: '',
  description: '',
  price: '',
  image_url: '',
  category_id: '',
  inventory_count: 0,
  is_active: true,
}

const EMPTY_BASE = {
  name: '',
  size: 'M',
  price: '',
  image_url: '',
  max_items: 8,
}

const ORDER_STATUSES = ['pending', 'processing', 'shipped', 'delivered']

export function AdminPage() {
  const { token, user, pushToast } = useAppContext()

  const [activeTab, setActiveTab] = useState('orders')

  const [categoryForm, setCategoryForm] = useState(EMPTY_CATEGORY)
  const [productForm, setProductForm] = useState(EMPTY_PRODUCT)
  const [baseForm, setBaseForm] = useState(EMPTY_BASE)

  const [orders, setOrders] = useState([])
  const [categories, setCategories] = useState([])
  const [products, setProducts] = useState([])
  const [bases, setBases] = useState([])

  const [statusDrafts, setStatusDrafts] = useState({})
  const [selectedPackingOrder, setSelectedPackingOrder] = useState(null)
  const [packingList, setPackingList] = useState([])

  const [isLoadingOrders, setIsLoadingOrders] = useState(false)
  const [isLoadingData, setIsLoadingData] = useState(false)

  const canUseAdmin = useMemo(() => Boolean(token && user?.role === 'admin'), [token, user])

  const loadData = useCallback(async () => {
    if (!token) return
    setIsLoadingData(true)
    try {
      const [cats, prods, bss] = await Promise.all([
        apiClient.listCategories(),
        apiClient.listProducts({ limit: 100 }),
        apiClient.listBases()
      ])
      setCategories(cats)
      setProducts(prods)
      setBases(bss)
    } catch (error) {
      pushToast(error.message || 'Unable to load catalog data.', 'error')
    } finally {
      setIsLoadingData(false)
    }
  }, [token, pushToast])

  const loadOrders = useCallback(async () => {
    if (!token) return
    setIsLoadingOrders(true)
    try {
      const data = await apiClient.adminListOrders({ limit: 100 }, token)
      setOrders(data)
      setStatusDrafts(
        Object.fromEntries(data.map((order) => [order.id, order.status])),
      )
    } catch (error) {
      pushToast(error.message || 'Unable to load admin orders.', 'error')
    } finally {
      setIsLoadingOrders(false)
    }
  }, [token, pushToast])

  useEffect(() => {
    if (!canUseAdmin) return
    if (activeTab === 'orders') {
      loadOrders()
    } else {
      loadData()
    }
  }, [canUseAdmin, activeTab, loadOrders, loadData])

  const createCategory = async (event) => {
    event.preventDefault()
    if (!token) return
    try {
      await apiClient.adminCreateCategory(categoryForm, token)
      setCategoryForm(EMPTY_CATEGORY)
      pushToast('Category created successfully.', 'success')
      loadData()
    } catch (error) {
      pushToast(error.message || 'Unable to create category.', 'error')
    }
  }

  const createProduct = async (event) => {
    event.preventDefault()
    if (!token) return
    if (!productForm.category_id) {
      pushToast('Please select a category.', 'info')
      return
    }
    try {
      await apiClient.adminCreateProduct(
        {
          ...productForm,
          price: Number(productForm.price || 0),
          inventory_count: Number(productForm.inventory_count || 0),
          category_id: productForm.category_id,
        },
        token,
      )
      setProductForm(EMPTY_PRODUCT)
      pushToast('Product created successfully.', 'success')
      loadData()
    } catch (error) {
      pushToast(error.message || 'Unable to create product.', 'error')
    }
  }

  const createBase = async (event) => {
    event.preventDefault()
    if (!token) return
    try {
      await apiClient.adminCreateBase(
        {
          ...baseForm,
          price: Number(baseForm.price || 0),
          max_items: Number(baseForm.max_items || 0),
        },
        token,
      )
      setBaseForm(EMPTY_BASE)
      pushToast('Gift base created successfully.', 'success')
      loadData()
    } catch (error) {
      pushToast(error.message || 'Unable to create base.', 'error')
    }
  }

  const updateOrderStatus = async (orderId) => {
    if (!token) return
    try {
      const status = statusDrafts[orderId]
      await apiClient.adminUpdateOrderStatus(orderId, { status }, token)
      pushToast('Order status updated.', 'success')
      await loadOrders()
    } catch (error) {
      pushToast(error.message || 'Unable to update order status.', 'error')
    }
  }

  const fetchPackingList = async (orderId) => {
    if (!token) return
    try {
      const data = await apiClient.adminGetPackingList(orderId, token)
      setSelectedPackingOrder(orderId)
      setPackingList(data)
      pushToast('Packing list loaded.', 'success')
    } catch (error) {
      pushToast(error.message || 'Unable to fetch packing list.', 'error')
    }
  }

  const uploadImage = async (file) => {
    if (!token || !file) return null
    setIsLoadingData(true)
    try {
      const response = await apiClient.uploadImage(file, token)
      pushToast('Image uploaded successfully', 'success')
      return response.url
    } catch (error) {
      pushToast(error.message || 'Image upload failed', 'error')
      return null
    } finally {
      setIsLoadingData(false)
    }
  }

  const handleProductImageUpload = async (e) => {
    const file = e.target.files[0]
    if (!file) return
    const url = await uploadImage(file)
    if (url) {
      setProductForm(c => ({ ...c, image_url: url }))
    }
  }

  const handleCategoryImageUpload = async (e) => {
    const file = e.target.files[0]
    if (!file) return
    const url = await uploadImage(file)
    if (url) {
      setCategoryForm(c => ({ ...c, image_url: url }))
    }
  }

  const handleBaseImageUpload = async (e) => {
    const file = e.target.files[0]
    if (!file) return
    const url = await uploadImage(file)
    if (url) {
      setBaseForm(c => ({ ...c, image_url: url }))
    }
  }

  if (!canUseAdmin) {
    return (
      <main className="page page-admin">
        <PageHeader
          eyebrow="Admin"
          title="Admin access required"
          subtitle="Sign in with an admin role account to manage inventory and orders."
        />
        <section className="panel" style={{ textAlign: 'center' }}>
          <Link className="button" to="/auth">
            Go to sign in
          </Link>
        </section>
      </main>
    )
  }

  return (
    <main className="page page-admin">
      <PageHeader
        eyebrow="Dashboard"
        title="Operations Center"
        subtitle="Manage your catalog and fulfill customer orders."
      />

      <div className="auth-tabs" style={{ display: 'flex', justifyContent: 'center', marginBottom: '2rem' }}>
        <button
          className={activeTab === 'orders' ? 'active' : ''}
          onClick={() => setActiveTab('orders')}
        >
          Orders & Fulfillment
        </button>
        <button
          className={activeTab === 'products' ? 'active' : ''}
          onClick={() => setActiveTab('products')}
        >
          Manage Products
        </button>
        <button
          className={activeTab === 'categories' ? 'active' : ''}
          onClick={() => setActiveTab('categories')}
        >
          Manage Categories
        </button>
        <button
          className={activeTab === 'bases' ? 'active' : ''}
          onClick={() => setActiveTab('bases')}
        >
          Manage Bases
        </button>
        <button
          className={activeTab === 'chat' ? 'active' : ''}
          onClick={() => setActiveTab('chat')}
        >
          Live Chat
        </button>
      </div>

      {activeTab === 'chat' && (
        <section>
          <AdminChatPanel />
        </section>
      )}

      {activeTab === 'products' && (
        <section className="account-grid">
          <article className="panel">
            <h2>Add New Product</h2>
            <p className="compact-copy" style={{ marginBottom: '1rem' }}>
              Create an item that goes inside a gift basket.
            </p>
            <form className="stack-form" onSubmit={createProduct}>
              <div className="inline-grid">
                <label>
                  SKU (Unique ID)
                  <input
                    required
                    placeholder="e.g. SNACK-001"
                    value={productForm.sku}
                    onChange={(e) => setProductForm((c) => ({ ...c, sku: e.target.value }))}
                  />
                </label>
                <label>
                  Title
                  <input
                    required
                    placeholder="e.g. Gourmet Chocolate Bar"
                    value={productForm.title}
                    onChange={(e) => setProductForm((c) => ({ ...c, title: e.target.value }))}
                  />
                </label>
              </div>
              <label>
                Description
                <textarea
                  rows={2}
                  placeholder="Describe the product..."
                  value={productForm.description}
                  onChange={(e) => setProductForm((c) => ({ ...c, description: e.target.value }))}
                />
              </label>
              <div className="inline-grid">
                <label>
                  Price ($)
                  <input
                    type="number"
                    min="0"
                    step="0.01"
                    required
                    placeholder="e.g. 5.99"
                    value={productForm.price}
                    onChange={(e) => setProductForm((c) => ({ ...c, price: e.target.value }))}
                  />
                </label>
                <label>
                  Inventory Count
                  <input
                    type="number"
                    min="0"
                    required
                    placeholder="e.g. 50"
                    value={productForm.inventory_count}
                    onChange={(e) => setProductForm((c) => ({ ...c, inventory_count: e.target.value }))}
                  />
                </label>
              </div>
              <label>
                Category
                <select
                  required
                  value={productForm.category_id}
                  onChange={(e) => setProductForm((c) => ({ ...c, category_id: e.target.value }))}
                >
                  <option value="" disabled>-- Select a category --</option>
                  {categories.map(cat => (
                    <option key={cat.id} value={cat.id}>{cat.name}</option>
                  ))}
                </select>
              </label>
              <label>
                Upload Image
                <input
                  type="file"
                  accept="image/*"
                  onChange={handleProductImageUpload}
                  style={{ marginBottom: '0.5rem' }}
                />
                {productForm.image_url && (
                  <div style={{ marginTop: '0.5rem', background: 'rgba(0,0,0,0.2)', padding: '0.5rem', borderRadius: '0.5rem' }}>
                    <small style={{ color: 'var(--brand-teal)', display: 'block' }}>Image uploaded securely to database:</small>
                    <code style={{ fontSize: '0.8rem', wordBreak: 'break-all' }}>{productForm.image_url}</code>
                  </div>
                )}
              </label>
              <label className="checkbox-label" style={{ marginTop: '0.5rem' }}>
                <input
                  type="checkbox"
                  checked={productForm.is_active}
                  onChange={(e) => setProductForm((c) => ({ ...c, is_active: e.target.checked }))}
                />
                Product is active and visible
              </label>
              <button type="submit" className="button" style={{ marginTop: '0.5rem' }}>
                Create Product
              </button>
            </form>
          </article>

          <article className="panel subtle-panel">
            <h2>Existing Products</h2>
            <p className="compact-copy">You have {products.length} products in the catalog.</p>
            {isLoadingData ? <p>Loading...</p> : (
              <div className="stack-list" style={{ maxHeight: '600px', overflowY: 'auto' }}>
                {products.map(p => (
                  <div key={p.id} className="list-row" style={{ padding: '0.6rem' }}>
                    <div>
                      <strong style={{ display: 'block', marginBottom: '0.2rem' }}>{p.title}</strong>
                      <small style={{ color: 'var(--ink-muted)' }}>{p.sku} | ${p.price} | Stock: {p.inventory_count}</small>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </article>
        </section>
      )}

      {activeTab === 'categories' && (
        <section className="account-grid">
          <article className="panel">
            <h2>Add New Category</h2>
            <p className="compact-copy" style={{ marginBottom: '1rem' }}>
              Organize products into groups (e.g., Snacks, Self-Care).
            </p>
            <form className="stack-form" onSubmit={createCategory}>
              <div className="inline-grid">
                <label>
                  Category Name
                  <input
                    required
                    placeholder="e.g. Sweet Treats"
                    value={categoryForm.name}
                    onChange={(e) => setCategoryForm((c) => ({ ...c, name: e.target.value }))}
                  />
                </label>
                <label>
                  URL Slug
                  <input
                    required
                    placeholder="e.g. sweet-treats"
                    value={categoryForm.slug}
                    onChange={(e) => setCategoryForm((c) => ({ ...c, slug: e.target.value }))}
                  />
                </label>
              </div>
              <label>
                Description
                <textarea
                  rows={2}
                  placeholder="Short description..."
                  value={categoryForm.description}
                  onChange={(e) => setCategoryForm((c) => ({ ...c, description: e.target.value }))}
                />
              </label>
              <label>
                Upload Image
                <input
                  type="file"
                  accept="image/*"
                  onChange={handleCategoryImageUpload}
                  style={{ marginBottom: '0.5rem' }}
                />
                {categoryForm.image_url && (
                  <div style={{ marginTop: '0.5rem', background: 'rgba(0,0,0,0.2)', padding: '0.5rem', borderRadius: '0.5rem' }}>
                    <small style={{ color: 'var(--brand-teal)', display: 'block' }}>Image uploaded securely to database:</small>
                    <code style={{ fontSize: '0.8rem', wordBreak: 'break-all' }}>{categoryForm.image_url}</code>
                  </div>
                )}
              </label>
              <button type="submit" className="button" style={{ marginTop: '0.5rem' }}>
                Create Category
              </button>
            </form>
          </article>

          <article className="panel subtle-panel">
            <h2>Existing Categories</h2>
            <p className="compact-copy">You have {categories.length} categories.</p>
            {isLoadingData ? <p>Loading...</p> : (
              <div className="stack-list">
                {categories.map(c => (
                  <div key={c.id} className="list-row" style={{ padding: '0.6rem' }}>
                    <div>
                      <strong style={{ display: 'block', marginBottom: '0.2rem' }}>{c.name}</strong>
                      <small style={{ color: 'var(--ink-muted)' }}>Slug: {c.slug}</small>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </article>
        </section>
      )}

      {activeTab === 'bases' && (
        <section className="account-grid">
          <article className="panel">
            <h2>Add Gift Base</h2>
            <p className="compact-copy" style={{ marginBottom: '1rem' }}>
              Containers that hold the gift items (Baskets, Boxes).
            </p>
            <form className="stack-form" onSubmit={createBase}>
              <div className="inline-grid">
                <label>
                  Base Name
                  <input
                    required
                    placeholder="e.g. Wicker Basket"
                    value={baseForm.name}
                    onChange={(e) => setBaseForm((c) => ({ ...c, name: e.target.value }))}
                  />
                </label>
                <label>
                  Size
                  <select
                    value={baseForm.size}
                    onChange={(e) => setBaseForm((c) => ({ ...c, size: e.target.value }))}
                  >
                    <option value="S">Small (S)</option>
                    <option value="M">Medium (M)</option>
                    <option value="L">Large (L)</option>
                  </select>
                </label>
              </div>
              <div className="inline-grid">
                <label>
                  Price ($)
                  <input
                    type="number"
                    min="0"
                    step="0.01"
                    required
                    placeholder="e.g. 12.00"
                    value={baseForm.price}
                    onChange={(e) => setBaseForm((c) => ({ ...c, price: e.target.value }))}
                  />
                </label>
                <label>
                  Max Item Capacity
                  <input
                    type="number"
                    min="1"
                    required
                    placeholder="e.g. 8"
                    value={baseForm.max_items}
                    onChange={(e) => setBaseForm((c) => ({ ...c, max_items: e.target.value }))}
                  />
                </label>
              </div>
              <label>
                Upload Image
                <input
                  type="file"
                  accept="image/*"
                  onChange={handleBaseImageUpload}
                  style={{ marginBottom: '0.5rem' }}
                />
                {baseForm.image_url && (
                  <div style={{ marginTop: '0.5rem', background: 'rgba(0,0,0,0.2)', padding: '0.5rem', borderRadius: '0.5rem' }}>
                    <small style={{ color: 'var(--brand-teal)', display: 'block' }}>Image uploaded securely to database:</small>
                    <code style={{ fontSize: '0.8rem', wordBreak: 'break-all' }}>{baseForm.image_url}</code>
                  </div>
                )}
              </label>
              <button type="submit" className="button" style={{ marginTop: '0.5rem' }}>
                Create Base Container
              </button>
            </form>
          </article>

          <article className="panel subtle-panel">
            <h2>Existing Bases</h2>
            <p className="compact-copy">You have {bases.length} bases configured.</p>
            {isLoadingData ? <p>Loading...</p> : (
              <div className="stack-list">
                {bases.map(b => (
                  <div key={b.id} className="list-row" style={{ padding: '0.6rem' }}>
                    <div>
                      <strong style={{ display: 'block', marginBottom: '0.2rem' }}>{b.name} ({b.size})</strong>
                      <small style={{ color: 'var(--ink-muted)' }}>Price: ${b.price} | Capacity: {b.max_items} items</small>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </article>
        </section>
      )}

      {activeTab === 'orders' && (
        <section className="panel">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
            <h2>Orders & Fulfillment</h2>
            <button className="button button-secondary" onClick={loadOrders} disabled={isLoadingOrders}>
              {isLoadingOrders ? 'Refreshing...' : 'Refresh Orders'}
            </button>
          </div>

          <div className="stack-list">
            {orders.map((order) => (
              <article key={order.id} className="list-row order-card">
                <div style={{ flex: 1 }}>
                  <strong style={{ fontSize: '1.1rem', color: '#fff' }}>Order #{order.id.slice(0, 8)}</strong>
                  <div className="order-card-summary" style={{ marginTop: '0.5rem' }}>
                    <p><strong>Date:</strong> {formatDate(order.created_at)}</p>
                    <p><strong>Total:</strong> {formatCurrency(order.total)}</p>
                    <p><strong>Status:</strong> <span style={{ color: 'var(--brand-teal)' }}>{order.status.toUpperCase()}</span></p>
                    <p><strong>Items:</strong> {order.items.length} baskets</p>
                  </div>
                </div>

                <div className="row-actions" style={{ padding: '1rem', background: 'rgba(0,0,0,0.2)', borderRadius: '0.8rem', minWidth: '280px' }}>
                  <label style={{ width: '100%', marginBottom: '0.5rem' }}>
                    <span style={{ fontSize: '0.8rem', textTransform: 'uppercase', letterSpacing: '1px' }}>Update Status</span>
                    <select
                      style={{ width: '100%' }}
                      value={statusDrafts[order.id] || order.status}
                      onChange={(event) =>
                        setStatusDrafts((current) => ({ ...current, [order.id]: event.target.value }))
                      }
                    >
                      {ORDER_STATUSES.map((status) => (
                        <option key={status} value={status}>
                          {status.charAt(0).toUpperCase() + status.slice(1)}
                        </option>
                      ))}
                    </select>
                  </label>
                  <button type="button" className="button" style={{ flex: 1 }} onClick={() => updateOrderStatus(order.id)}>
                    Save Status
                  </button>
                  <button type="button" className="button button-secondary" style={{ flex: 1 }} onClick={() => fetchPackingList(order.id)}>
                    Packing List
                  </button>
                </div>
              </article>
            ))}

            {!isLoadingOrders && orders.length === 0 ? (
              <div className="orders-empty-panel" style={{ padding: '3rem 1rem' }}>
                <p>No orders have been placed yet.</p>
              </div>
            ) : null}
          </div>

          {selectedPackingOrder && (
            <div style={{ marginTop: '2rem', borderTop: '1px solid var(--line)', paddingTop: '2rem' }}>
              <h2>Packing List: #{selectedPackingOrder.slice(0, 8)}</h2>
              {packingList.length === 0 ? <p>No packing details returned.</p> : null}

              <div className="stack-list">
                {packingList.map((entry, index) => (
                  <article key={`${entry.basket_id}-${index}`} className="list-row" style={{ alignItems: 'flex-start' }}>
                    <div style={{ flex: 1 }}>
                      <strong style={{ fontSize: '1.1rem', color: 'var(--brand-amber)' }}>
                        Basket {index + 1}: {entry.base_name} ({entry.base_size})
                      </strong>

                      <div style={{ marginTop: '0.8rem', background: 'rgba(255,255,255,0.03)', padding: '0.8rem', borderRadius: '0.5rem' }}>
                        <h4 style={{ margin: '0 0 0.5rem 0', color: 'var(--ink)' }}>Contents to pack:</h4>
                        <ul style={{ margin: 0, paddingLeft: '1.2rem', color: 'var(--ink-muted)' }}>
                          {entry.items.map((item, idx) => (
                            <li key={idx} style={{ marginBottom: '0.3rem' }}>
                              <strong>{item.quantity}x</strong> {item.product_title}
                            </li>
                          ))}
                        </ul>
                      </div>

                      <div style={{ marginTop: '0.8rem', display: 'flex', gap: '1rem', flexWrap: 'wrap' }}>
                        <p style={{ margin: 0, background: 'rgba(255, 126, 103, 0.1)', padding: '0.4rem 0.8rem', borderRadius: '0.4rem' }}>
                          🎀 <strong>Ribbon:</strong> {entry.ribbon_color || 'None specified'}
                        </p>
                        <p style={{ margin: 0, background: 'rgba(45, 192, 175, 0.1)', padding: '0.4rem 0.8rem', borderRadius: '0.4rem' }}>
                          📅 <strong>Deliver by:</strong> {entry.requested_delivery_date || 'Anytime'}
                        </p>
                      </div>

                      {entry.personalization_message && (
                        <div style={{ marginTop: '0.8rem', padding: '0.8rem', borderLeft: '3px solid var(--brand-coral)', background: 'rgba(0,0,0,0.2)' }}>
                          <small style={{ display: 'block', color: 'var(--ink-muted)', marginBottom: '0.2rem' }}>Gift Message:</small>
                          <em style={{ color: '#fff' }}>"{entry.personalization_message}"</em>
                        </div>
                      )}
                    </div>
                  </article>
                ))}
              </div>
            </div>
          )}
        </section>
      )}
    </main>
  )
}