# LocaBazaar API 🚀
> **A High-Performance, Distributed Asynchronous Marketplace API Platform.**

LocaBazaar is an enterprise-grade, asynchronous backend platform engineered with **FastAPI** to facilitate multi-provider hyperlocal service discovery, secure scheduling, and zero-trust identity operations. 

---

## 🛠 Tech Stack & Architecture Design

- **Runtime Environment:** Docker Containerization (Multi-stage builds)
- **Application Layer:** FastAPI (Python 3.12, fully Asynchronous concurrency)
- **Primary Database:** PostgreSQL (Managed Cloud Layer via SQLAlchemy 2.0 Async Sessions)
- **Caching Core:** Redis / Render Key-Value (RAM-backed Cache-Aside implementation)
- **Identity Protocol:** OAuth 2.0 & OpenID Connect (OIDC via Google Sign-In)

---

## 💡 System Architecture Highlights

### 1. Zero-Trust Identity Flow (OIDC & Stateless JWT)
- **Delegated Authentication:** Integrated Google Sign-In utilizing OpenID Connect (OIDC) protocols. The system cryptographically validates incoming Google ID Tokens (JWTs) against Google's authorization servers to securely extract verified identity claims without the liability of direct password storage management.
- **Stateless Session Control:** Employs cryptographically signed JSON Web Tokens (JWT) embedded with Role-Based Access Control (RBAC) claims (Customer, Provider, Admin) to enforce permission validation down to the individual endpoint layer without stateful server-side storage lookup bottlenecks.

### 2. High-Performance Sub-10ms Cache-Aside Architecture
- To alleviate read-heavy database strain, service queries hit an in-memory Redis layer first. 
- **Cache Hits:** Served in under 10ms directly from RAM memory maps.
- **Cache Misses:** Lazily fetched from PostgreSQL, committed back to Redis RAM, and cleanly returned to the requester.
- **Read-After-Write Consistency:** Implements a dynamic invalidation layer. Any state-altering structural transaction (`POST`, `PUT`, `DELETE`) automatically fires background events to invalidate matching Redis cache patterns, guaranteeing strict data freshness.

### 3. Infinite Scalability Pagination
- Completely rejects traditional, slow `OFFSET` / `LIMIT` pagination architectures which degrade to $O(N)$ linear time complexities at high volume.
- Utilizes **Cursor-Based Pagination** mapping deterministic, unique chronological indices, maintaining a strict $O(1)$ constant processing speed regardless of database record depths.

### 4. Advanced Security Hardening
- **User Enumeration Defense:** Authentication routines return immutable, generalized error structures (`Authentication Failed`) paired with identical HTTP status structures to prevent analytical malicious account filtering.
- **Timing Attack Mitigation:** Core validation gates enforce intentional execution delays to equalize server processing timelines, neutralizing stopwatch-based account verification indexing tactics.

---

## 🚀 Live Cloud Exploration

- **Interactive Swagger Documentation:** [https://locabazaar-api.onrender.com/docs](https://locabazaar-api.onrender.com/docs)
- **Alternative ReDoc Technical Spec:** [https://locabazaar-api.onrender.com/redoc](https://locabazaar-api.onrender.com/redoc)