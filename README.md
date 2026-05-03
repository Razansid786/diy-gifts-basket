# 🎁 DIY Gift Basket Platform

A full-stack e-commerce platform for building customizable gift baskets.

## Features
- **User Accounts**: Secure registration, login, and password recovery.
- **Product Catalog**: Browse and search for items by category and price.
- **Custom Builder**: A step-by-step wizard to choose a base, add products, and personalize with messages and ribbons.
- **Shopping Cart**: Manage multiple baskets and proceed to checkout.
- **Order Tracking**: View order history and shipping status.
- **Admin Dashboard**: Manage inventory, categories, and fulfill orders.

## Tech Stack
- **Backend**: FastAPI, SQLAlchemy (PostgreSQL), Alembic, JWT.
- **Frontend**: React, Vanilla CSS.

## Getting Started

### 1. Backend Setup
```bash
# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env

# Run migrations
alembic upgrade head

# Start server
uvicorn app.main:app --reload
```

### 2. Frontend Setup
```bash
cd frontend
npm install
npm run dev
```

## Project Structure
- `app/`: FastAPI backend logic.
- `frontend/`: React frontend application.
- `alembic/`: Database migration scripts.

## Contact
For any assistance with orders, please contact us at hello@diygiftsbasket.com or call **+92 (300) 123-4567**.
