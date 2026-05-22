# LocaBazaar 🛠️

**A Professional Hyperlocal Service Marketplace Backend**

LocaBazaar is a high-performance, asynchronous REST API that connects customers with local service providers. Built with FastAPI, PostgreSQL, and Redis.

---

## 🚀 Key Features

- Role-Based Access Control (Customer, Provider, Admin)
- Service listing and management with categories
- Booking system with status workflow
- Verified reviews (only after completed bookings)
- Advanced search & filtering
- Google OAuth2 authentication
- JWT-based auth
- Redis caching support

---

## 🏗️ Tech Stack

- **Framework**: FastAPI (Python 3.11+)
- **Database**: PostgreSQL + SQLAlchemy 2.0 (Async)
- **Cache**: Redis
- **Validation**: Pydantic v2
- **Auth**: JWT + Authlib (Google OAuth)
- **Containerization**: Docker + Docker Compose

---

## 📂 Project Structure

```text
LocaBazaar/
├── app/
│   ├── api/v1/
│   │   ├── endpoints/          # API route handlers
│   │   └── router.py           # Main API router
│   ├── core/                   # Config, security, dependencies
│   ├── db/                     # Database configuration
│   ├── models/                 # SQLAlchemy models
│   ├── schemas/                # Pydantic schemas
│   └── main.py
├── docker-compose.yml
├── seed.py                     # Data seeder
├── .env.example
├── requirements.txt
└── README.md

