# 🚀 LocaBazaar

A high-performance hyperlocal services marketplace platform featuring an asynchronous **FastAPI** backend, **Next.js** web client, in-memory **Redis** caching, and decoupled **RabbitMQ** event queueing.

LocaBazaar connects local service providers with neighborhood customers, featuring role-based authorization, location-based service discovery, real-time booking management, verified customer reviews, and transactional email processing.

---

## 🏗️ System Architecture

```text
                           ┌────────────────────────┐
                           │   Next.js Web Client   │
                           │  (TypeScript, Query)   │
                           └───────────┬────────────┘
                                       │ HTTP / REST
                                       ▼
                           ┌────────────────────────┐
                           │  FastAPI Backend API   │
                           │ (Asyncpg, Pydantic v2) │
                           └───────────┬────────────┘
                                       │
            ┌──────────────────────────┼──────────────────────────┐
            ▼                          ▼                          ▼
   ┌─────────────────┐        ┌─────────────────┐        ┌─────────────────┐
   │   PostgreSQL    │        │      Redis      │        │    RabbitMQ     │
   │  (Supabase/DB)  │        │  (Cache-Aside)  │        │ (Message Broker)│
   └─────────────────┘        └─────────────────┘        └────────┬────────┘
     • 3NF Schema               • Sub-5ms Read Hits               │
     • CheckConstraints         • Invalidation on Write           ▼
     • Cascaded Foreign Keys    • Cursor Pagination      ┌─────────────────┐
                                                         │  Async Worker   │
                                                         │ (Email Service) │
                                                         └─────────────────┘
```

---

## 🛠️ Technology Stack

| Layer | Technologies | Purpose |
| :--- | :--- | :--- |
| **Backend Core** | FastAPI, Python 3.12+, Uvicorn | Async ASGI RESTful API framework |
| **Data & ORM** | PostgreSQL, SQLAlchemy 2.0 (asyncpg) | Relational persistence with 3NF normalization |
| **Caching Layer** | Redis (`redis-py` async) | Cache-Aside pattern for services & reviews |
| **Message Broker** | RabbitMQ, `aio-pika` | Asynchronous decoupled message queuing |
| **Background Worker** | Python AsyncIO Worker | Durable transactional email processor |
| **Frontend Client** | Next.js 16, React 19, TypeScript, Tailwind CSS | Responsive SPA/SSR client |
| **Client State** | TanStack React Query, Zustand | Server-state caching and auth state management |
| **Authentication** | JWT (PyJWT), Bcrypt, Google OAuth 2.0 | Dual native & dynamic OAuth2 security |
| **Orchestration** | Docker & Docker Compose | Multi-container local orchestration (DB, Cache, Queue, API, Worker) |
| **Testing** | Pytest, Pytest-Asyncio | Automated backend unit and schema testing |

---

## ✨ Key Architectural Features

### 1. ⚡ Redis Cache-Aside Pattern
- High-frequency read endpoints (`/api/v1/services/`, `/api/v1/reviews/service/{id}`) leverage Redis caching.
- **Cache-Aside Flow**:
  1. Check Redis for key (derived from query params & pagination cursor).
  2. On **Cache Hit** ➔ Return serialized response in <5ms without querying the database.
  3. On **Cache Miss** ➔ Query PostgreSQL via `asyncpg`, cache in Redis with TTL, and return.
- **Targeted Invalidation**: Creating, editing, or deleting services or reviews invalidates specific Redis key patterns (`services:q:*`, `reviews:svc:{id}:*`) to prevent stale data.

### 2. 📬 Decoupled Asynchronous Processing (RabbitMQ)
- Time-consuming I/O tasks like SMTP email delivery (account verification, booking updates) are offloaded from the main HTTP event loop to RabbitMQ using `aio-pika`.
- The standalone [`email_worker.py`](app/workers/email_worker.py) consumes from durable queues with acknowledgment, ensuring reliability and zero HTTP latency overhead for users.

