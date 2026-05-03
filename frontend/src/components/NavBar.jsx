import { NavLink } from 'react-router-dom'

import { useAppContext } from '../context/AppContext'

function cartCountFromCart(cart) {
  if (!cart?.items?.length) return 0
  return cart.items.reduce((sum, item) => sum + Number(item.quantity || 0), 0)
}

export function NavBar() {
  const { cart, user, logout } = useAppContext()
  const cartCount = cartCountFromCart(cart)

  return (
    <header className="app-nav-wrap">
      <nav className="app-nav">
        <NavLink to="/" className="brand-link">
          <span className="brand-badge">DIY</span>
          <span>
            Gifts Basket
            <small>Premium Custom Gifting</small>
          </span>
        </NavLink>

        <div className="nav-links">
          <NavLink to="/" end>
            Home
          </NavLink>
          {user?.role !== 'admin' ? (
            <>
              <NavLink to="/builder">Start Here</NavLink>
              <NavLink to="/cart" className="cart-link">
                Cart
                <span>{cartCount}</span>
              </NavLink>
              {user ? <NavLink to="/orders">Orders</NavLink> : null}
            </>
          ) : null}
          {user?.role === 'admin' ? <NavLink to="/admin">Admin</NavLink> : null}
          {user ? <NavLink to="/account">Profile</NavLink> : <NavLink to="/auth">Sign In</NavLink>}
          {user ? (
            <button type="button" onClick={logout} className="ghost-button">
              Logout
            </button>
          ) : null}
        </div>
      </nav>
    </header>
  )
}