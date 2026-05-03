import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { apiClient } from '../api/client'
import { PageHeader } from '../components/PageHeader'
import { useAppContext } from '../context/AppContext'
import { enhanceProducts, enhanceBases } from '../utils/catalog'
import { formatCurrency, formatDate } from '../utils/format'
import { AIBuilderChat } from '../components/AIBuilderChat'

const EMPTY_PERSONALIZATION = {
  gift_message: '',
  ribbon_color: '',
  requested_delivery_date: '',
}

function parsePrefillPayload(rawPrefill) {
  if (!rawPrefill) return null
  let parsed
  try {
    parsed = JSON.parse(decodeURIComponent(rawPrefill))
  } catch {
    return null
  }
  if (!parsed || typeof parsed !== 'object') return null
  const normalizedItems = Array.isArray(parsed.items)
    ? parsed.items
      .map((item) => ({ productId: item?.productId, quantity: Number(item?.quantity || 1) }))
      .filter((item) => item.productId && item.quantity > 0)
    : []
  return {
    baseId: parsed.baseId || '',
    items: normalizedItems,
    personalization: {
      gift_message: parsed.personalization?.gift_message || '',
      ribbon_color: parsed.personalization?.ribbon_color || '',
      requested_delivery_date: parsed.personalization?.requested_delivery_date || '',
    },
  }
}

function clampQuantity(quantity, max) {
  if (!Number.isFinite(quantity) || quantity <= 0) return 0
  return Math.min(Math.floor(quantity), Math.max(1, max || 1))
}

