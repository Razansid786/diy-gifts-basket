import { Link } from 'react-router-dom'

import { formatCurrency } from '../utils/format'

export function ProductCard({ product }) {
  return (
    <article className="product-card">
      <div className="product-image-wrap">
        <img src={product.image_url} alt={product.title} loading="lazy" />
      </div>

      <div className="product-copy">
        <h3>{product.title}</h3>
        <p>{product.short_description}</p>
      </div>

      <div className="product-tags" aria-label="Product style tags">
        <span className="pill subtle-pill">{product.theme_tag}</span>
        <span className="pill subtle-pill">{product.pairing_note}</span>
      </div>

      <div className="product-meta">
        <strong>{formatCurrency(product.price)}</strong>
        <span className={product.is_sold_out ? 'pill sold-out' : 'pill in-stock'}>
          {product.is_sold_out ? 'Sold out' : `In stock: ${product.inventory_count}`}
        </span>
      </div>

      <div className="product-actions">
        <Link to={`/products/${product.id}`} className="button button-secondary">
          Details
        </Link>
        <Link to={`/builder?seedProductId=${product.id}`} className="button">
          Build Basket
        </Link>
      </div>
    </article>
  )
}