### 3. 🔐 Security & Role-Based Access Control (RBAC)
- **Dual Authentication**: Native OAuth2 Password Bearer flow + Dynamic Google Sign-In.
- **Three-Tier RBAC**:
  - `Customer`: Browse services, create bookings, review completed bookings, modify their own reviews and profile.
  - `Provider`: List services with pricing, toggle service availability, manage customer bookings, upload service media.
  - `Admin`: Superuser moderation dashboard to review listings, suspend services, and moderate content.
- Route-level security enforced through reusable FastAPI dependencies (`get_current_user`, `get_superuser`).

### 4. ⭐ Verified Review & Rating System
- Reviews are gated: Customers can only review services they have a `completed` booking for.
- Database-level check constraints ensure ratings are strictly between 1 and 5 (`rating >= 1 AND rating <= 5`).
- Full review lifecycle: Customers can view, edit, or delete their own reviews with immediate cache invalidation.

### 5. 🖼️ Media & Image Uploads
- Dedicated multipart upload endpoint (`POST /api/v1/uploads/image`) with MIME-type whitelist (JPEG, PNG, WEBP, GIF) and 5MB size guard.
- Serves images locally via mounted static files with fallback to Lucide category icons and CSS gradients when no image is uploaded.

---

## 🐳 Running with Docker Compose

Docker Compose is used to orchestrate the entire multi-service stack (PostgreSQL, Redis, RabbitMQ, FastAPI backend, and the background email worker) in a unified environment with a single command:

```bash
# 1. Clone repository
git clone https://github.com/RitishGhosh1/LocaBazaar.git
cd LocaBazaar

# 2. Configure environment variables
cp .env.example .env

# 3. Spin up all containers (Database, Redis, RabbitMQ, API, Email Worker)
docker-compose up --build
```

Once running:
- **Interactive Swagger Docs**: `http://localhost:8000/docs`
- **ReDoc Documentation**: `http://localhost:8000/redoc`
- **RabbitMQ Management**: `http://localhost:15672` (guest / guest)

---

## 💻 Manual Local Setup (Without Docker)

### Backend:
```bash
cd LocaBazaar

# Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Seed superadmin, categories, services, reviews, and bookings
python seed_data.py

# Run FastAPI API server
uvicorn app.main:app --reload --port 8000

# Run Background Email Worker (in separate terminal)
python -m app.workers.email_worker
```

### Frontend:
```bash
cd LocaBazaar_frontend

# Install dependencies
npm install

# Start development server
npm run dev
```
Frontend runs at `http://localhost:3000`.

---

## 🧪 Testing

The backend includes automated tests using `pytest` and `pytest-asyncio`:

```bash
cd LocaBazaar
pytest tests/ -v
```

---

## 📁 Project Structure

```text
LocaBazaar_PROJECT/
├── LocaBazaar/                   # Backend Application
│   ├── app/
│   │   ├── api/v1/endpoints/     # REST Endpoints (auth, services, bookings, reviews, uploads, admin)
│   │   ├── core/                 # Config, Security, Redis client, RabbitMQ manager
│   │   ├── db/                   # Async session & engine setup
│   │   ├── models/               # SQLAlchemy ORM Models (User, Service, Booking, Review, Category)
│   │   ├── schemas/              # Pydantic validation schemas
│   │   ├── services/             # Email & utility business logic
│   │   └── workers/              # RabbitMQ email background consumer
│   ├── tests/                    # Pytest test suite
│   ├── Dockerfile
│   ├── docker-compose.yml
│   └── requirements.txt
│
└── LocaBazaar_frontend/          # Web Client
    ├── src/
    │   ├── app/                  # Next.js App Router (pages: /explore, /dashboard, /provider, /admin)
    │   ├── components/           # UI components (ServiceCard, Navbar, Forms)
    │   ├── hooks/                # TanStack Query custom hooks
    │   ├── services/             # Axios API client & endpoints
    │   └── store/                # Zustand client auth store
    └── package.json
```