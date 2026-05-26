# Backend Setup Guide: Authentication & Database

This guide documents the database initialization and authentication configuration for the Hybrid Transformer-Enhanced Literature Review Assistant backend.

## Quick Start

### 1. Environment Configuration

Copy `.env.example` to `.env` and configure:

```bash
cp .env.example .env
```

Edit `.env` with your settings:

```
# Database Configuration
DATABASE_URL=sqlite:///./litreview.db
# For PostgreSQL: postgresql://user:password@localhost/litreview_db

# JWT Authentication
JWT_SECRET_KEY=your-secret-key-here-change-in-production
JWT_ALGORITHM=HS256
JWT_EXPIRATION_HOURS=8760
```

### 2. Generate a Secure JWT Secret Key

For production deployments, generate a cryptographically secure secret:

```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

Copy the output into `JWT_SECRET_KEY` in your `.env` file.

### 3. Initialize the Database

Run Alembic migrations to create the database schema:

```bash
# From the backend/ directory
alembic upgrade head
```

This creates:
- **SQLite database** at `./litreview.db` (or your configured DATABASE_URL)
- **Users table**: email, hashed_password, full_name, created_at, last_login
- **SavedReviews table**: review metadata, summaries, themes, ROUGE scores, user_id foreign key

### 4. Start the Backend Server

```bash
# From the backend/ directory
python -m uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

The server starts with initialized database tables and is ready for authentication requests.

---

## Database Schema

### Users Table

```sql
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email VARCHAR(255) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    full_name VARCHAR(255),
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    last_login DATETIME
);

CREATE INDEX idx_users_email ON users(email);
```

### SavedReviews Table

```sql
CREATE TABLE saved_reviews (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    title VARCHAR(500),
    input_abstracts_count INTEGER NOT NULL,
    extractive_summary TEXT,
    abstractive_summary TEXT,
    key_themes JSON,
    visualizations_metadata JSON,
    rouge_scores JSON,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE INDEX idx_saved_reviews_user_id ON saved_reviews(user_id);
CREATE INDEX idx_saved_reviews_created_at ON saved_reviews(created_at);
```

---

## Authentication Endpoints

### 1. Register New User

```http
POST /auth/register
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "secure_password_8+_chars",
  "full_name": "John Doe"
}
```

**Response (201 Created):**
```json
{
  "access_token": "eyJhbGc...",
  "token_type": "bearer",
  "user": {
    "id": 1,
    "email": "user@example.com",
    "full_name": "John Doe",
    "created_at": "2026-04-16T10:00:00",
    "last_login": null
  }
}
```

Token returned in secure `httpOnly` cookie: `Set-Cookie: access_token=...; HttpOnly; SameSite=Lax`

### 2. Login

```http
POST /auth/login
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "secure_password_8+_chars"
}
```

**Response (200 OK):**
```json
{
  "access_token": "eyJhbGc...",
  "token_type": "bearer",
  "user": {
    "id": 1,
    "email": "user@example.com",
    "full_name": "John Doe",
    "created_at": "2026-04-16T10:00:00",
    "last_login": "2026-04-16T11:30:00"
  }
}
```

Token returned in secure httpOnly cookie. Updates `last_login` timestamp.

### 3. Get Current User

```http
GET /auth/me
Cookie: access_token=eyJhbGc...
```

**Response (200 OK):**
```json
{
  "id": 1,
  "email": "user@example.com",
  "full_name": "John Doe",
  "created_at": "2026-04-16T10:00:00",
  "last_login": "2026-04-16T11:30:00"
}
```

### 4. Logout

```http
POST /auth/logout
Cookie: access_token=eyJhbGc...
```

**Response (200 OK):**
```json
{
  "message": "Successfully logged out"
}
```

Clears `access_token` cookie.

---

## Review Endpoints

All review endpoints require authentication (valid JWT in httpOnly cookie).

### 1. Save a Review

```http
POST /reviews/save
Content-Type: application/json
Cookie: access_token=eyJhbGc...

{
  "title": "My First Literature Review",
  "input_abstracts_count": 3,
  "extractive_summary": "Key points from TextRank...",
  "abstractive_summary": "BART-generated summary...",
  "key_themes": ["AI", "NLP", "summarization"],
  "visualizations_metadata": {"network_graph": "data_url"},
  "rouge_scores": {"rouge1": 0.45, "rouge2": 0.32, "rougeL": 0.42}
}
```

