# 🎁 DIY Gift Basket API

A FastAPI backend for a customizable gift basket e-commerce platform. Users can browse products, build personalized gift baskets through a step-by-step wizard, and place orders with simulated payment.

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Framework | FastAPI (async) |
| Language | Python 3.9+ |
| ORM | SQLAlchemy 2.x (async) + `asyncpg` |
| Database | Supabase PostgreSQL |
| Migrations | Alembic |
| Auth | JWT (PyJWT) + bcrypt (passlib) |
| File Uploads | Supabase Storage |
| Email | fastapi-mail (SMTP) |

## Quick Start

### 1. Clone & create virtual environment

```bash
cd diy-gifts-basket
python3 -m venv venv
source venv/bin/activate   # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure environment variables

```bash
cp .env.example .env
# Edit .env with your Supabase credentials and settings
```

### 3. Run database migrations

```bash
alembic upgrade head
```

### 4. Start the development server

```bash
uvicorn app.main:app --reload
```

The API will be available at:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/health

## Project Structure

```
diy-gifts-basket/
├── app/
│   ├── main.py              # App factory, CORS, lifespan, health check
│   ├── core/                # Config, security, exceptions
│   ├── db/                  # Async engine, session, DeclarativeBase
│   ├── models/              # SQLAlchemy ORM models (8 domain files)
│   ├── schemas/             # Pydantic request/response schemas
│   ├── repositories/        # Data-access layer (DB queries only)
│   ├── services/            # Business-logic layer
│   ├── api/v1/              # HTTP route handlers (thin controllers)
│   └── utils/               # Email, pagination helpers
├── alembic/                 # Database migration scripts
├── tests/                   # Test suite
├── .env.example             # Environment variable template
├── requirements.txt         # Python dependencies
└── alembic.ini              # Alembic configuration
```

## Architecture (SOLID Principles)

The codebase follows a **layered architecture** with strict separation of concerns:

```
HTTP Request → API Route → Service → Repository → Database
```

- **Routes** (`api/v1/`): Thin controllers — validate input, call service, return response.
- **Services** (`services/`): Business logic — enforce rules, orchestrate repos, handle side effects.
- **Repositories** (`repositories/`): Data access — raw SQL queries via SQLAlchemy, no business logic.
- **Models** (`models/`): ORM definitions — table structure, relationships, computed properties.
- **Schemas** (`schemas/`): Pydantic models — request validation, response serialization.

## API Endpoints (36 total)

### Authentication (`/api/v1/auth`)
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/register` | Create account & get JWT |
| POST | `/login` | Login with email/password |
| POST | `/guest` | Generate guest session ID |

### Users (`/api/v1/users`)
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/me` | Get current user profile |
| PUT | `/me` | Update profile |

### Addresses (`/api/v1/addresses`)
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | List saved addresses |
| POST | `/` | Add new address |
| PUT | `/{id}` | Update address |
| DELETE | `/{id}` | Delete address |

### Categories (`/api/v1/categories`)
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | List categories |
| GET | `/{id}` | Get category |

### Products (`/api/v1/products`)
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | List products |
| GET | `/search` | Search with filters |
| GET | `/{id}` | Get product details |
| GET | `/{id}/related` | Related items |

### Basket Builder (`/api/v1/baskets`)
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/bases` | List containers |
| POST | `/` | Create new basket |
| PUT | `/{id}/base` | Select container |
| POST | `/{id}/items` | Add item |
| DELETE | `/{id}/items/{iid}` | Remove item |
| GET | `/{id}/summary` | Review basket |
| POST | `/{id}/complete` | Mark complete |

### Personalization (`/api/v1/baskets/{id}/personalization`)
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Get personalization |
| PUT | `/` | Set message/ribbon/date |
| POST | `/upload` | Upload gift-tag image |

### Cart (`/api/v1/cart`)
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Get cart with totals |
| POST | `/items` | Add basket to cart |
| PUT | `/items/{id}` | Edit quantity |
| DELETE | `/items/{id}` | Remove item |

### Orders (`/api/v1/orders`)
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/checkout` | Place order |
| GET | `/` | My order history |
| GET | `/{id}` | Order details |

### Admin (`/api/v1/admin`)
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/products` | Add product |
| PUT | `/products/{id}` | Edit product |
| POST | `/categories` | Add category |
| PUT | `/categories/{id}` | Edit category |
| POST | `/bases` | Add gift base |
| GET | `/orders` | All orders |
| GET | `/orders/{id}/packing-list` | Packing list |
| PUT | `/orders/{id}/status` | Update status |

## License

This project is for academic/educational purposes.
