# LocaBazaar API

LocaBazaar is a local-services marketplace that connects customers with nearby service providers. This repository contains the asynchronous FastAPI backend and the Docker Compose deployment stack.

**Live application:** [loca-bazaar-frontend.vercel.app](https://loca-bazaar-frontend.vercel.app/)

**API documentation:** [Swagger UI](https://locabazaar-ritish.duckdns.org/docs) · [ReDoc](https://locabazaar-ritish.duckdns.org/redoc)

## Features

- JWT authentication, optional Google sign-in, and customer, provider, and administrator roles.
- Service discovery with categories, search, location filters, and cursor pagination.
- Booking management for customers and providers.
- Customer reviews and ratings, including booking-based review eligibility.
- Image upload and service media support.
- Redis caching for frequently requested service and review data.
- RabbitMQ-backed background email processing.
- Administrator tools for managing users, services, bookings, and reviews.

## Architecture

```text
Next.js frontend (Vercel)
          │ HTTPS / REST
          ▼
Caddy reverse proxy (EC2) ── FastAPI API
                                  ├── PostgreSQL
                                  ├── Redis
                                  └── RabbitMQ ── Email worker
```

## Technology

| Area | Tools |
| --- | --- |
| API | Python 3.12, FastAPI, Uvicorn, Pydantic |
| Database | PostgreSQL, SQLAlchemy 2, asyncpg |
| Cache | Redis |
| Background jobs | RabbitMQ, aio-pika, Python asyncio |
| Deployment | Docker Compose, Caddy, AWS EC2 |
| Frontend | Next.js, React, TypeScript, Tailwind CSS ([frontend repository](https://github.com/RitishGhosh1/LocaBazaar_frontend)) |

## Run locally with Docker

Requirements: Docker Engine and the Docker Compose plugin.

```bash
git clone https://github.com/RitishGhosh1/LocaBazaar.git
cd LocaBazaar
cp .env.example .env
```

Edit `.env` before starting the stack. Set strong values for `DB_PASSWORD`, `RABBITMQ_PASS`, and `SECRET_KEY`. For local frontend development, set both `FRONTEND_URL` and `CORS_ORIGINS` to `http://localhost:3000`. Google OAuth and SMTP settings are optional unless you want to exercise those features. Do not commit `.env` or put production secrets in the repository.

```bash
docker compose up --build -d
```

The API waits for PostgreSQL, Redis, and RabbitMQ health checks before starting. The API port is bound to `127.0.0.1:8000` for local access.

- Swagger UI: <http://localhost:8000/docs>
- ReDoc: <http://localhost:8000/redoc>

### Add sample data

The API creates the database tables during startup. Wait until it reports that startup is complete, then run the seed script without the API container active to avoid competing with startup schema changes:

```bash
docker compose stop app
docker compose run --rm --no-deps app python seed_data.py
docker compose start app
```

The seed script creates a demo administrator, providers, customers, categories, services, reviews, and bookings. It prints the administrator login details when it completes. Change the seeded administrator password before using a public deployment; never publish that password in documentation.

### Useful commands

```bash
docker compose ps                         # Container status
docker compose logs -f app                # API logs
docker compose logs -f email-worker       # Background email worker logs
docker compose down                       # Stop containers; keep named volumes
```

## Deploy the API on EC2

The production Compose profile adds Caddy, which obtains and renews the HTTPS certificate for the configured domain.

1. Point your DuckDNS hostname at the EC2 public IP and allow inbound TCP ports **80** and **443** in the EC2 security group.
2. Configure the EC2 `.env` file with strong database, RabbitMQ, and JWT secrets. Set `PUBLIC_DOMAIN` to the hostname only (for example, `locabazaar-ritish.duckdns.org`), and set `FRONTEND_URL` and `CORS_ORIGINS` to the deployed Vercel origin (for example, `https://loca-bazaar-frontend.vercel.app`).
3. Start the production stack:

   ```bash
   sudo docker compose --profile production up --build -d
   ```

4. Set `NEXT_PUBLIC_API_URL` in the Vercel project to `https://locabazaar-ritish.duckdns.org/api/v1`, then redeploy the frontend.

The backend Compose file keeps PostgreSQL, Redis, and RabbitMQ on the private Docker network. The API is published only on the EC2 loopback interface; Caddy handles public HTTPS traffic.

## Repository layout

```text
app/
├── api/v1/endpoints/   # Authentication, services, bookings, reviews, uploads, admin
├── core/               # Settings, security, cache, and message broker
├── db/                 # SQLAlchemy engines and sessions
├── models/             # Database models
├── schemas/             # Request and response validation
├── services/            # Application and email logic
└── workers/             # RabbitMQ email consumer
tests/                   # Backend tests
Dockerfile
docker-compose.yml
seed_data.py
```

## API

The interactive API schema is available at `/docs`. The main route groups are `/api/v1/auth`, `/api/v1/services`, `/api/v1/categories`, `/api/v1/providers`, `/api/v1/bookings`, `/api/v1/reviews`, `/api/v1/uploads`, and `/api/v1/admin`.