**Response (201 Created):**
```json
{
  "id": 1,
  "user_id": 1,
  "title": "My First Literature Review",
  "input_abstracts_count": 3,
  "extractive_summary": "...",
  "abstractive_summary": "...",
  "key_themes": ["AI", "NLP", "summarization"],
  "visualizations_metadata": {...},
  "rouge_scores": {...},
  "created_at": "2026-04-16T11:30:00",
  "updated_at": "2026-04-16T11:30:00"
}
```

### 2. List User's Reviews

```http
GET /reviews/?page=1&page_size=50
Cookie: access_token=eyJhbGc...
```

**Response (200 OK):**
```json
{
  "reviews": [
    {
      "id": 1,
      "title": "My First Literature Review",
      "input_abstracts_count": 3,
      "created_at": "2026-04-16T11:30:00",
      "updated_at": "2026-04-16T11:30:00"
    }
  ],
  "total_count": 1,
  "page": 1,
  "page_size": 50,
  "has_more": false
}
```

### 3. Get Single Review

```http
GET /reviews/1
Cookie: access_token=eyJhbGc...
```

**Response (200 OK):**
Full review with all summaries and metrics.

### 4. Delete Review

```http
DELETE /reviews/1
Cookie: access_token=eyJhbGc...
```

**Response (204 No Content)** - Review deleted.

---

## Alembic Migration Management

### Create a New Migration

After modifying SQLAlchemy models, generate a new migration:

```bash
alembic revision --autogenerate -m "describe your changes"
```

This creates a new migration file in `alembic/versions/`.

### View Migration History

```bash
alembic history
```

### Upgrade to Latest Migration

```bash
alembic upgrade head
```

### Downgrade One Step

```bash
alembic downgrade -1
```

### Downgrade to Specific Version

```bash
alembic downgrade 3015d61a4208
```

---

## PostgreSQL Setup (Optional)

For production-like testing, you can use PostgreSQL instead of SQLite:

### 1. Install PostgreSQL Adapter

```bash
pip install psycopg2-binary
```

### 2. Create Database

```bash
createdb litreview_db
```

### 3. Update DATABASE_URL in .env

```
DATABASE_URL=postgresql://postgres:password@localhost/litreview_db
```

### 4. Run Migrations

```bash
alembic upgrade head
```

---

## Security Best Practices

### Password Hashing

- Passwords are hashed using **bcrypt** (passlib) with secure salt rounds
- Never log or store plain-text passwords
- Verify passwords using `hash_password()` and `verify_password()` functions

### JWT Tokens

- Tokens are stored in **httpOnly cookies** (not accessible via JavaScript)
- Set `Secure` flag in production (HTTPS only)
- Set `SameSite=Lax` to prevent CSRF attacks
- Default expiration: 1 year (non-expiring for thesis project)

### SQL Injection Prevention

- **SQLAlchemy ORM** prevents SQL injection via parameterized queries
- All database operations use ORM models, not raw SQL

### CORS Configuration

- Frontend restricted to `http://localhost:5173` (Vite dev server)
- Update `allow_origins` in `src/main.py` for production deployments
- Credentials enabled (`allow_credentials=True`) for cookie transmission

---

## Troubleshooting

### Issue: "sqlalchemy.exc.OperationalError: unable to open database file"

**Solution**: Ensure directory path is writable and `DATABASE_URL` is correct.

### Issue: "JWT token validation failed"

**Solution**: 
1. Verify `JWT_SECRET_KEY` matches across all instances
2. Check token expiration time in Swagger UI
3. Ensure cookies are being sent with requests (`credentials: 'include'` in fetch/axios)

### Issue: "Duplicate key value violates unique constraint"

**Solution**: Email already registered. Use different email or reset database with `alembic downgrade -1` then `alembic upgrade head`.

### Issue: Password hashing errors

**Solution**: 
1. Verify `passlib[bcrypt]` is installed: `pip install passlib[bcrypt]`
2. Check Python version (3.8+ required)

---

## Supporting Feature Note

This authentication and persistence layer is a **supporting feature** of the Hybrid Transformer-Enhanced Literature Review Assistant. The primary focus remains the hybrid extractive-abstractive summarization pipeline (TextRank + fine-tuned BART/T5).

See Chapter 3 of the thesis for architecture documentation.
