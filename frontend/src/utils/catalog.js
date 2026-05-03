const THEME_TAGS = ['Self-Care', 'Celebration', 'Cozy Night', 'Tea Time', 'Sweet Treat']

const BACKEND_ORIGIN =
  (import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1')
    .replace(/\/api\/v1\/?$/, '')

export function resolveImageUrl(url) {
  if (!url) return null
  if (url.startsWith('http://') || url.startsWith('https://')) return url
  if (url.startsWith('/images/')) return url
  return `${BACKEND_ORIGIN}${url}`
}
const PAIRING_NOTES = [
  'Pairs well with artisan tea',
  'Great with a handwritten card',
  'Best for evening unboxing',
  'Loved in birthday baskets',
  'A calm and cozy pick',
]

function seededNumber(seedSource) {
  const text = String(seedSource ?? '0')
  let hash = 0
  for (let index = 0; index < text.length; index += 1) {
    hash = (hash << 5) - hash + text.charCodeAt(index)
    hash |= 0
  }
  return Math.abs(hash)
}

export function fallbackImageForProduct(product, index = 0) {
  const seed = seededNumber(`${product?.id || ''}-${index}`) % 1000
  return `https://picsum.photos/seed/diy-gift-${seed}/640/420`
}

export function enhanceProduct(product, index = 0) {
  const seed = seededNumber(product?.id || index)
  const themeTag = THEME_TAGS[seed % THEME_TAGS.length]
  const pairingNote = PAIRING_NOTES[(seed + 2) % PAIRING_NOTES.length]

  return {
    ...product,
    image_url: resolveImageUrl(product.image_url) || fallbackImageForProduct(product, index),
    short_description:
      product.description || `${themeTag} pick with premium basket appeal.`,
    theme_tag: themeTag,
    pairing_note: pairingNote,
  }
}

export function enhanceProducts(products = []) {
  return products.map((product, index) => enhanceProduct(product, index))
}

export function enhanceBases(bases = []) {
  return bases.map((base) => ({
    ...base,
    image_url: resolveImageUrl(base.image_url) || null,
  }))
}