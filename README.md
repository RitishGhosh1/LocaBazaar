# ProLink 🛠️
**A Professional Hyperlocal Service Marketplace Backend**

ProLink is a high-performance, asynchronous REST API designed to connect local service providers with customers. Built with **FastAPI**, **PostgreSQL**, and **Redis**, it features a robust 3NF normalized database architecture and role-based access control.

---

## 🚀 Key Features

- **Role-Based Access Control (RBAC)**: Dedicated workflows and permissions for **Customers**, **Providers**, and **Admins**.
- **Service Management**: Providers can list, update, and manage their service offerings with categorization.
- **Advanced Booking System**: Seamless booking flow from request to completion.
- **Verified Reviews**: Integrity-focused review system—customers can only review services after a verified `COMPLETED` booking.
- **Dynamic Search & Filtering**: Optimized PostgreSQL queries for filtering by categories, price ranges, and keywords.
- **Async Architecture**: Leverages `SQLAlchemy 2.0` and `asyncpg` for non-blocking database operations.
- **Authentication**: Secure JWT-based authentication with support for Google OAuth2.
- **Caching**: Integrated Redis for performance optimization.

---

## 🏗️ Tech Stack

- **Framework**: [FastAPI](https://fastapi.tiangolo.com/) (Python 3.14+)
- **Database**: [PostgreSQL](https://www.postgresql.org/)
- **ORM**: [SQLAlchemy 2.0](https://www.sqlalchemy.org/) (Async)
- **Validation**: [Pydantic V2](https://docs.pydantic.dev/)
- **Authentication**: JWT, [Authlib](https://docs.authlib.org/) (OAuth2)
- **Caching**: [Redis](https://redis.io/)
- **Task Management**: Fully Asynchronous I/O

---

## 📂 Project Structure

```text
prolink/
├── app/
│   ├── api/v1/             # API Routes
│   │   ├── endpoints/      # Resource-specific controllers
│   │   └── api.py          # Main router configuration
│   ├── core/               # Configuration, security, and global settings
│   ├── db/                 # Database session and engine setup
│   ├── models/             # SQLAlchemy database models
│   ├── schemas/            # Pydantic data validation schemas
│   └── main.py             # Application entry point
├── seed.py                 # Initial data seeding script
├── pyproject.toml          # Project metadata and dependencies
├── requirements.txt        # Python dependencies
└── .env                    # Environment variables (not committed)
```

---

## 🛠️ Local Setup

### Prerequisites
- Python 3.14+
- PostgreSQL
- Redis server

### 1. Clone the Repository
```bash
git clone <repository-url>
cd prolink
```

### 2. Configure Environment
Create a `.env` file in the root directory and populate it with the following:

```env
# Database Configuration
DB_USER=your_user
DB_PASSWORD=your_password
DB_HOST=localhost
DB_PORT=5432
DB_NAME=prolink

# JWT Configuration
SECRET_KEY=your_super_secret_key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# OAuth (Optional)
GOOGLE_CLIENT_ID=your_google_id
GOOGLE_CLIENT_SECRET=your_google_secret
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
# OR if using uv
uv sync
```

### 4. Initialize Database & Seed Data
The project uses SQLAlchemy's `create_all` to initialize the database schema on startup. To populate the database with initial categories and data, run:

```bash
python seed.py
```

### 5. Run the Application
```bash
uvicorn app.main:app --reload
```

---

## 📖 API Documentation

Once the server is running, you can access the interactive API documentation:

- **Swagger UI**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **ReDoc**: [http://localhost:8000/redoc](http://localhost:8000/redoc)

---

## 🧪 Testing

The project uses `pytest` for testing. Run the test suite with:

```bash
pytest
```
