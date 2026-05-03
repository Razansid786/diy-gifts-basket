import { useCallback, useEffect, useMemo, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'

import { apiClient } from '../api/client'
import { PageHeader } from '../components/PageHeader'
import { useAppContext } from '../context/AppContext'
import { formatCurrency, formatDate } from '../utils/format'

const EMPTY_ADDRESS = {
  label: 'Home',
  line1: '',
  line2: '',
  city: '',
  state: '',
  zip_code: '',
  country: 'US',
  is_default: false,
}

export function AccountPage() {
  const navigate = useNavigate()
  const { token, user, refreshUser, pushToast } = useAppContext()

  const [profileForm, setProfileForm] = useState({ full_name: '', email: '' })
  const [addresses, setAddresses] = useState([])
  const [orders, setOrders] = useState([])
  const [addressForm, setAddressForm] = useState(EMPTY_ADDRESS)
  const [editingAddressId, setEditingAddressId] = useState(null)
  const [isLoading, setIsLoading] = useState(false)
  const [profileNotice, setProfileNotice] = useState('')
  const [addressNotice, setAddressNotice] = useState('')

  useEffect(() => {
    if (!user) return
    setProfileForm({
      full_name: user.full_name || '',
      email: user.email || '',
    })
  }, [user])

  const loadAccountData = useCallback(async () => {
    if (!token) return

    setIsLoading(true)
    try {
      const [addressData, orderData] = await Promise.all([
        apiClient.listAddresses(token),
        apiClient.listOrders(token),
      ])
      setAddresses(addressData)
      setOrders(orderData)
    } catch (error) {
      pushToast(error.message || 'Unable to load account data.', 'error')
    } finally {
      setIsLoading(false)
    }
  }, [token, pushToast])

  useEffect(() => {
    loadAccountData()
  }, [loadAccountData])

  const isAuthenticated = useMemo(() => Boolean(token && user), [token, user])

  const handleProfileSubmit = async (event) => {
    event.preventDefault()
    if (!token) return

    try {
      await apiClient.updateMe(profileForm, token)
      await refreshUser()
      setProfileNotice('Profile saved. Taking you to the basket builder...')
      window.setTimeout(() => {
        navigate('/builder')
      }, 900)
    } catch (error) {
      pushToast(error.message || 'Unable to update profile.', 'error')
    }
  }

  const handleAddressSubmit = async (event) => {
    event.preventDefault()
    if (!token) return

    try {
      if (editingAddressId) {
        await apiClient.updateAddress(editingAddressId, addressForm, token)
        setAddressNotice('Address updated.')
      } else {
        await apiClient.createAddress(addressForm, token)
        setAddressNotice('Address added.')
      }

      setAddressForm(EMPTY_ADDRESS)
      setEditingAddressId(null)
      await loadAccountData()
    } catch (error) {
      pushToast(error.message || 'Unable to save address.', 'error')
    }
  }

  const editAddress = (address) => {
    setEditingAddressId(address.id)
    setAddressForm({
      label: address.label,
      line1: address.line1,
      line2: address.line2,
      city: address.city,
      state: address.state,
      zip_code: address.zip_code,
      country: address.country,
      is_default: address.is_default,
    })
  }

  const cancelAddressEdit = () => {
    setEditingAddressId(null)
    setAddressForm(EMPTY_ADDRESS)
  }

  const removeAddress = async (addressId) => {
    if (!token) return
    try {
      await apiClient.deleteAddress(addressId, token)
      setAddressNotice('Address removed.')
      await loadAccountData()
    } catch (error) {
      pushToast(error.message || 'Unable to remove address.', 'error')
    }
  }

  if (!isAuthenticated) {
    return (
      <main className="page page-account">
        <PageHeader
          eyebrow="Account"
          title="Sign in to access your dashboard"
          subtitle="Track your orders, update profile details, and manage shipping addresses."
        />
        <section className="panel">
          <p>Please sign in before visiting this page.</p>
          <Link className="button" to="/auth">
            Go to sign in
          </Link>
        </section>
      </main>
    )
  }

  return (
    <main className="page page-account">
      <PageHeader
        eyebrow="Account"
        title={`Welcome, ${user.full_name || 'Customer'}`}
        subtitle="Save your profile, then continue to build a basket."
      />

      <section className="account-grid">
        <article className="panel">
          <h2>Profile</h2>
          {profileNotice ? <p className="inline-notice">{profileNotice}</p> : null}
          <form className="stack-form" onSubmit={handleProfileSubmit}>
            <label>
              Full name
              <input
                type="text"
                value={profileForm.full_name}
                onChange={(event) =>
                  setProfileForm((current) => ({ ...current, full_name: event.target.value }))
                }
              />
            </label>
            <label>
              Email
              <input
                type="email"
                required
                value={profileForm.email}
                onChange={(event) =>
                  setProfileForm((current) => ({ ...current, email: event.target.value }))
                }
              />
            </label>
            <button type="submit" className="button">
              Save profile
            </button>
          </form>
        </article>

        <article className="panel">
          <h2>{editingAddressId ? 'Edit address' : 'Add address'}</h2>
          {addressNotice ? <p className="inline-notice">{addressNotice}</p> : null}
          <form className="stack-form" onSubmit={handleAddressSubmit}>
            <label>
              Label
              <input
                type="text"
                maxLength={50}
                value={addressForm.label}
                onChange={(event) =>
                  setAddressForm((current) => ({ ...current, label: event.target.value }))
                }
              />
            </label>
            <label>
              Address line 1
              <input
                type="text"
                required
                value={addressForm.line1}
                onChange={(event) =>
                  setAddressForm((current) => ({ ...current, line1: event.target.value }))
                }
              />
            </label>
            <label>
              Address line 2
              <input
                type="text"
                value={addressForm.line2}
                onChange={(event) =>
                  setAddressForm((current) => ({ ...current, line2: event.target.value }))
                }
              />
            </label>
            <div className="inline-grid">
              <label>
                City
                <input
                  type="text"
                  required
                  value={addressForm.city}
                  onChange={(event) =>
                    setAddressForm((current) => ({ ...current, city: event.target.value }))
                  }
                />
              </label>
              <label>
                State
                <input
                  type="text"
                  required
                  value={addressForm.state}
                  onChange={(event) =>
                    setAddressForm((current) => ({ ...current, state: event.target.value }))
                  }
                />
              </label>
            </div>
            <div className="inline-grid">
              <label>
                Zip code
                <input
                  type="text"
                  required
                  value={addressForm.zip_code}
                  onChange={(event) =>
                    setAddressForm((current) => ({ ...current, zip_code: event.target.value }))
                  }
                />
              </label>
              <label>
                Country
                <input
                  type="text"
                  required
                  value={addressForm.country}
                  onChange={(event) =>
                    setAddressForm((current) => ({ ...current, country: event.target.value }))
                  }
                />
              </label>
            </div>
            <label className="checkbox-label">
              <input
                type="checkbox"
                checked={addressForm.is_default}
                onChange={(event) =>
                  setAddressForm((current) => ({ ...current, is_default: event.target.checked }))
                }
              />
              Set as default address
            </label>
            <div className="form-actions">
              <button type="submit" className="button">
                {editingAddressId ? 'Update address' : 'Add address'}
              </button>
              {editingAddressId ? (
                <button type="button" className="button button-secondary" onClick={cancelAddressEdit}>
                  Cancel
                </button>
              ) : null}
            </div>
          </form>
        </article>
      </section>

      <section className="panel">
        <h2>Saved addresses</h2>
        {addresses.length === 0 ? <p>No saved addresses yet.</p> : null}
        <div className="stack-list">
          {addresses.map((address) => (
            <article key={address.id} className="list-row">
              <div>
                <strong>
                  {address.label} {address.is_default ? '(Default)' : ''}
                </strong>
                <p>
                  {address.line1}, {address.line2 ? `${address.line2}, ` : ''}
                  {address.city}, {address.state} {address.zip_code}, {address.country}
                </p>
              </div>
              <div className="row-actions">
                <button type="button" className="ghost-button" onClick={() => editAddress(address)}>
                  Edit
                </button>
                <button type="button" className="ghost-button danger" onClick={() => removeAddress(address.id)}>
                  Delete
                </button>
              </div>
            </article>
          ))}
        </div>
      </section>

      <section className="panel">
        <h2>Order history</h2>
        {isLoading ? <p>Loading orders...</p> : null}
        {!isLoading && orders.length === 0 ? <p>No orders yet.</p> : null}

        <div className="stack-list">
          {orders.map((order) => (
            <article key={order.id} className="list-row">
              <div>
                <strong>Order {order.id}</strong>
                <p>
                  Status: {order.status} | Total: {formatCurrency(order.total)} | Date:{' '}
                  {formatDate(order.created_at)}
                </p>
              </div>
              <p>{order.items.length} line items</p>
            </article>
          ))}
        </div>
      </section>
    </main>
  )
}