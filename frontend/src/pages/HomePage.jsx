import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { apiClient } from '../api/client'
import { useAppContext } from '../context/AppContext'
import { formatCurrency } from '../utils/format'
import { buildPrebuiltBaskets } from '../utils/prebuiltBaskets'
import { AIBuilderChat } from '../components/AIBuilderChat'

const FEATURED_BASKETS = [
  {
    id: 'celebration',
    title: 'Birthday Bliss Basket',
    subtitle: 'Chocolate, premium tea, and festive ribbon',
    imageUrl: '/images/prebuilt/Birthday Bliss Basket.jpg',
  },
  {
    id: 'wellness',
    title: 'Wellness Reset Basket',
    subtitle: 'Spa oils, candles, and calm evening picks',
    imageUrl: '/images/prebuilt/Wellnes Reset Basket.jpg',
  },
  {
    id: 'cozy',
    title: 'Cozy Evening Basket',
    subtitle: 'Hot cocoa kit, cookies, and soft textures',
    imageUrl: '/images/prebuilt/Cozy Evening Basket.jpg',
  },
]

async function withTimeout(task, timeoutMs = 15000, timeoutMessage = 'Request timed out') {
  let timeoutId
  const timeoutPromise = new Promise((_, reject) => {
    timeoutId = window.setTimeout(() => {
      reject(new Error(timeoutMessage))
    }, timeoutMs)
  })
  try {
    return await Promise.race([task, timeoutPromise])
  } finally {
    window.clearTimeout(timeoutId)
  }
}

function buildPrefillPayload(prebuiltBasket) {
  return {
    baseId: prebuiltBasket.baseId,
    items: prebuiltBasket.items.map((item) => ({
      productId: item.productId,
      quantity: item.quantity,
    })),
    personalization: prebuiltBasket.personalization,
  }
}

