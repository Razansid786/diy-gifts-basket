const PREBUILT_BLUEPRINTS = [
  {
    id: 'birthday-bliss',
    title: 'Birthday Bliss Basket',
    teaser: 'Sweet bites, sparkle, and a celebratory touch.',
    description:
      'A vibrant birthday-ready basket with premium snacks and celebration extras. Great when you want to send a complete gift in one click.',
    imageUrl: '/images/prebuilt/Birthday Bliss Basket.jpg',
    baseKeywords: ['willow'],
    items: [
      { keywords: ['dark', 'chocolate'], quantity: 1 },
      { keywords: ['sparkling', 'grape'], quantity: 1 },
      { keywords: ['greeting', 'card'], quantity: 1 },
    ],
    personalization: {
      gift_message: 'Happy Birthday! Wishing you joy and sweet moments.',
      ribbon_color: 'Ruby Red',
    },
  },
  {
    id: 'cozy-evening',
    title: 'Cozy Evening Basket',
    teaser: 'Tea-time comfort with cozy-night favorites.',
    description:
      'Built for relaxed evenings with warm drinks and comforting treats. This one is ideal for thank-you gifts and self-care moments.',
    imageUrl: '/images/prebuilt/Cozy Evening Basket.jpg',
    baseKeywords: ['magnetic'],
    items: [
      { keywords: ['earl', 'grey'], quantity: 1 },
      { keywords: ['caramel', 'cookies'], quantity: 1 },
      { keywords: ['candle'], quantity: 1 },
    ],
    personalization: {
      gift_message: 'A cozy moment just for you.',
      ribbon_color: 'Ivory Pearl',
    },
  },
  {
    id: 'wellness-reset',
    title: 'Wellness Reset Basket',
    teaser: 'Spa-inspired picks for a calm reset.',
    description:
      'A gentle wellness combination with bath and body favorites, paired with a calming drink option for a complete unwind.',
    imageUrl: '/images/prebuilt/Wellnes Reset Basket.jpg',
    baseKeywords: ['kraft'],
    items: [
      { keywords: ['lavender', 'bath'], quantity: 1 },
      { keywords: ['hand', 'cream'], quantity: 1 },
      { keywords: ['chamomile'], quantity: 1 },
    ],
    personalization: {
      gift_message: 'Take a pause and enjoy this reset.',
      ribbon_color: 'Ocean Teal',
    },
  },
  {
    id: 'coffee-crate',
    title: 'Coffee Break Basket',
    teaser: 'A richer flavor profile with premium pairings.',
    description:
      'A practical and stylish prebuilt basket for coffee lovers, designed with balanced flavors and easy gifting appeal.',
    imageUrl: '/images/prebuilt/Coffee Break Basket.jpg',
    baseKeywords: ['willow'],
    items: [
      { keywords: ['single-origin', 'coffee'], quantity: 1 },
      { keywords: ['trail', 'mix'], quantity: 1 },
      { keywords: ['chocolate'], quantity: 1 },
    ],
    personalization: {
      gift_message: 'Enjoy every sip and bite.',
      ribbon_color: 'Saffron Gold',
    },
  },
  {
    id: 'signature-mix',
    title: 'Signature Mix Basket',
    teaser: 'Balanced best-sellers from multiple categories.',
    description:
      'A versatile gift basket that mixes crowd favorites from snacks, self-care, and celebration essentials.',
    imageUrl: '/images/prebuilt/Signature Mix Basket.jpg',
    baseKeywords: ['magnetic'],
    items: [
      { keywords: ['trail', 'mix'], quantity: 1 },
      { keywords: ['sparkling', 'grape'], quantity: 1 },
      { keywords: ['hand', 'cream'], quantity: 1 },
    ],
    personalization: {
      gift_message: 'A little something premium, just for you.',
      ribbon_color: 'Ruby Red',
    },
  },
]

function includesAllKeywords(value, keywords) {
  if (!keywords?.length) return false
  const normalized = value.toLowerCase()
  return keywords.every((keyword) => normalized.includes(keyword.toLowerCase()))
}

function findBaseForBlueprint(bases, baseKeywords = []) {
  if (!bases.length) return null

  if (!baseKeywords.length) {
    return bases[0]
  }

  const matched = bases.find((base) =>
    baseKeywords.every((keyword) => base.name.toLowerCase().includes(keyword.toLowerCase())),
  )

  return matched || bases[0]
}

function resolveItemsForBlueprint(products, itemBlueprints = []) {
  if (!products.length) return []

  const usedProductIds = new Set()
  let fallbackIndex = 0

  const resolveNextFallback = () => {
    while (fallbackIndex < products.length) {
      const candidate = products[fallbackIndex]
      fallbackIndex += 1
      if (!usedProductIds.has(candidate.id)) {
        return candidate
      }
    }
    return null
  }

  const resolved = itemBlueprints
    .map((blueprintItem) => {
      const matcher = products.find((product) => {
        if (usedProductIds.has(product.id)) return false
        return includesAllKeywords(
          `${product.title || ''} ${product.description || ''}`,
          blueprintItem.keywords,
        )
      })

      const chosen = matcher || resolveNextFallback()
      if (!chosen) return null

      usedProductIds.add(chosen.id)
      return {
        productId: chosen.id,
        title: chosen.title,
        quantity: Number(blueprintItem.quantity || 1),
        unitPrice: Number(chosen.price || 0),
      }
    })
    .filter(Boolean)

  while (resolved.length < 2) {
    const fallback = resolveNextFallback()
    if (!fallback) break
    usedProductIds.add(fallback.id)
    resolved.push({
      productId: fallback.id,
      title: fallback.title,
      quantity: 1,
      unitPrice: Number(fallback.price || 0),
    })
  }

  return resolved
}

export function buildPrebuiltBaskets(products = [], bases = []) {
  if (!products.length || !bases.length) return []

  const availableProducts = products.filter(
    (product) => Number(product.inventory_count || 0) > 0,
  )
  const sourceProducts = availableProducts.length ? availableProducts : products

  return PREBUILT_BLUEPRINTS.map((blueprint) => {
    const base = findBaseForBlueprint(bases, blueprint.baseKeywords)
    const items = resolveItemsForBlueprint(sourceProducts, blueprint.items)

    if (!base || !items.length) {
      return null
    }

    const itemCount = items.reduce((sum, item) => sum + item.quantity, 0)
    const estimatedSubtotal = items.reduce(
      (sum, item) => sum + item.unitPrice * item.quantity,
      0,
    )

    return {
      id: blueprint.id,
      title: blueprint.title,
      teaser: blueprint.teaser,
      description: blueprint.description,
      imageUrl: blueprint.imageUrl,
      baseId: base.id,
      baseLabel: `${base.name} (${base.size})`,
      basePrice: Number(base.price || 0),
      items,
      itemCount,
      estimatedTotal: estimatedSubtotal + Number(base.price || 0),
      personalization: blueprint.personalization,
    }
  })
    .filter(Boolean)
    .slice(0, 5)
}