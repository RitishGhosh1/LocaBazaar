# ProLink 🛠️
**A Hyperlocal Service Marketplace Backend**

ProLink is a high-performance, asynchronous REST API built with **FastAPI** and **PostgreSQL**. It connects local service providers with customers using a 3NF normalized database architecture.

## 🚀 Key Features
* **Role-Based Access Control (RBAC)**: Distinct flows for Customers, Providers, and Admins.
* **Deep Review Integrity**: Customers can only review services after a `COMPLETED` booking status is verified.
* **Dynamic Search & Filtering**: Complex PostgreSQL joins allow filtering by Category Name, Price Range, and Keyword search simultaneously.
* **Async Architecture**: Fully non-blocking I/O using `SQLAlchemy 2.0` and `asyncpg`.

## 🏗️ Tech Stack
* **Language**: Python 3.12+
* **Framework**: FastAPI
* **Database**: PostgreSQL (Relational)
* **ORM**: SQLAlchemy 2.0 (Async)
* **Validation**: Pydantic V2

## 🛠️ Local Setup
1. Clone the repo: `git clone ...`
2. Create `.env` file (see `.env.example`)
3. Install dependencies: `pip install -r requirements.txt`
4. Run migrations: `alembic upgrade head`
5. Start server: `uvicorn app.main:app --reload`