export function HomePage() {
  const navigate = useNavigate()
  const { user, token, sessionId, ensureGuestSession, refreshCart, pushToast } = useAppContext()
  const [products, setProducts] = useState([])
  const [bases, setBases] = useState([])
  const [categories, setCategories] = useState([])
  const [isLoading, setIsLoading] = useState(true)
  const [activeSlide, setActiveSlide] = useState(0)
  const [activeBasket, setActiveBasket] = useState(null)
  const [showAIBuilder, setShowAIBuilder] = useState(false)
  const [busyAction, setBusyAction] = useState(null)

  const [searchQuery, setSearchQuery] = useState('')
  const [selectedCategoryId, setSelectedCategoryId] = useState('')
  const [searchResults, setSearchResults] = useState([])
  const [isSearching, setIsSearching] = useState(false)
  const searchTimeoutRef = useRef(null)
  const isSearchActive = searchQuery.trim().length > 0 || selectedCategoryId !== ''

  const prebuiltBaskets = useMemo(
    () => buildPrebuiltBaskets(products, bases),
    [products, bases],
  )
  const fetchCatalog = useCallback(async () => {
    setIsLoading(true)
    try {
      const [productData, baseData, categoryData] = await Promise.all([
        apiClient.listProducts({ limit: 100 }),
        apiClient.listBases(),
        apiClient.listCategories({ limit: 50 }),
      ])
      setProducts(productData)
      setBases(baseData)
      setCategories(categoryData)
    } catch (error) {
      pushToast(error.message || 'Unable to load prebuilt baskets.', 'error')
    } finally {
      setIsLoading(false)
    }
  }, [pushToast])
  useEffect(() => {
    fetchCatalog()
  }, [fetchCatalog])
  useEffect(() => {
    const timer = window.setInterval(() => {
      setActiveSlide((current) => (current + 1) % FEATURED_BASKETS.length)
    }, 4200)
    return () => window.clearInterval(timer)
  }, [])

  useEffect(() => {
    if (searchTimeoutRef.current) window.clearTimeout(searchTimeoutRef.current)
    if (!searchQuery.trim() && !selectedCategoryId) {
      setSearchResults([])
      return
    }
    setIsSearching(true)
    searchTimeoutRef.current = window.setTimeout(async () => {
      try {
        const results = await apiClient.searchProducts({
          q: searchQuery.trim() || undefined,
          categoryId: selectedCategoryId || undefined,
          limit: 48,
        })
        setSearchResults(results)
      } catch {
        setSearchResults([])
      } finally {
        setIsSearching(false)
      }
    }, 350)
    return () => window.clearTimeout(searchTimeoutRef.current)
  }, [searchQuery, selectedCategoryId])
  useEffect(() => {
    if (!activeBasket) return
    const updatedBasket = prebuiltBaskets.find((basket) => basket.id === activeBasket.id)
    if (!updatedBasket) {
      setActiveBasket(null)
      return
    }
    setActiveBasket(updatedBasket)
  }, [prebuiltBaskets, activeBasket])
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
  const createBasketFromTemplate = useCallback(async (prebuiltBasket, meta) => {
    const payload = {
      base_id: prebuiltBasket.baseId || undefined,
      session_id: meta.token ? undefined : meta.sessionId,
    }
    let workingBasket = await withTimeout(
      apiClient.createBasket(payload, meta),
      15000,
      'Creating basket timed out. Please try again.',
    )
    for (const item of prebuiltBasket.items) {
      workingBasket = await withTimeout(
        apiClient.addBasketItem(
          workingBasket.id,
          {
            product_id: item.productId,
            quantity: item.quantity,
          },
          meta,
        ),
        15000,
        'Adding basket items timed out. Please try again.',
      )
    }
    const personalization = prebuiltBasket.personalization || {}
    if (
      personalization.gift_message ||
      personalization.ribbon_color ||
      personalization.requested_delivery_date
    ) {
      await withTimeout(
        apiClient.upsertPersonalization(
          workingBasket.id,
          {
            gift_message: personalization.gift_message || null,
            ribbon_color: personalization.ribbon_color || null,
            requested_delivery_date: personalization.requested_delivery_date || null,
          },
          meta,
        ),
        15000,
        'Saving personalization timed out. Please try again.',
      )
    }
    return workingBasket
  }, [])
  const handleCustomize = (prebuiltBasket) => {
    const payload = buildPrefillPayload(prebuiltBasket)
    navigate(`/builder?prefill=${encodeURIComponent(JSON.stringify(payload))}`)
  }
  const handleBuyNow = async (prebuiltBasket) => {
    setBusyAction({ basketId: prebuiltBasket.id, type: 'buy' })
    try {
      const meta = await resolveAuthMeta()
      await withTimeout(
        apiClient.quickBuy(
          {
            base_id: prebuiltBasket.baseId,
            session_id: meta.token ? undefined : meta.sessionId,
            items: prebuiltBasket.items.map((item) => ({
              product_id: item.productId,
              quantity: item.quantity,
            })),
            personalization: prebuiltBasket.personalization
              ? {
                  gift_message: prebuiltBasket.personalization.gift_message || null,
                  ribbon_color: prebuiltBasket.personalization.ribbon_color || null,
                  requested_delivery_date:
                    prebuiltBasket.personalization.requested_delivery_date || null,
                }
              : null,
          },
          meta,
        ),
        15000,
        'Adding basket to cart timed out. Please try again.',
      )
      await refreshCart()
      setActiveBasket(null)
      pushToast(`${prebuiltBasket.title} added to cart.`, 'success')
      navigate('/cart')
    } catch (error) {
      pushToast(error.message || 'Unable to add this basket to your cart.', 'error')
    } finally {
      setBusyAction(null)
    }
  }

  const handleAddAIProduct = async (product) => {
    try {
      setBusyAction({ type: 'ai-add' })
      const meta = await resolveAuthMeta()
      const newBasket = await withTimeout(
        apiClient.createBasket({
          base_id: 'box-standard',
          items: []
        }, meta),
        15000,
        'Creating basket timed out.'
      )
      
      await withTimeout(
        apiClient.addBasketItem(newBasket.id, {
          product_id: product.id,
          quantity: 1
        }, meta),
        15000,
        'Adding item timed out.'
      )
      
      await refreshCart()
      pushToast(`${product.title} added to your basket!`, 'success')
      navigate('/cart')
    } catch (err) {
      pushToast(err.message || 'Could not add item.', 'error')
    } finally {
      setBusyAction(null)
    }
  }
  const statsLabel = useMemo(() => {
    if (isLoading) return 'Preparing prebuilt baskets...'
    return `${prebuiltBaskets.length} prebuilt baskets ready`
  }, [isLoading, prebuiltBaskets.length])
  const nextSlide = () => {
    setActiveSlide((current) => (current + 1) % FEATURED_BASKETS.length)
  }
  const previousSlide = () => {
    setActiveSlide((current) =>
      current === 0 ? FEATURED_BASKETS.length - 1 : current - 1,
    )
  }
  const featuredBasket = FEATURED_BASKETS[activeSlide]
  return (
    <main className="page page-home">
      <section className="panel home-hero-panel">
        <div className="home-hero-copy">
          <p className="eyebrow">Finished Baskets</p>
          <h1>Choose your style, then build it</h1>
          <p className="page-subtitle hero-subtitle">
            Start with inspiration, personalize it, and send it in minutes.
          </p>
        </div>
        <div className="carousel-shell" aria-label="Finished basket showcase">
          <img
            key={featuredBasket.id}
            src={featuredBasket.imageUrl}
            alt={featuredBasket.title}
            className="carousel-image"
          />
          <div className="carousel-overlay">
            <h3>{featuredBasket.title}</h3>
            <p>{featuredBasket.subtitle}</p>
          </div>
          <button
            type="button"
            className="carousel-control carousel-prev"
            aria-label="Show previous basket"
            onClick={previousSlide}
          >
            ‹
          </button>
          <button
            type="button"
            className="carousel-control carousel-next"
            aria-label="Show next basket"
            onClick={nextSlide}
          >
            ›
          </button>
          <div className="carousel-dots" role="tablist" aria-label="Choose basket slide">
            {FEATURED_BASKETS.map((basket, index) => (
              <button
                key={basket.id}
                type="button"
                role="tab"
                aria-selected={activeSlide === index}
                className={activeSlide === index ? 'active' : ''}
                onClick={() => setActiveSlide(index)}
              >
                <span className="sr-only">{basket.title}</span>
              </button>
            ))}
          </div>
        </div>
      </section>
      {user?.role !== 'admin' ? (
        <section className="panel start-cta-panel">
          <p className="start-cta-subline">
            Create a premium basket your way, one simple step at a time.
          </p>
          <div className="home-action-group" style={{ display: 'flex', gap: '1rem', justifyContent: 'center', flexWrap: 'wrap' }}>
            <Link to="/builder" className="button button-pulse">
              Get Started
            </Link>
            <button 
              type="button" 
              className="button button-secondary"
              onClick={() => setShowAIBuilder(true)}
            >
              Build with AI
            </button>
          </div>
          <p className="header-stat">{statsLabel}</p>
        </section>
      ) : null}
      <section className="panel">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem', flexWrap: 'wrap', gap: '0.5rem' }}>
          <h2 style={{ margin: 0 }}>Browse Products</h2>
          {isSearchActive && (
            <button
              type="button"
              className="ghost-button"
              style={{ fontSize: '0.85rem' }}
              onClick={() => { setSearchQuery(''); setSelectedCategoryId('') }}
            >
              Clear filters
            </button>
          )}
        </div>
        <div className="product-search-bar">
          <div className="product-search-input-wrap">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="search-icon"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>
            <input
              type="search"
              placeholder="Search products..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="product-search-input"
            />
          </div>
          <select
            value={selectedCategoryId}
            onChange={(e) => setSelectedCategoryId(e.target.value)}
            className="product-category-filter"
          >
            <option value="">All Categories</option>
            {categories.map((cat) => (
              <option key={cat.id} value={cat.id}>{cat.name}</option>
            ))}
          </select>
        </div>

        {isSearching && <p className="empty-state" style={{ marginTop: '1.5rem' }}>Searching...</p>}

        {!isSearching && isSearchActive && searchResults.length === 0 && (
          <p className="empty-state" style={{ marginTop: '1.5rem' }}>No products found. Try a different search.</p>
        )}

        {!isSearching && isSearchActive && searchResults.length > 0 && (
          <>
            <p className="compact-copy" style={{ marginTop: '0.5rem', marginBottom: '1rem' }}>
              {searchResults.length} result{searchResults.length !== 1 ? 's' : ''}
            </p>
            <div className="product-browse-grid">
              {searchResults.map((product) => (
                <article key={product.id} className="product-browse-card">
                  <img
                    src={product.image_url || '/images/placeholder.png'}
                    alt={product.title}
                    className="product-browse-img"
                    loading="lazy"
                  />
                  <div className="product-browse-copy">
                    <strong>{product.title}</strong>
                    <span style={{ color: 'var(--brand-amber)', fontWeight: 600 }}>
                      {formatCurrency(product.price)}
                    </span>
                    {product.inventory_count <= 0 && (
                      <small style={{ color: 'var(--brand-coral)' }}>Out of stock</small>
                    )}
                  </div>
                  {user?.role !== 'admin' && product.inventory_count > 0 && (
                    <button
                      type="button"
                      className="button"
                      style={{ width: '100%', fontSize: '0.8rem', padding: '0.4rem' }}
                      onClick={() => navigate(`/builder?seedProductId=${product.id}`)}
                    >
                      Add to Basket
                    </button>
                  )}
                </article>
              ))}
            </div>
          </>
        )}

        {!isSearchActive && (
          <p className="empty-state" style={{ marginTop: '1rem', fontSize: '0.9rem', opacity: 0.6 }}>
            Type a product name or pick a category to browse.
          </p>
        )}
      </section>
      <section className="panel">
        <h2>Prebuilt Baskets</h2>
        <p className="compact-copy">
          Tap a basket to see details, then choose Buy Now or Customize.
        </p>
        {isLoading ? <p className="empty-state">Preparing your prebuilt options...</p> : null}
        {!isLoading && !prebuiltBaskets.length ? (
          <p className="empty-state">No prebuilt baskets are available right now.</p>
        ) : null}
        {!isLoading && prebuiltBaskets.length ? (
          <div className="prebuilt-grid">
            {prebuiltBaskets.map((prebuiltBasket) => (
              <button
                key={prebuiltBasket.id}
                type="button"
                className="prebuilt-card"
                onClick={() => setActiveBasket(prebuiltBasket)}
                aria-label={`Open ${prebuiltBasket.title} details`}
              >
                <img src={prebuiltBasket.imageUrl} alt={prebuiltBasket.title} loading="lazy" />
                <div className="prebuilt-copy">
                  <h3>{prebuiltBasket.title}</h3>
                  <p>{prebuiltBasket.teaser}</p>
                  <small>
                    {prebuiltBasket.itemCount} items · {formatCurrency(prebuiltBasket.estimatedTotal)}
                  </small>
                </div>
              </button>
            ))}
          </div>
        ) : null}
      </section>
      {activeBasket ? (
        <section
          className="prebuilt-modal-backdrop"
          role="presentation"
          onClick={() => setActiveBasket(null)}
        >
          <article
            className="panel prebuilt-detail-card"
            role="dialog"
            aria-modal="true"
            aria-label={activeBasket.title}
            onClick={(event) => event.stopPropagation()}
          >
            <button
              type="button"
              className="ghost-button prebuilt-close"
              onClick={() => setActiveBasket(null)}
            >
              Close
            </button>
            <img
              src={activeBasket.imageUrl}
              alt={activeBasket.title}
              className="prebuilt-detail-image"
            />
            <div className="prebuilt-detail-copy">
              <h2>{activeBasket.title}</h2>
              <p>{activeBasket.description}</p>
              <p className="compact-copy">
                Base: {activeBasket.baseLabel} · Estimated total:{' '}
                {formatCurrency(activeBasket.estimatedTotal)}
              </p>
              <ul className="prebuilt-item-list">
                {activeBasket.items.map((item) => (
                  <li key={`${activeBasket.id}-${item.productId}`}>
                    {item.quantity}x {item.title}
                  </li>
                ))}
              </ul>
              {user?.role !== 'admin' ? (
                <div className="form-actions">
                  <button
                    type="button"
                    className="button button-secondary"
                    onClick={() => handleCustomize(activeBasket)}
                    disabled={Boolean(busyAction)}
                  >
                    Customize
                  </button>
                  <button
                    type="button"
                    className="button"
                    onClick={() => handleBuyNow(activeBasket)}
                    disabled={Boolean(busyAction)}
                  >
                    {busyAction?.basketId === activeBasket.id && busyAction?.type === 'buy'
                      ? 'Adding...'
                      : 'Buy Now'}
                  </button>
                </div>
              ) : (
                <p className="empty-state">Admins cannot place orders.</p>
              )}
            </div>
          </article>
        </section>
      ) : null}

      <section className="panel contact-panel">
        <h2>Contact Us</h2>
        <p>Need help with a custom order or delivery request? We are here to help.</p>
        <div className="contact-grid">
          <a href="mailto:hello@diygiftsbasket.com">hello@diygiftsbasket.com</a>
          <a href="tel:+923001234567">+92 (300) 123-4567</a>
          <p>Mon-Sat: 9:00 AM - 7:00 PM</p>
        </div>
      </section>

      {showAIBuilder && (
        <div className="prebuilt-modal-backdrop" style={{ zIndex: 60 }} onClick={() => setShowAIBuilder(false)}>
          <div className="panel" style={{ width: 'min(500px, 95vw)', padding: '2rem' }} onClick={e => e.stopPropagation()}>
            <h2 style={{ marginBottom: '0.5rem' }}>✨ Build with AI</h2>
            <p style={{ marginBottom: '1.5rem', opacity: 0.8 }}>Describe who you are building for, and our AI will guide you step-by-step.</p>
            <form onSubmit={(e) => {
              e.preventDefault();
              const prompt = e.target.prompt.value;
              if (prompt.trim()) {
                navigate(`/builder?ai_prompt=${encodeURIComponent(prompt)}`);
              }
            }}>
              <textarea 
                name="prompt" 
                placeholder="e.g. I want to build a relaxation basket for my sister's birthday..." 
                rows={4}
                autoFocus
                style={{ width: '100%', marginBottom: '1.5rem' }}
              />
              <div className="form-actions">
                <button type="button" className="button button-secondary" onClick={() => setShowAIBuilder(false)}>Cancel</button>
                <button type="submit" className="button">Start Building</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </main>
  )
}