export function BasketBuilderPage() {
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const { token, sessionId, ensureGuestSession, refreshCart, pushToast } = useAppContext()

  const seededProductId = searchParams.get('seedProductId') || ''
  const prefillTemplate = useMemo(() => parsePrefillPayload(searchParams.get('prefill')), [searchParams])
  const hasAppliedPrefill = useRef(false)

  const [bases, setBases] = useState([])
  const [products, setProducts] = useState([])
  const [basket, setBasket] = useState(null)
  const [personalization, setPersonalization] = useState(null)
  const [selectedBaseId, setSelectedBaseId] = useState('')
  const [selectedQuantities, setSelectedQuantities] = useState({})
  const [personalizationForm, setPersonalizationForm] = useState(EMPTY_PERSONALIZATION)
  const [isInitializing, setIsInitializing] = useState(true)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [uploadingTag, setUploadingTag] = useState(false)
  const [currentStep, setCurrentStep] = useState(1)
  const [showAI, setShowAI] = useState(Boolean(searchParams.get('ai_prompt')))
  const aiPrompt = searchParams.get('ai_prompt')

  const productMap = useMemo(() => new Map(products.map((p) => [p.id, p])), [products])

  const selectedItemsPreview = useMemo(() =>
    Object.entries(selectedQuantities)
      .map(([id, qty]) => {
        const p = productMap.get(id)
        return p && qty > 0 ? { productId: id, quantity: qty, product: p } : null
      }).filter(Boolean),
    [selectedQuantities, productMap]
  )

  const selectedItemsCount = useMemo(() => selectedItemsPreview.reduce((s, i) => s + i.quantity, 0), [selectedItemsPreview])
  const hasItems = Boolean(basket?.items?.length)
  const hasPersonalization = Boolean(personalization?.gift_message) || Boolean(personalization?.ribbon_color) || Boolean(personalization?.requested_delivery_date) || Boolean(personalization?.gift_tag_image_url)
  const hasDraftPersonalization = Boolean(personalizationForm.gift_message) || Boolean(personalizationForm.ribbon_color) || Boolean(personalizationForm.requested_delivery_date)

  const maxStep = useMemo(() => {
    if (hasPersonalization || hasDraftPersonalization || currentStep >= 4) return 4
    if (hasItems) return 3
    if (basket) return 2
    return 1
  }, [basket, hasItems, hasPersonalization, hasDraftPersonalization, currentStep])

  const resolveAuthMeta = useCallback(async () => {
    let activeSessionId = sessionId
    if (!token && !activeSessionId) activeSessionId = await ensureGuestSession()
    return { token, sessionId: activeSessionId }
  }, [token, sessionId, ensureGuestSession])

  const loadCatalog = useCallback(async () => {
    setIsInitializing(true)
    hasAppliedPrefill.current = false
    try {
      const [baseData, productData] = await Promise.all([apiClient.listBases(), apiClient.listProducts({ limit: 100 })])
      setBases(enhanceBases(baseData))
      setProducts(enhanceProducts(productData))
    } catch (error) {
      pushToast(error.message || 'Unable to load builder options.', 'error')
    } finally {
      setIsInitializing(false)
    }
  }, [pushToast])

  useEffect(() => { loadCatalog() }, [loadCatalog])

  useEffect(() => {
    if (!seededProductId || prefillTemplate) return
    setSelectedQuantities(c => c[seededProductId] ? c : { ...c, [seededProductId]: 1 })
  }, [seededProductId, prefillTemplate])

  const syncPersonalization = useCallback(async (basketId) => {
    try {
      const meta = await resolveAuthMeta()
      const data = await apiClient.getPersonalization(basketId, meta)
      setPersonalization(data)
      setPersonalizationForm({
        gift_message: data.gift_message || '',
        ribbon_color: data.ribbon_color || '',
        requested_delivery_date: data.requested_delivery_date || '',
      })
    } catch {
      setPersonalization(null)
      setPersonalizationForm(EMPTY_PERSONALIZATION)
    }
  }, [resolveAuthMeta])

  const ensureBasketWithBase = useCallback(async () => {
    if (!selectedBaseId) {
      pushToast('Select a base container first.', 'info')
      return null
    }
    const meta = await resolveAuthMeta()
    if (!basket) {
      const created = await apiClient.createBasket({ base_id: selectedBaseId, session_id: meta.token ? undefined : meta.sessionId }, meta)
      setBasket(created)
      return created
    }
    if (basket.base?.id === selectedBaseId) return basket
    const updated = await apiClient.setBasketBase(basket.id, { base_id: selectedBaseId }, meta)
    setBasket(updated)
    return updated
  }, [selectedBaseId, pushToast, resolveAuthMeta, basket])

  const setProductQuantity = useCallback((productId, nextQuantity) => {
    const product = productMap.get(productId)
    if (!product) return
    const maxStock = Number(product.inventory_count || 0)
    const safeQuantity = clampQuantity(Number(nextQuantity), maxStock)
    setSelectedQuantities(current => {
      if (safeQuantity <= 0) {
        const next = { ...current }; delete next[productId]; return next
      }
      return { ...current, [productId]: safeQuantity }
    })
  }, [productMap])

  useEffect(() => {
    if (isInitializing || !prefillTemplate || hasAppliedPrefill.current) return
    hasAppliedPrefill.current = true
    async function applyPrefill() {
      setIsSubmitting(true)
      try {
        const meta = await resolveAuthMeta()
        const created = await apiClient.createBasket({ base_id: prefillTemplate.baseId || undefined, session_id: meta.token ? undefined : meta.sessionId }, meta)
        const nextQuantities = {}
        prefillTemplate.items.forEach(item => {
          const p = productMap.get(item.productId)
          if (p) nextQuantities[item.productId] = clampQuantity(item.quantity, Number(p.inventory_count || 0))
        })
        const itemsToSync = Object.entries(nextQuantities).map(([id, qty]) => ({ product_id: id, quantity: qty }))
        const workingBasket = itemsToSync.length ? await apiClient.syncBasketItems(created.id, { items: itemsToSync }, meta) : created
        setSelectedQuantities(nextQuantities)
        if (prefillTemplate.personalization) {
          const p = await apiClient.upsertPersonalization(created.id, {
            gift_message: prefillTemplate.personalization.gift_message || null,
            ribbon_color: prefillTemplate.personalization.ribbon_color || null,
            requested_delivery_date: prefillTemplate.personalization.requested_delivery_date || null,
          }, meta)
          setPersonalization(p)
          setPersonalizationForm({ gift_message: p.gift_message || '', ribbon_color: p.ribbon_color || '', requested_delivery_date: p.requested_delivery_date || '' })
        }
        setBasket(workingBasket)
        setSelectedBaseId(workingBasket.base?.id || prefillTemplate.baseId)
        setCurrentStep(2)
        pushToast('Template loaded.', 'success')
      } catch (e) { pushToast(e.message || 'Error loading template.', 'error') }
      finally { setIsSubmitting(false) }
    }
    applyPrefill()
  }, [isInitializing, prefillTemplate, resolveAuthMeta, productMap, pushToast])

  const handleBaseNext = () => {
    if (!selectedBaseId) return pushToast('Select a base first.', 'info')
    setCurrentStep(2)
  }

  const applySelectedProducts = useCallback(async () => {
    const items = selectedItemsPreview.map(i => ({ product_id: i.productId, quantity: i.quantity }))
    if (!items.length) return pushToast('Select items first.', 'info')
    const readyBasket = await ensureBasketWithBase()
    if (!readyBasket) return false
    const meta = await resolveAuthMeta()
    const updated = await apiClient.syncBasketItems(readyBasket.id, { items }, meta)
    setBasket(updated)
    return true
  }, [selectedItemsPreview, ensureBasketWithBase, resolveAuthMeta, pushToast])

  const handleProductsNext = async () => {
    setIsSubmitting(true)
    try { if (await applySelectedProducts()) setCurrentStep(3) }
    catch (e) { pushToast(e.message || 'Error saving items.', 'error') }
    finally { setIsSubmitting(false) }
  }

  const savePersonalization = (e) => {
    e.preventDefault()
    if (!basket?.items?.length) return setCurrentStep(2)
    setCurrentStep(4)
  }

  const uploadGiftTag = async (e) => {
    const file = e.target.files?.[0]
    if (!file) return
    setUploadingTag(true)
    try {
      const ready = await ensureBasketWithBase()
      if (ready) {
        const meta = await resolveAuthMeta()
        const updated = await apiClient.uploadGiftTag(ready.id, file, meta)
        setPersonalization(updated)
      }
    } catch (e) { pushToast(e.message || 'Upload failed.', 'error') }
    finally { setUploadingTag(false); e.target.value = '' }
  }

  const completeAndAddToCart = async () => {
    if (!basket) return
    setIsSubmitting(true)
    try {
      const meta = await resolveAuthMeta()
      const payload = { personalization: { gift_message: personalizationForm.gift_message || null, ribbon_color: personalizationForm.ribbon_color || null, requested_delivery_date: personalizationForm.requested_delivery_date || null } }
      await apiClient.completeAndAddToCart(basket.id, payload, meta)
      await refreshCart()
      navigate('/cart')
    } catch (e) { pushToast(e.message || 'Error finalizing build.', 'error') }
    finally { setIsSubmitting(false) }
  }

  const basketItemsForReview = useMemo(() =>
    (basket?.items || []).map(i => ({ id: i.id, quantity: i.quantity, title: productMap.get(i.product_id)?.title || i.product_id })),
    [basket, productMap]
  )

  const totalItems = useMemo(() => (basket?.items || []).reduce((s, i) => s + Number(i.quantity || 0), 0), [basket])

  return (
    <main className="page page-builder">
      <PageHeader
        eyebrow="Custom Gift"
        title="Create your unique basket"
        subtitle="Follow the steps to build, personalize, and review your custom gift."
      />

      <div className="builder-layout-container">
        {showAI && (
          <div className="ai-side-chat-wrapper">
            <AIBuilderChat
              isOpen={showAI}
              onClose={() => setShowAI(false)}
              initialMessage={aiPrompt}
              context={{
                currentStep,
                selectedBaseId,
                selectedProductIds: Object.keys(selectedQuantities)
              }}
              onSelectBase={(base) => {
                setSelectedBaseId(base.id)
                setCurrentStep(2)
                pushToast(`Base ${base.name} selected!`, 'success')
              }}
              onAddProduct={(p) => {
                setProductQuantity(p.id, (selectedQuantities[p.id] || 0) + 1)
                pushToast(`${p.title} added to selection.`, 'success')
              }}
            />
          </div>
        )}
        <div className="builder-main-content">
          {isInitializing ? <p className="empty-state">Loading...</p> : (
            <>
              <section className="panel stepper-panel">
                <div className="stepper">
                  {[{ n: 1, l: 'Base' }, { n: 2, l: 'Products' }, { n: 3, l: 'Personalize' }, { n: 4, l: 'Review' }].map(s => (
                    <button key={s.n} className={`step-dot ${currentStep === s.n ? 'active' : ''}`} disabled={s.n > maxStep} onClick={() => setCurrentStep(s.n)}>
                      <span>{s.n}</span>{s.l}
                    </button>
                  ))}
                </div>
              </section>

              {currentStep === 1 && (
                <section className="panel">
                  <h2>Choose a base</h2>
                  <div className="base-choice-grid">
                    {bases.map(b => (
                      <button key={b.id} className={`base-choice-card ${selectedBaseId === b.id ? 'selected' : ''}`} onClick={() => setSelectedBaseId(b.id)}>
                        <img src={b.image_url} alt={b.name} /><div className="base-choice-copy"><h3>{b.name}</h3><p>Size {b.size} · Max {b.max_items} items</p><strong>{formatCurrency(b.price)}</strong></div>
                      </button>
                    ))}
                  </div>
                  <div className="form-actions"><button className="button" onClick={handleBaseNext}>Next</button></div>
                </section>
              )}

              {currentStep === 2 && (
                <section className="panel">
                  <h2>Add items</h2>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <p className="header-stat">Items selected: {selectedItemsCount}</p>
                  </div>
                  <div className="builder-product-grid">
                    {products.filter(p => !p.is_sold_out).slice(0, 24).map(p => {
                      const q = selectedQuantities[p.id] || 0
                      return (
                        <article key={p.id} className={`builder-product-card ${q > 0 ? 'selected' : ''}`}>
                          <img src={p.image_url} alt={p.title} /><strong>{p.title}</strong><span>{formatCurrency(p.price)} · Stock {p.inventory_count}</span>
                          <div className="quantity-controls">
                            <button className="ghost-button" onClick={() => setProductQuantity(p.id, q - 1)}>-</button>
                            <input type="number" min="0" value={q} onChange={e => setProductQuantity(p.id, Number(e.target.value || 0))} />
                            <button className="ghost-button" onClick={() => setProductQuantity(p.id, q + 1)}>+</button>
                          </div>
                        </article>
                      )
                    })}
                  </div>
                  <div className="form-actions"><button className="button button-secondary" onClick={() => setCurrentStep(1)}>Back</button><button className="button" onClick={handleProductsNext}>Next</button></div>
                </section>
              )}

              {currentStep === 3 && (
                <section className="panel">
                  <h2>Personalize</h2>
                  <form className="stack-form" onSubmit={savePersonalization}>
                    <label>Gift message<textarea rows={3} value={personalizationForm.gift_message} onChange={e => setPersonalizationForm(c => ({ ...c, gift_message: e.target.value }))} /></label>
                    <div className="inline-grid">
                      <label>Ribbon<select value={personalizationForm.ribbon_color} onChange={e => setPersonalizationForm(c => ({ ...c, ribbon_color: e.target.value }))}><option value="">None</option><option value="Ruby Red">Ruby Red</option><option value="Saffron Gold">Saffron Gold</option><option value="Ocean Teal">Ocean Teal</option><option value="Ivory Pearl">Ivory Pearl</option></select></label>
                      <label>Date<input type="date" value={personalizationForm.requested_delivery_date} onChange={e => setPersonalizationForm(c => ({ ...c, requested_delivery_date: e.target.value }))} /></label>
                    </div>
                    <label>Custom tag<input type="file" accept="image/*" onChange={uploadGiftTag} disabled={uploadingTag} /></label>
                    {personalization?.gift_tag_image_url && <div className="tag-preview-wrap"><img src={personalization.gift_tag_image_url} alt="Tag" className="gift-tag-preview" /></div>}
                    <div className="form-actions"><button className="button button-secondary" onClick={() => setCurrentStep(2)}>Back</button><button type="submit" className="button">Next</button></div>
                  </form>
                </section>
              )}

              {currentStep === 4 && (
                <section className="panel">
                  <h2>Review</h2>
                  {basket && (
                    <>
                      <div className="summary-grid"><p><strong>Base:</strong> {basket.base?.name}</p><p><strong>Items:</strong> {totalItems}</p><p><strong>Total:</strong> {formatCurrency(basket.running_total)}</p><p><strong>Date:</strong> {formatDate(personalization?.requested_delivery_date)}</p></div>
                      <div className="stack-list">{basketItemsForReview.map(i => <article key={i.id} className="list-row"><div><strong>{i.title}</strong><p>Qty: {i.quantity}</p></div></article>)}</div>
                      <div className="form-actions"><button className="button button-secondary" onClick={() => setCurrentStep(2)}>Edit items</button><button className="button" onClick={completeAndAddToCart}>Add to cart</button></div>
                    </>
                  )}
                </section>
              )}
            </>
          )}
        </div>
      </div>

      {!showAI && (
        <button 
          type="button" 
          className="ai-open-fab" 
          onClick={() => setShowAI(true)}
        >
          ✨ AI Assistant
        </button>
      )}
    </main>
  )
}