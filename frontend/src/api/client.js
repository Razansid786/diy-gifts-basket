const DEFAULT_API_BASE_URL = 'http://localhost:8000/api/v1'
const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL || DEFAULT_API_BASE_URL).replace(/\/$/, '')

function buildUrl(path, query = {}) {
  const url = new URL(`${API_BASE_URL}${path}`)
  Object.entries(query).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== '') {
      url.searchParams.set(key, value)
    }
  })
  return url.toString()
}

async function readJsonSafe(response) {
  try {
    return await response.json()
  } catch {
    return null
  }
}

async function request(path, options = {}) {
  const { method = 'GET', token, sessionId, body, query, isFormData = false } = options
  const headers = { Accept: 'application/json' }

  if (token) headers.Authorization = `Bearer ${token}`
  if (sessionId) headers['X-Session-ID'] = sessionId
  if (!isFormData) headers['Content-Type'] = 'application/json'

  const response = await fetch(buildUrl(path, query), {
    method,
    headers,
    body: isFormData ? body : body ? JSON.stringify(body) : undefined,
  })

  if (!response.ok) {
    if (response.status === 401 && token) {
      if (typeof window !== 'undefined') window.dispatchEvent(new CustomEvent('auth:expired'))
    }
    const errorPayload = await readJsonSafe(response)
    const detail = errorPayload?.detail || errorPayload?.message || `Error: ${response.status}`
    const error = new Error(detail)
    error.status = response.status
    throw error
  }

  if (response.status === 204) return null
  const contentType = response.headers.get('content-type')
  if (contentType && contentType.includes('application/json')) return response.json()
  return response.text()
}

