# DIY Gift Basket — Project Walkthrough

## Table of Contents

1. [Folder Structure](#folder-structure)
2. [How the Backend Starts](#how-the-backend-starts)
3. [How the Frontend Starts](#how-the-frontend-starts)
4. [Request Lifecycle (Backend Pattern)](#request-lifecycle-backend-pattern)
5. [Flow: App Initialization](#flow-app-initialization)
6. [Flow: Authentication](#flow-authentication)
7. [Flow: Basket Builder (main feature)](#flow-basket-builder-main-feature)
8. [Flow: Cart & Checkout](#flow-cart--checkout)
9. [Flow: AI Assistant](#flow-ai-assistant)
10. [Flow: Admin Panel](#flow-admin-panel)
11. [Database Layer](#database-layer)
12. [Key Concepts & Integration Points](#key-concepts--integration-points)

---

## Folder Structure

```
diy-gifts-basket/
│
├── app/                        ← Python backend (FastAPI)
│   ├── main.py                 ← App factory + CORS + lifespan hooks
│   ├── api/
│   │   └── v1/                 ← All HTTP route handlers (one file per domain)
│   │       ├── router.py       ← Registers every sub-router under /api/v1
│   │       ├── auth.py         ← /auth/register, /auth/login, /auth/guest
│   │       ├── baskets.py      ← /baskets/... (the basket builder endpoints)
│   │       ├── products.py     ← /products/...
│   │       ├── categories.py   ← /categories/...
│   │       ├── cart.py         ← /cart/...
│   │       ├── orders.py       ← /orders/checkout, /orders/...
│   │       ├── personalization.py ← /baskets/{id}/personalization/...
│   │       ├── users.py        ← /users/me
│   │       ├── addresses.py    ← /addresses/...
│   │       ├── admin.py        ← /admin/... (admin-only endpoints)
│   │       ├── chat.py         ← /chat/... (live support chat)
│   │       ├── images.py       ← /images/ (file upload)
│   │       └── ai.py           ← /ai/chat (AI basket assistant)
│   │
│   ├── services/               ← Business logic layer (one file per domain)
│   │   ├── auth_service.py
│   │   ├── basket_service.py   ← Core basket builder logic
│   │   ├── cart_service.py
│   │   ├── order_service.py
│   │   ├── product_service.py
│   │   ├── user_service.py
│   │   ├── personalization_service.py
│   │   ├── category_service.py
│   │   ├── address_service.py
│   │   └── upload_service.py
│   │
│   ├── repositories/           ← Database query layer (one file per model)
│   │   ├── base.py             ← Generic CRUD: create, get_by_id, update, delete
│   │   ├── basket_repo.py      ← Basket-specific queries (eager loading, totals)
│   │   ├── cart_repo.py
│   │   ├── order_repo.py
│   │   ├── product_repo.py
│   │   └── user_repo.py
│   │
│   ├── models/                 ← SQLAlchemy ORM models (map to DB tables)
│   │   ├── user.py             ← users table
│   │   ├── basket.py           ← baskets, basket_items, bases tables
│   │   ├── cart.py             ← carts, cart_items tables
│   │   ├── order.py            ← orders, order_items tables
│   │   ├── product.py          ← products, product_relations tables
│   │   ├── category.py         ← categories table
│   │   ├── address.py          ← addresses table
│   │   └── personalization.py  ← personalizations table
│   │
│   ├── schemas/                ← Pydantic models (request validation + response shape)
│   │   ├── basket.py           ← BasketCreate, BasketResponse, GiftBaseResponse, ...
│   │   ├── user.py             ← UserCreate, UserLogin, TokenResponse, ...
│   │   └── ...
│   │
│   ├── core/
│   │   ├── config.py           ← Settings loaded from .env via pydantic-settings
│   │   ├── security.py         ← JWT creation/validation, password hashing, auth deps
│   │   └── exceptions.py       ← Custom exception classes + global exception handlers
│   │
│   ├── db/
│   │   ├── base.py             ← DeclarativeBase (all models inherit from this)
│   │   └── session.py          ← Async engine, session factory, get_db() dependency
│   │
│   └── utils/
│       ├── email.py            ← SMTP helpers (welcome, order confirmation, reset)
│       └── pagination.py       ← Pagination helpers
│
├── frontend/
│   └── src/
│       ├── main.jsx            ← Vite entry point; mounts <App /> into #root
│       ├── App.jsx             ← Router setup, context providers, AppShell
│       ├── api/
│       │   └── client.js       ← Single fetch wrapper + every API call method
│       ├── context/
│       │   ├── AppContext.jsx  ← Global state: token, sessionId, user, cart, toasts
│       │   └── ChatContext.jsx ← Live support chat state
│       ├── pages/              ← One component per route
│       │   ├── HomePage.jsx
│       │   ├── BasketBuilderPage.jsx  ← 4-step basket builder
│       │   ├── CartPage.jsx
│       │   ├── AuthPage.jsx
│       │   ├── AccountPage.jsx
│       │   ├── OrdersPage.jsx
│       │   ├── ProductPage.jsx
│       │   ├── AdminPage.jsx
│       │   └── ...
│       ├── components/
│       │   ├── NavBar.jsx
│       │   ├── AIBuilderChat.jsx  ← AI sidebar inside basket builder
│       │   ├── ChatWidget.jsx     ← Floating live-support chat (bottom right)
│       │   ├── ProductCard.jsx
│       │   ├── ToastTray.jsx
│       │   └── PageHeader.jsx
│       ├── utils/
│       │   ├── catalog.js      ← enhanceProducts(), enhanceBases() (fallback images)
│       │   ├── format.js       ← formatCurrency(), formatDate()
│       │   ├── storage.js      ← localStorage get/set for token and sessionId
│       │   └── prebuiltBaskets.js ← Static prebuilt basket templates for HomePage
│       └── index.css           ← All global styles
│
├── alembic/                    ← Database migration files
│   └── versions/               ← Each file is a schema migration
│
├── .env                        ← Secret keys (never committed)
├── .env.example                ← Template for .env
├── requirements.txt            ← Python dependencies
└── alembic.ini                 ← Alembic config
```

---

## How the Backend Starts

**Entry point:** `uvicorn app.main:app`

```
app/main.py
└── create_app()
    ├── get_settings()          ← reads .env, returns cached Settings singleton
    ├── FastAPI(lifespan=...)   ← registers startup/shutdown hooks
    ├── CORSMiddleware          ← allows all origins (dev config)
    ├── register_exception_handlers(app)   ← maps NotFoundError → 404, etc.
    └── app.include_router(v1_router)      ← mounts all routes under /api/v1
```

**`app/api/v1/router.py`** imports every sub-router and attaches them:

```
v1_router (prefix: /api/v1)
├── /auth/...
├── /users/...
├── /products/...
├── /baskets/...
├── /cart/...
├── /orders/...
├── /admin/...
├── /chat/...
├── /images/...
└── /ai/...
```

**`app/db/session.py`** runs at import time:
1. Reads `DATABASE_URL` from Settings
2. Creates the async SQLAlchemy engine (`create_async_engine`)
3. Creates `AsyncSessionLocal` (session factory)
4. Defines `get_db()` — a FastAPI dependency that yields a session and auto-commits or rolls back

---

## How the Frontend Starts

**Entry point:** `frontend/src/main.jsx` — mounts `<App />` into `document.getElementById('root')`

```
App.jsx
└── <AppProvider>               ← initializes token, sessionId, user, cart state
    └── <ChatProvider>          ← initializes live support chat state
        └── <BrowserRouter>
            └── <AppShell>
                ├── <NavBar />
                ├── <Routes>    ← maps URL paths to page components
                ├── <footer />
                ├── <ToastTray />
                └── <ChatWidget />   ← always rendered (floating chat button)
```

**`AppContext.jsx` on mount runs three effects in order:**

1. `ensureGuestSession()` — if no sessionId in localStorage, calls `POST /auth/guest` to get one, saves to localStorage
2. `refreshUser()` — if token in localStorage, calls `GET /users/me` to rehydrate user state
3. `refreshCart()` — calls `GET /cart/` using token + sessionId to load the user's cart

---

## Request Lifecycle (Backend Pattern)

Every API request follows this stack. No step skips another.

```
HTTP Request
    ↓
FastAPI route handler  (app/api/v1/*.py)
    ↓  validates request body via Pydantic schema
    ↓  resolves FastAPI dependencies (get_db, get_current_user)
Service class          (app/services/*.py)
    ↓  contains business rules (capacity checks, status transitions, etc.)
Repository class       (app/repositories/*.py)
    ↓  builds and executes SQLAlchemy queries
Database (Supabase PostgreSQL)
    ↓
Repository returns ORM model instance(s) to Service
Service returns dict or ORM model to Route handler
Route handler serializes via Pydantic response_model
    ↓
HTTP Response (JSON)
```

**`get_db()` dependency** (in `app/db/session.py`):
- Opens an `AsyncSession`
- Yields it to the route handler
- On success: calls `await session.commit()` — writes all changes to DB
- On exception: calls `await session.rollback()` — discards all changes
- Always calls `await session.close()`

**`get_current_user()` dependency** (in `app/core/security.py`):
- Reads `Authorization: Bearer <token>` header
- Calls `decode_access_token()` — verifies JWT signature and expiry
- Returns a lightweight `User` object with `id` and `role` from token payload
- `get_current_user_optional()` — same but returns `None` instead of 401 if no token

---

## Flow: App Initialization

What happens the moment a user opens the site:

```
Browser loads index.html
    ↓
Vite serves frontend/src/main.jsx
    ↓
React mounts App → AppProvider constructor runs
    ↓
useState(() => getStoredToken())        ← reads localStorage["token"]
useState(() => getStoredSessionId())    ← reads localStorage["sessionId"]
    ↓
useEffect #1: ensureGuestSession()
    if no sessionId → apiClient.createGuestSession()
        → POST /api/v1/auth/guest
        → AuthService.generate_guest_session()  returns "guest_<uuid>"
    → saves sessionId to localStorage
    ↓
useEffect #2: refreshUser()
    if token exists → apiClient.getMe(token)
        → GET /api/v1/users/me
        → get_current_user() dependency decodes JWT
        → UserService.get_profile() fetches user from DB
    → sets user state (or clears token if 401)
    ↓
useEffect #3: refreshCart()
    → apiClient.getCart({ token, sessionId })
        → GET /api/v1/cart/
        → CartService.get_cart() loads cart + items + baskets
    → sets cart state
    ↓
NavBar renders with correct user/cart state
```

---

## Flow: Authentication

### Register

```
User fills AuthPage register form → submit
    ↓
apiClient.register({ email, password, full_name })
    → POST /api/v1/auth/register
    ↓
auth.py: register() handler
    ↓
AuthService.register(data)
    ├── user_repo.get_by_email(email)     ← check if email exists
    ├── if exists → raise ConflictError 409
    ├── hash_password(password)           ← bcrypt
    ├── user_repo.create({...})           ← INSERT into users
    ├── asyncio.create_task(send_welcome_email(...))   ← fire-and-forget SMTP
    └── create_access_token({"sub": user.id, "role": "customer"})
        ← signs JWT with JWT_SECRET, expires in ACCESS_TOKEN_EXPIRE_MINUTES
    ↓
Returns TokenResponse { access_token: "..." }
    ↓
Frontend: setToken(access_token) → saves to localStorage
    ↓
AppContext.refreshUser() called → sets user state
```

### Login

```
User fills login form → submit
    ↓
apiClient.login({ email, password })
    → POST /api/v1/auth/login
    ↓
AuthService.login(data)
    ├── user_repo.get_by_email(email)
    ├── verify_password(plain, hashed)    ← bcrypt compare
    ├── if invalid → raise ValidationError 422
    └── create_access_token(...)
    ↓
Frontend saves token, refreshUser() loads profile
```

### Guest Session

Guests get a `session_id` string like `guest_<32hex chars>`. Every basket/cart API call sends this as `X-Session-ID` header. The backend uses it to associate data with anonymous users. Logging in does NOT automatically merge guest data.

---

## Flow: Basket Builder (main feature)

The basket builder is a 4-step wizard at `/builder`. This is the core product flow.

### Step 0 — Page Load

```
BasketBuilderPage mounts
    ↓
loadCatalog() runs immediately via useEffect
    ├── apiClient.listBases()
    │   → GET /api/v1/baskets/bases
    │   → BasketService.list_bases()
    │   → GiftBaseRepository.get_all()
    │   → SELECT * FROM bases
    │
    └── apiClient.listProducts({ limit: 100 })
        → GET /api/v1/products/
        → ProductService.list_products()
        → SELECT * FROM products WHERE is_active = true
    ↓
enhanceBases(baseData)    ← adds fallback image_url if missing
enhanceProducts(productData)  ← same
    ↓
setBases([...])
setProducts([...])
setIsInitializing(false)
    ↓
Stepper renders; Step 1 (Base Selection) is shown
```

### Step 1 — Select a Base

```
User clicks a base card → setSelectedBaseId(base.id)
User clicks "Next" → handleBaseNext()
    ↓
if no selectedBaseId → pushToast('Select a base first')
else → setCurrentStep(2)

NOTE: No API call yet. The basket is not created until Step 2 "Next" is clicked.
```

### Step 2 — Add Products

```
Products grid is shown (filtered: is_sold_out === false)
User clicks + or - → setProductQuantity(productId, newQty)
    └── clampQuantity() ensures qty is between 0 and inventory_count

User clicks "Next" → handleProductsNext()
    ↓
setIsSubmitting(true)
    ↓
applySelectedProducts()
    ↓
ensureBasketWithBase()
    ├── if no basket yet:
    │   apiClient.createBasket({ base_id: selectedBaseId, session_id })
    │   → POST /api/v1/baskets/
    │   → BasketService.create_basket()
    │       ├── GiftBaseRepository.get_by_id(base_id)  ← verify base exists
    │       ├── BasketRepository.create({ user_id, session_id, base_id, status:"draft" })
    │       │   → INSERT INTO baskets
    │       └── returns { basket, running_total }
    │   setBasket(created)
    │
    └── if basket exists but base changed:
        apiClient.setBasketBase(basket.id, { base_id })
        → PUT /api/v1/baskets/{id}/base
        → BasketService.set_base()
            ├── checks capacity: current items <= base.max_items
            ├── basket.base_id = base.id
            └── db.flush()
    ↓
apiClient.syncBasketItems(basketId, { items: [...] })
    → PUT /api/v1/baskets/{id}/items/sync
    → BasketService.sync_items()
        ├── BasketRepository.get_with_base(basket_id)   ← load basket + base
        ├── validates total_quantity <= base.max_items
        ├── ProductRepository.get_by_ids(product_ids)   ← verify all products exist
        ├── checks none are sold out
        ├── BasketItemRepository.replace_items(basket_id, items)
        │   → DELETE FROM basket_items WHERE basket_id = ?
        │   → INSERT INTO basket_items (new rows)
        │   → db.flush()
        └── BasketRepository.get_with_items(basket_id)
            ← SELECT basket with selectinload(items→product) + joinedload(base)
    → returns BasketResponse with running_total
    ↓
setBasket(updated)
setCurrentStep(3)
```

### Step 3 — Personalization

```
Form fields: gift message (textarea), ribbon color (select), delivery date (date input)
Optional: gift tag image upload

User changes fields → setPersonalizationForm({ gift_message, ribbon_color, ... })
    (state update only, no API call)

Gift tag upload:
    ensureBasketWithBase()   ← ensures basket exists
    apiClient.uploadGiftTag(basketId, file)
    → POST /api/v1/baskets/{id}/personalization/upload
    → UploadService saves file locally, returns public URL
    → PersonalizationService.upsert(basket_id, { gift_tag_image_url: url })
    → UPSERT INTO personalizations

User clicks "Next" → savePersonalization(e)
    e.preventDefault()
    if no basket items → go back to step 2
    else → setCurrentStep(4)
    (personalizationForm state is saved in-memory; it's submitted at Step 4)
```

### Step 4 — Review & Add to Cart

```
Shows summary: base name, item count, running_total, delivery date
Lists each basket item (title + quantity)

User clicks "Add to cart" → completeAndAddToCart()
    ↓
apiClient.completeAndAddToCart(basket.id, { personalization: {...} })
    → POST /api/v1/baskets/{id}/complete-and-cart
    → BasketService.complete_and_add_to_cart()
        ├── _get_basket(basket_id)   ← verifies basket exists and has base + items
        ├── if personalization has values:
        │   ├── BasketRepository.get_with_personalization(basket_id)
        │   ├── if personalization row exists → UPDATE it
        │   └── else → INSERT INTO personalizations
        │   └── db.flush()
        ├── basket.status = "complete"
        │   → db.flush()
        ├── CartRepository.get_or_create(user_id, session_id)
        │   ← finds existing cart or inserts new one
        └── CartItemRepository.create({ cart_id, basket_id, quantity: 1 })
            → INSERT INTO cart_items
    ↓
get_db() auto-commits entire transaction
    ↓
refreshCart()   ← reloads cart from API → updates NavBar badge
navigate('/cart')
```

---

## Flow: Cart & Checkout

### Cart Page Load

```
CartPage mounts
    ↓
apiClient.getCart({ token, sessionId })
    → GET /api/v1/cart/
    → CartService.get_cart()
        ├── CartRepository.get_or_create(user_id, session_id)
        ├── loads cart items with their baskets (selectinload)
        ├── basket_ids = [item.basket_id for each cart item]
        ├── BasketRepository.get_many_with_items(basket_ids)
        │   ← loads each basket with items + products + base + personalization
        ├── BasketRepository.get_totals_by_ids(basket_ids)
        │   ← single SQL query: SUM(product.price * qty) + base.price per basket
        ├── subtotal = sum of all basket totals
        ├── shipping_fee = 0 if subtotal >= 50 else 5.99
        └── returns { cart, baskets_by_id, subtotal, shipping_fee, total }
    ↓
Renders each basket as a line item with its total
```

### Checkout

```
User fills shipping form (or selects saved address) → clicks "Place Order"
    ↓
apiClient.checkout({ shipping: {...} or address_id, guest_email })
    → POST /api/v1/orders/checkout
    → OrderService.checkout()
        ├── _resolve_shipping()
        │   ← if address_id: fetch from DB and serialize to JSON
        │   ← else: use inline shipping object
        ├── CartService.get_cart()    ← recalculates totals fresh
        ├── validates cart not empty
        ├── generates payment_ref = "PAY-<12 random hex chars>"
        ├── OrderRepository.create({...})  → INSERT INTO orders
        ├── BasketRepository.get_totals_by_ids([...])
        ├── OrderItemRepository.create_many([...])
        │   → INSERT INTO order_items (one row per basket in cart)
        ├── CartItemRepository.clear_cart(cart.id)
        │   → DELETE FROM cart_items WHERE cart_id = ?
        ├── send_order_confirmation(email, order)   ← SMTP email
        └── OrderRepository.get_with_items(order.id)  ← return full order
    ↓
navigates to /orders
```

---

## Flow: AI Assistant

The AI sidebar lives inside `BasketBuilderPage`. It communicates with the backend Groq API.

### Opening the Panel

```
User clicks "✨ AI Assistant" FAB button (bottom left)
    → setShowAI(true)
    → {showAI && <AIBuilderChat ... />} renders in DOM (left side of flex layout)
    → ai-side-chat-wrapper slides in via CSS @keyframes ai-slide-in
```

### Sending a Message

```
User types message → clicks Send
    ↓
AIBuilderChat calls apiClient.post('/ai/chat', { message, current_step, selected_base_id, selected_product_ids })
    → POST /api/v1/ai/chat
    ↓
ai.py: chat_with_ai(request)
    ↓
1. Reads GROQ_API_KEY from Settings
   if missing → raise 500

2. Creates AsyncOpenAI client with:
   api_key = GROQ_API_KEY
   base_url = "https://api.groq.com/openai/v1"
   (Groq is OpenAI-API compatible)

3. ProductService.list_products(limit=100)   ← loads all in-stock products
   BasketService.list_bases()                ← loads all bases

4. Builds catalog_summary string:
   "AVAILABLE BASES:\n- {name} (ID: {id}, Price: ...) ..."
   "AVAILABLE PRODUCTS:\n- {title} (ID: {id}, Price: ...) ..."

5. Builds system_prompt with:
   - current_step number
   - Step-specific instructions (max 2 suggestions, no gift cards in step 3, etc.)
   - Full catalog
   - User state (selected base + product IDs)

6. client.chat.completions.create(
       model="llama-3.3-70b-versatile",
       messages=[system_prompt, user_message],
       max_tokens=300
   )
   ← Groq runs inference and returns reply

7. Parses reply_text
   Scans products: if product.id or product.title appears in reply → add to recommendations

8. Returns ChatResponse { reply, suggested_step, recommendations }
    ↓
AIBuilderChat renders reply as message bubble
If recommendations exist → shows product cards with "Add" buttons
```

---

## Flow: Admin Panel

```
AdminPage checks user.role === 'admin'
If not admin → redirected away by NonAdminRoute guard in App.jsx

Admin features:
├── Products: adminCreateProduct / adminUpdateProduct
│   → POST/PUT /api/v1/admin/products
│   → require_admin dependency checks role from JWT
│
├── Categories: adminCreateCategory / adminUpdateCategory
│   → POST/PUT /api/v1/admin/categories
│
├── Bases: adminCreateBase
│   → POST /api/v1/admin/bases
│
├── Orders: adminListOrders, adminUpdateOrderStatus
│   → GET/PUT /api/v1/admin/orders
│   → OrderService.update_order_status() validates status transition
│
└── Packing List: adminGetPackingList(orderId)
    → GET /api/v1/admin/orders/{id}/packing-list
    → OrderService.get_packing_list()
        ← loads each order_item → basket → basket_items → products
        ← returns structured packing list per basket
```

---

## Database Layer

### Schema Summary

| Table | Key columns |
|-------|-------------|
| `users` | id, email, hashed_password, role, is_active |
| `bases` | id, name, size (S/M/L), price, max_items |
| `baskets` | id, user_id, session_id, base_id, status (draft/complete) |
| `basket_items` | id, basket_id, product_id, quantity |
| `personalizations` | id, basket_id (unique), gift_message, ribbon_color, gift_tag_image_url, requested_delivery_date |
| `products` | id, sku, title, price, inventory_count, is_active, category_id |
| `categories` | id, name, slug |
| `carts` | id, user_id (unique), session_id |
| `cart_items` | id, cart_id, basket_id, quantity |
| `orders` | id, user_id, total, subtotal, shipping_fee, status, payment_ref |
| `order_items` | id, order_id, basket_id, unit_price, quantity |
| `addresses` | id, user_id, line1, city, state, zip_code, is_default |

### Relationship flow (data model)

```
User ──< Basket ──< BasketItem >── Product
          │
          ├── GiftBase
          └── Personalization

User ──── Cart ──< CartItem >── Basket

User ──< Order ──< OrderItem >── Basket
```

### BaseRepository pattern

`app/repositories/base.py` provides generic CRUD that all repos inherit:

| Method | SQL |
|--------|-----|
| `create(data)` | INSERT + flush |
| `get_by_id(id)` | SELECT WHERE id = ? |
| `get_all(skip, limit)` | SELECT OFFSET LIMIT |
| `update(id, data)` | setattr + flush |
| `delete(id)` | DELETE + flush |

Specialized repos (e.g. `BasketRepository`) add queries that require joins or eager loading.

---

## Key Concepts & Integration Points

### Session Commit Pattern

`get_db()` commits after the route handler completes. Route handlers and services call `db.flush()` to write to the DB within the same transaction (so IDs are generated and relations work), but the commit only happens once at the end. If anything raises an exception, the entire transaction rolls back.

### Guest vs Authenticated

- **Guest**: No token. Sends `X-Session-ID` header. Baskets/carts are keyed by `session_id` column.
- **Authenticated**: Sends `Authorization: Bearer <token>`. Baskets/carts are keyed by `user_id`.
- Both can use the basket builder. `get_current_user_optional()` returns `None` for guests instead of 401.

### JWT Flow

1. Login/register → `create_access_token({"sub": user.id, "role": user.role})` → signed HS256 JWT
2. Frontend stores in localStorage
3. Every protected request sends `Authorization: Bearer <token>`
4. `decode_access_token()` verifies signature and expiry → returns payload
5. `get_current_user()` builds a lightweight `User(id=..., role=...)` from the payload (no DB call)

### API Client (frontend)

`frontend/src/api/client.js` is a single module that:
- Wraps every API call in one `request()` function
- Automatically sets `Authorization` and `X-Session-ID` headers when provided
- On 401 responses: fires `window.dispatchEvent(new CustomEvent('auth:expired'))` → AppContext listener clears token and redirects to `/auth`
- All calls return parsed JSON or throw an `Error` with the API's `detail` message

### Toast Notifications

`AppContext.pushToast(message, type)` creates a toast with a UUID and auto-dismisses it after 4200ms. `ToastTray` component reads `toasts` from context and renders them. Any component can call `pushToast` via `useAppContext()`.

### Prebuilt Baskets (HomePage)

`frontend/src/utils/prebuiltBaskets.js` contains static templates. When a user clicks "Build this basket" on the HomePage, it encodes the template as a URL query param:

```
/builder?prefill=<URL-encoded JSON>
```

`BasketBuilderPage` reads `?prefill`, decodes it, and runs `applyPrefill()` which creates a basket, syncs the items, and upserts personalization — all in one shot before rendering the form.
