# DIY Gifts Basket Frontend

React JS frontend for the DIY Gifts Basket backend API.

## Stack

- React + Vite
- React Router DOM
- Native Fetch API client
- CSS custom design system (vibrant premium theme)

## Features Implemented

- Authentication: register/login/logout
- Guest session flow (`X-Session-ID`) for cart and checkout without login
- Product browsing, search, filtering, product detail, related products
- Basket builder workflow: base selection, item management, personalization, image upload
- Cart management with shipping totals from backend
- Checkout flow with guest email or saved addresses
- Account dashboard: profile update, address CRUD, order history
- Admin dashboard: create category/product/base, list orders, update status, view packing list

## Environment

Create a frontend env file:

```bash
cp .env.example .env
```

Default value:

```env
VITE_API_BASE_URL=http://localhost:8000/api/v1
```

## Run Locally

```bash
cd frontend
npm install
npm run dev
```

App runs at `http://localhost:5173` by default.

## Quality Commands

```bash
npm run lint
npm run build
```

## Frontend Structure

```text
src/
	api/client.js            # All backend endpoint calls
	context/AppContext.jsx   # Auth/session/cart shared state
	components/              # Nav, page sections, toasts, product cards
	pages/                   # Home, Product, Builder, Cart, Auth, Account, 404
	utils/                   # Formatting + localStorage helpers
	App.jsx                  # App shell + routes
	index.css                # Design system and responsive styling
```