export const apiClient = {
  getApiBaseUrl() { return API_BASE_URL },

  register(payload) { return request('/auth/register', { method: 'POST', body: payload }) },
  login(payload) { return request('/auth/login', { method: 'POST', body: payload }) },
  createGuestSession() { return request('/auth/guest', { method: 'POST' }) },
  forgotPassword(payload) { return request('/auth/forgot-password', { method: 'POST', body: payload }) },
  resetPassword(payload) { return request('/auth/reset-password', { method: 'POST', body: payload }) },

  getMe(token) { return request('/users/me', { token }) },
  updateMe(payload, token) { return request('/users/me', { method: 'PUT', body: payload, token }) },

  listProducts(params = {}) { return request('/products/', { query: { skip: params.skip, limit: params.limit } }) },
  searchProducts(params = {}) {
    return request('/products/search', {
      query: {
        q: params.q,
        category_id: params.categoryId,
        min_price: params.minPrice,
        max_price: params.maxPrice,
        in_stock_only: params.inStockOnly,
        skip: params.skip,
        limit: params.limit,
      },
    })
  },
  getProduct(productId) { return request(`/products/${productId}`) },
  getRelatedProducts(productId) { return request(`/products/${productId}/related`) },
  listCategories(params = {}) { return request('/categories/', { query: { skip: params.skip, limit: params.limit } }) },
  listBases() { return request('/baskets/bases') },

  createBasket(payload, { token, sessionId } = {}) { return request('/baskets/', { method: 'POST', body: payload, token, sessionId }) },
  setBasketBase(basketId, payload, { token, sessionId } = {}) { return request(`/baskets/${basketId}/base`, { method: 'PUT', body: payload, token, sessionId }) },
  addBasketItem(basketId, payload, { token, sessionId } = {}) { return request(`/baskets/${basketId}/items`, { method: 'POST', body: payload, token, sessionId }) },
  syncBasketItems(basketId, payload, { token, sessionId } = {}) { return request(`/baskets/${basketId}/items/sync`, { method: 'PUT', body: payload, token, sessionId }) },
  removeBasketItem(basketId, itemId, { token, sessionId } = {}) { return request(`/baskets/${basketId}/items/${itemId}`, { method: 'DELETE', token, sessionId }) },
  getBasketSummary(basketId, { token, sessionId } = {}) { return request(`/baskets/${basketId}/summary`, { token, sessionId }) },
  completeBasket(basketId, { token, sessionId } = {}) { return request(`/baskets/${basketId}/complete`, { method: 'POST', token, sessionId }) },
  completeAndAddToCart(basketId, payload, { token, sessionId } = {}) { return request(`/baskets/${basketId}/complete-and-cart`, { method: 'POST', body: payload, token, sessionId }) },
  quickBuy(payload, { token, sessionId } = {}) { return request('/baskets/quick-buy', { method: 'POST', body: payload, token, sessionId }) },

  getPersonalization(basketId, { token, sessionId } = {}) { return request(`/baskets/${basketId}/personalization/`, { token, sessionId }) },
  upsertPersonalization(basketId, payload, { token, sessionId } = {}) { return request(`/baskets/${basketId}/personalization/`, { method: 'PUT', body: payload, token, sessionId }) },
  uploadGiftTag(basketId, file, { token, sessionId } = {}) {
    const formData = new FormData()
    formData.append('file', file)
    return request(`/baskets/${basketId}/personalization/upload`, { method: 'POST', body: formData, token, sessionId, isFormData: true })
  },

  getCart({ token, sessionId } = {}) { return request('/cart/', { token, sessionId }) },
  addCartItem(payload, { token, sessionId } = {}) { return request('/cart/items', { method: 'POST', body: payload, token, sessionId }) },
  updateCartItem(itemId, payload, { token, sessionId } = {}) { return request(`/cart/items/${itemId}`, { method: 'PUT', body: payload, token, sessionId }) },
  removeCartItem(itemId, { token, sessionId } = {}) { return request(`/cart/items/${itemId}`, { method: 'DELETE', token, sessionId }) },

  listAddresses(token) { return request('/addresses/', { token }) },
  createAddress(payload, token) { return request('/addresses/', { method: 'POST', body: payload, token }) },
  updateAddress(addressId, payload, token) { return request(`/addresses/${addressId}`, { method: 'PUT', body: payload, token }) },
  deleteAddress(addressId, token) { return request(`/addresses/${addressId}`, { method: 'DELETE', token }) },

  checkout(payload, { token, sessionId } = {}) { return request('/orders/checkout', { method: 'POST', body: payload, token, sessionId }) },
  listOrders(token) { return request('/orders/', { token }) },
  getOrder(orderId, token) { return request(`/orders/${orderId}`, { token }) },

  async getChatHistory(token) { return request('/chat/history', { token }) },
  async markChatRead(token) { return request('/chat/read', { method: 'POST', token }) },
  async getAdminRooms(token) { return request('/chat/admin/rooms', { token }) },
  async getAdminRoomMessages(roomId, token) { return request(`/chat/admin/rooms/${roomId}/messages`, { token }) },
  async markAdminChatRead(roomId, token) { return request(`/chat/admin/rooms/${roomId}/read`, { method: 'POST', token }) },

  adminCreateProduct(payload, token) { return request('/admin/products', { method: 'POST', body: payload, token }) },
  adminUpdateProduct(productId, payload, token) { return request(`/admin/products/${productId}`, { method: 'PUT', body: payload, token }) },
  adminCreateCategory(payload, token) { return request('/admin/categories', { method: 'POST', body: payload, token }) },
  adminUpdateCategory(categoryId, payload, token) { return request(`/admin/categories/${categoryId}`, { method: 'PUT', body: payload, token }) },
  adminCreateBase(payload, token) { return request('/admin/bases', { method: 'POST', body: payload, token }) },
  adminListOrders(params = {}, token) { return request('/admin/orders', { token, query: { skip: params.skip, limit: params.limit } }) },
  adminGetPackingList(orderId, token) { return request(`/admin/orders/${orderId}/packing-list`, { token }) },
  adminUpdateOrderStatus(orderId, payload, token) { return request(`/admin/orders/${orderId}/status`, { method: 'PUT', body: payload, token }) },

  async uploadImage(file, token) {
    const formData = new FormData()
    formData.append('file', file)
    const result = await request('/images/', { method: 'POST', body: formData, token })
    if (result?.url && result.url.startsWith('/')) {
      const backendOrigin = API_BASE_URL.replace(/\/api\/v1\/?$/, '')
      result.url = `${backendOrigin}${result.url}`
    }
    return result
  },

  post(path, body, options = {}) { return request(path, { method: 'POST', body, ...options }) },
  get(path, options = {}) { return request(path, { method: 'GET', ...options }) },
  put(path, body, options = {}) { return request(path, { method: 'PUT', body, ...options }) },
  delete(path, options = {}) { return request(path, { method: 'DELETE', ...options }) },
}