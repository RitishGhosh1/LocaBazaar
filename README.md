# 🚀 LocaBazaar API

A production-style backend API for a hyperlocal marketplace platform built with **FastAPI**. LocaBazaar allows customers to discover local service providers, book services, and manage bookings while supporting secure authentication, role-based authorization, caching, and cloud deployment.

---

## ✨ Features

- 🔐 JWT Authentication & Authorization
- 🌐 Google OAuth 2.0 Sign-In
- 👥 Role-Based Access Control (RBAC)
  - Customer
  - Provider
  - Admin
- 📦 Service & Provider Management
- 📅 Booking Management
- ⚡ Redis Caching
- 📄 Cursor-Based Pagination
- 📚 Interactive API Documentation (Swagger)
- ☁️ Cloud Deployment

---

# 🏗️ Architecture

```
                Client
                   │
                   ▼
            FastAPI Application
                   │
      ┌────────────┴────────────┐
      ▼                         ▼
 Authentication            Business Logic
 (JWT / Google OAuth)            │
      │                          │
      ▼                          ▼
 PostgreSQL (Supabase)      Redis (Upstash)
      │
 SQLAlchemy Async ORM
```

---

# 🛠 Tech Stack

| Layer | Technology |
|--------|------------|
| Backend | FastAPI |
| Language | Python 3.12 |
| Database | PostgreSQL (Supabase) |
| ORM | SQLAlchemy 2.0 Async |
| Cache | Redis (Upstash) |
| Authentication | JWT + OAuth2 + Google Sign-In |
| Validation | Pydantic |
| API Docs | Swagger / OpenAPI |
| Deployment | Render |
| Containerization | Docker |

---

# 🔐 Authentication

LocaBazaar supports two authentication methods:

- JWT Authentication
- Google OAuth 2.0 Login

After successful authentication, the API issues JWT access tokens that are used to authorize protected endpoints.

Role-based authorization is enforced through FastAPI dependencies.

---

# 👥 Roles

### Customer

- Browse services
- Book providers
- Manage bookings

### Provider

- Manage services
- View bookings
- Update service availability

### Admin

- Manage categories
- Manage products
- Manage platform resources

---

# ⚡ Redis Caching

Redis is used as a cache layer to reduce database reads for frequently requested resources.

The application follows a Cache-Aside strategy:

1. Check Redis
2. If cache miss → query PostgreSQL
3. Store response in Redis
4. Return data

Cache entries are invalidated whenever relevant resources are modified.

---

# 📑 Pagination

Large datasets use **Cursor-Based Pagination** instead of traditional Offset Pagination for improved scalability and consistent query performance.

---

# 🌍 Live Demo

### Swagger UI

https://locabazaar-api.onrender.com/docs

### ReDoc

https://locabazaar-api.onrender.com/redoc

---

# 🚀 Running Locally

```bash
git clone https://github.com/RitishGhosh1/LocaBazaar.git

cd LocaBazaar

docker-compose up --build
```

or

```bash
uvicorn app.main:app --reload
```

---

# Environment Variables

```env
DB_HOST=
DB_PORT=
DB_NAME=
DB_USER=
DB_PASSWORD=

REDIS_URL=

SECRET_KEY=
ALGORITHM=

GOOGLE_CLIENT_ID=
GOOGLE_CLIENT_SECRET=
```

---

# API Modules

- Authentication
- Users
- Providers
- Services
- Bookings
- Categories
- Products

---

# Future Improvements

- Refresh Tokens
- Background Notifications
- Payment Gateway Integration
- Rate Limiting
- CI/CD Pipeline
- Unit & Integration Tests

---