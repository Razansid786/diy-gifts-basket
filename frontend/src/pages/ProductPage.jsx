import { Link, useParams } from 'react-router-dom'
import { useEffect, useState } from 'react'

import { apiClient } from '../api/client'
import { PageHeader } from '../components/PageHeader'
import { ProductCard } from '../components/ProductCard'
import { useAppContext } from '../context/AppContext'
import { enhanceProduct, enhanceProducts } from '../utils/catalog'
import { formatCurrency } from '../utils/format'

export function ProductPage() {
  const { productId } = useParams()
  const { pushToast } = useAppContext()

  const [product, setProduct] = useState(null)
  const [relatedProducts, setRelatedProducts] = useState([])
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    let isMounted = true

    async function loadProductDetails() {
      setIsLoading(true)
      try {

        const [productData, relatedData] = await Promise.all([
          apiClient.getProduct(productId),
          apiClient.getRelatedProducts(productId),
        ])

        if (!isMounted) return
        setProduct(enhanceProduct(productData))
        setRelatedProducts(enhanceProducts(relatedData))
      } catch (error) {
        pushToast(error.message || 'Unable to load product details.', 'error')
      } finally {
        if (isMounted) setIsLoading(false)
      }
    }

    loadProductDetails()

    return () => {
      isMounted = false
    }
  }, [productId, pushToast])

  return (
    <main className="page page-product">
      {isLoading ? <p className="empty-state">Loading product details...</p> : null}

      {!isLoading && product ? (
        <>
          <PageHeader
            eyebrow="Product Detail"
            title={product.title}
            subtitle={product.short_description}
            actions={
              <div className="inline-actions">
                <span className="price-highlight">{formatCurrency(product.price)}</span>
                <Link to={`/builder?seedProductId=${product.id}`} className="button">
                  Start with this item
                </Link>
              </div>
            }
          />

          <section className="panel product-detail-panel">
            <div className="detail-image-wrap">
              {product.image_url ? (
                <img src={product.image_url} alt={product.title} className="detail-image" />
              ) : (
                <div className="product-image-fallback detail-fallback">No image available</div>
              )}
            </div>

            <div className="detail-copy">
              <p>
                <strong>Style:</strong> {product.theme_tag}
              </p>
              <p>
                <strong>Pairing note:</strong> {product.pairing_note}
              </p>
              <p>
                <strong>Inventory:</strong>{' '}
                {product.is_sold_out ? 'Sold out' : `${product.inventory_count} available`}
              </p>
            </div>
          </section>

          <section className="section-block">
            <h2>Related products</h2>
            {relatedProducts.length === 0 ? (
              <p className="empty-state">No related products configured for this item yet.</p>
            ) : (
              <div className="product-grid compact-grid">
                {relatedProducts.map((item) => (
                  <ProductCard key={item.id} product={item} />
                ))}
              </div>
            )}
          </section>
        </>
      ) : null}
    </main>
  )
}