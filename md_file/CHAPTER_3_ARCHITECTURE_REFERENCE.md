# Chapter 3 Architecture Reference: Authentication & Persistence Layer

## For Thesis Writing

Use this section as reference when writing Chapter 3 - System Architecture. This describes the supporting authentication and database persistence features that complement the core hybrid summarization pipeline.

---

## 1. System Overview

The literature review assistant comprises two primary components:

### Primary Component: Hybrid Summarization Pipeline
- **Extractive stage**: TextRank keyword extraction with research-aware biases (position, structure, keyword)
- **Abstractive stage**: Fine-tuned transformer model (BART/T5) for summary generation
- **Cross-document synthesis**: Multi-document aggregation and synthesis
- **Evaluation**: ROUGE metrics (ROUGE-1, ROUGE-2, ROUGE-L) for quality assessment

### Supporting Component: Authentication & Persistence Layer
- **User management**: Account registration and login with secure password handling
- **Session management**: Stateless JWT tokens stored in secure cookies
- **Review persistence**: Database-backed storage of summaries, themes, and evaluation metrics
- **User isolation**: Single-user model ensuring data privacy and access control

---

## 2. Architecture Diagram (ASCII)

```
┌─────────────────────────────────────────────────────────────┐
│                    Frontend (React + TypeScript)            │
│                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌─────────────────┐  │
│  │ Auth Pages   │  │ Upload Page  │  │ Results Page    │  │
│  │ (Login/Reg)  │  │ (File Input) │  │ (Summaries)     │  │
│  └──────────────┘  └──────────────┘  └─────────────────┘  │
│         │                  │                   │             │
│         └─────────────────────────────────────┘             │
│                    Zustand Auth Store                       │
│              (Session, User State, Callbacks)               │
└────────────┬────────────────────────────────────────────────┘
             │ HTTP Requests (JWT in httpOnly Cookie)
             │
┌────────────┴────────────────────────────────────────────────┐
│              Backend (FastAPI + Python)                     │
│                                                              │
│  ┌────────────────────────────────────────────────────────┐│
│  │           Authentication Layer                        ││
│  │  ┌──────────────────┐  ┌──────────────────────────┐  ││
│  │  │ JWT Validation   │  │ Credential Verification  │  ││
│  │  │ (dependencies.py)│  │ (auth_service.py)       │  ││
│  │  └──────────────────┘  └──────────────────────────┘  ││
│  │         ▲                       ▲                      ││
│  │         │                       │                      ││
│  │  /auth/register    /auth/login   /auth/me   /auth/logout
│  │  /auth/register    /auth/login   /auth/me   /auth/logout
│  └────────────────────────────────────────────────────────┘│
│                           ▼                                 │
│  ┌────────────────────────────────────────────────────────┐│
│  │           Review Persistence Layer                    ││
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐ ││
│  │  │ Save Review  │  │ List Reviews │  │ Delete Review│ ││
│  │  │ (POST /save) │  │ (GET /)      │  │ (DELETE /:id)│ ││
│  │  └──────────────┘  └──────────────┘  └──────────────┘ ││
│  └────────────────────────────────────────────────────────┘│
│                           ▼                                 │
│  ┌────────────────────────────────────────────────────────┐│
│  │        Hybrid Summarization Pipeline                  ││
│  │  TextRank → BART Abstractive → Synthesis → Metrics    ││
│  │  /api/upload  /api/process  /api/extract-themes      ││
│  └────────────────────────────────────────────────────────┘│
│                           ▼                                 │
│  ┌────────────────────────────────────────────────────────┐│
│  │           SQLAlchemy ORM Layer                        ││
│  │          (Database Abstraction)                       ││
│  └────────────────────────────────────────────────────────┘│
│                           ▼                                 │
│  ┌────────────────────────────────────────────────────────┐│
│  │       SQLite Database (or PostgreSQL)                 ││
│  │    ┌────────────────┐  ┌──────────────────────┐       ││
│  │    │ Users Table    │  │ SavedReviews Table   │       ││
│  │    │ (id, email,    │  │ (id, user_id,       │       ││
│  │    │  password,     │  │  extractive_summary,│       ││
│  │    │  full_name...)│  │  abstractive_summary,│       ││
│  │    │                │  │  key_themes, ROUGE) │       ││
│  │    └────────────────┘  └──────────────────────┘       ││
│  └────────────────────────────────────────────────────────┘│
└──────────────────────────────────────────────────────────────┘
```

---

## 3. Database Schema

### Users Table
| Column | Type | Constraints | Purpose |
|--------|------|-------------|---------|
| id | INT | PRIMARY KEY | Unique user identifier |
| email | VARCHAR | UNIQUE, NOT NULL | Login credential |
| hashed_password | VARCHAR | NOT NULL | Bcrypt-hashed password |
| full_name | VARCHAR | NULLABLE | Display name |
| created_at | DATETIME | NOT NULL | Account creation timestamp |
| last_login | DATETIME | NULLABLE | Last activity timestamp |

**Indexes:** `idx_users_email` on `email` (fast login lookups)

### SavedReviews Table
| Column | Type | Constraints | Purpose |
|--------|------|-------------|---------|
| id | INT | PRIMARY KEY | Unique review identifier |
| user_id | INT | FOREIGN KEY → users(id) ON DELETE CASCADE | Review owner |
| title | VARCHAR | NULLABLE, MAX 500 | User-provided label |
| input_abstracts_count | INT | NOT NULL | Document count |
| extractive_summary | TEXT | NULLABLE | TextRank output |
| abstractive_summary | TEXT | NULLABLE | BART/T5 output |
| key_themes | JSON | NULLABLE | TF-IDF extracted themes |
| visualizations_metadata | JSON | NULLABLE | Metadata for charts/graphs |
| rouge_scores | JSON | NULLABLE | ROUGE-1, ROUGE-2, ROUGE-L |
| created_at | DATETIME | NOT NULL | Review timestamp |
| updated_at | DATETIME | NOT NULL | Last modification |

**Indexes:** `idx_saved_reviews_user_id` (user queries), `idx_saved_reviews_created_at` (sorting)

**Relationships:**
- One User → Many SavedReviews
- Cascade delete: User deletion removes all their reviews

---

## 4. Authentication Flow

### 4.1 Registration

**Sequence:**
1. User submits email, password, full_name via POST `/auth/register`
2. Backend validates:
   - Email format and uniqueness
   - Password length (minimum 8 characters)
3. Backend hashes password using bcrypt (passlib library)
4. Creates User record in database with:
   - Generated bcrypt hash (not plain password)
   - Email and full_name
   - created_at timestamp
5. Generates JWT token with user_id claim
6. Sets token in httpOnly cookie (secure, sameSite=Lax)
7. Returns AuthResponse with token and user info

**Security:**
- Passwords never logged or transmitted plain-text
- Bcrypt provides cryptographic hashing with salt
- Database stores only hashes
- httpOnly cookies prevent JavaScript access

### 4.2 Login

**Sequence:**
1. User submits email + password via POST `/auth/login`
2. Backend queries Users table by email
3. If user found: verifies plain password against stored hash using bcrypt
4. If match:
   - Updates last_login timestamp
   - Generates JWT token
   - Sets secure httpOnly cookie
   - Returns AuthResponse
5. If no match: returns 401 Unauthorized (no user/password info leaked)

**Token Details:**
- Algorithm: HS256 (HMAC with SHA-256)
- Claims: `{"sub": user_id, "exp": expiration_time}`
- Secret Key: JWT_SECRET_KEY from environment (.env)
- Expiration: 1 year (suitable for thesis project, production would use shorter times + refresh tokens)
- Signature: HS256(header.payload, JWT_SECRET_KEY)

### 4.3 Session Restoration

**Sequence:**
1. Frontend mounts → calls `fetchCurrentUser()`
2. GET `/auth/me` request sent with httpOnly cookie
3. Backend extracts token from cookie
4. Calls `decode_access_token(token)` to validate:
   - Token signature (proves integrity with secret key)
   - Token expiration
   - Token format
5. If valid: extracts user_id claim
6. Queries Users table for user
7. Returns UserResponse
8. Frontend sets user in Zustand store
9. User stays logged in across page refreshes

**Cookie Mechanism:**
- Browser automatically sends httpOnly cookies with requests
- Server-side generates Set-Cookie header
- Secure flag: false in dev, true in production (HTTPS only)
- SameSite: Lax (CSRF protection; allows some cross-site get requests)

### 4.4 Logout

1. User clicks Logout
2. POST `/auth/logout` request sent
3. Backend sends Set-Cookie response with empty value, expiration in past
4. Browser deletes cookie
5. Frontend clears Zustand auth store
6. User redirected to login page

---

## 5. Review Persistence Layer

### 5.1 Saving Reviews

**Endpoint:** `POST /reviews/save` (requires JWT authentication)

**Payload:**
```json
{
  "title": "Optional Review Title",
  "input_abstracts_count": 3,
  "extractive_summary": "Key sentences from TextRank...",
  "abstractive_summary": "Generated summary from BART/T5...",
  "key_themes": ["theme1", "theme2", "theme3"],
  "visualizations_metadata": {"chart_id": "...", "network_id": "..."},
  "rouge_scores": {"rouge1": 0.45, "rouge2": 0.32, "rougeL": 0.42}
}
```

**Processing:**
1. JWT dependency extracts user_id from token
2. Creates SavedReview record with:
   - user_id from current user
   - All provided summaries and metrics
   - Automatic created_at/updated_at timestamps
3. Inserts into database
4. Returns SavedReviewResponse with record ID

**Ownership Isolation:**
- SavedReview linked to user_id foreign key
- All subsequent queries filtered by user_id
- Cross-user access returns 403 Forbidden

### 5.2 Retrieving Reviews

**List Reviews:** `GET /reviews/?page=1&page_size=50` (requires JWT)

**Response:**
```json
{
  "reviews": [
    {
      "id": 1,
      "title": "My First Review",
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

**Query Details:**
- Filters: `WHERE user_id = current_user.id`
- Sort: `ORDER BY created_at DESC` (newest first)
- Pagination: `LIMIT {page_size} OFFSET {(page-1)*page_size}`
- Returns: Limited fields for list view (full summaries not included for performance)

**Get Single Review:** `GET /reviews/{review_id}` (requires JWT + ownership check)
- Returns full SavedReviewResponse with all summaries, metrics, themes
- 404 if review_id not found
- 403 if review belongs to different user

### 5.3 Deleting Reviews

**Delete Review:** `DELETE /reviews/{review_id}` (requires JWT + ownership check)

**Processing:**
1. Query SavedReviews by id
2. Verify current user owns review (user_id check)
3. Execute SQL DELETE
4. Return 204 No Content

---

## 6. Technology Stack Rationale

### Backend Framework: FastAPI
- Native async support for concurrent requests
- Automatic Swagger/OpenAPI documentation
- Built-in dependency injection for middleware composition
- Type hints enable runtime validation via Pydantic

### ORM: SQLAlchemy
- Database-agnostic (SQLite + PostgreSQL without code changes)
- SQL injection prevention via parameterized queries
- Relationship management (user ↔ review)
- Migration support (Alembic integration)

### Password Hashing: bcrypt via passlib
- Industry standard for password hashing
- Configurable work factor (CPU-intensive by design)
- Includes salt automatically
- Resistant to GPU attacks due to memory requirements

### JWT Implementation: python-jose
- Standard JWT library (RFC 7519 compliant)
- Signature verification prevents tampering
- Claims-based identity (stateless tokens)
- Compatible with JWT standards (can integrate with other systems)

### Frontend State: Zustand
- Minimal boilerplate vs. Redux
- No provider wrapper per se (can wrap root)
- Middleware support for persistence
- Fast performance, predictable updates

---

## 7. Security Considerations

### Authentication Security
✅ **Password Hashing:**
- Bcrypt with automatic salt
- One-way hash function (irreversible)
- Work factor configured in passlib

✅ **JWT Tokens:**
- HMAC-SHA256 signature prevents tampering
- Token verification requires JWT_SECRET_KEY
- Expiration enforced at decode time
- Stateless (no server-side session storage needed)

✅ **Cookie Security:**
- httpOnly flag prevents JavaScript access (XSS protection)
- SameSite=Lax prevents CSRF attacks
- Secure flag enforced in production (HTTPS only)

### Database Security
✅ **SQL Injection Prevention:**
- SQLAlchemy ORM uses parameterized queries
- No string concatenation in SQL
- User input never directly interpolated

✅ **Referential Integrity:**
- Foreign key constraints enforce user_id validity
- Cascade delete ensures no orphaned reviews
- Database enforces constraints at engine level

### Authorization Security
✅ **Ownership Verification:**
- Every protected endpoint checks current_user vs. resource owner
- 403 Forbidden returned for unauthorized access
- Client cannot bypass checks (server-side validation)

### Remaining Risks & Mitigations
⚠️ **Risk**: Token expiration not enforced in dev (1 year)  
→ **Mitigation**: Suitable for thesis/testing; production would use shorter expiration + refresh tokens

⚠️ **Risk**: No rate limiting on auth endpoints  
→ **Mitigation**: Could add rate limiter middleware in production

⚠️ **Risk**: Environment variables in .env file  
→ **Mitigation**: .env not committed to Git; production uses managed secrets

---

## 8. Data Flow: End-to-End Review Saving

1. **User uploads files** via React interface
2. **Frontend sends file** → `POST /api/upload`
3. **Backend processes:**
   - Stores file temporarily
   - Extracts text (PDF or plaintext)
   - Returns file list with preview
4. **User clicks "Process"**
5. **Frontend sends filenames** → `POST /api/process`
6. **Backend runs pipeline:**
   - TextRank extracts key sentences
   - BART generates abstractive summary
   - TF-IDF extracts themes
   - ROUGE calculates metrics
7. **Results displayed** on frontend
8. **User enters optional title & clicks "Save"**
9. **Frontend sends** → `POST /reviews/save` with:
   - Authorization header (JWT in httpOnly cookie)
   - Extractive summary (TextRank output)
   - Abstractive summary (BART output)
   - Themes (TF-IDF output)
   - ROUGE scores (metrics)
10. **Backend receives (protected endpoint):**
    - Extracts current_user from JWT token
    - Creates SavedReview with user_id
    - Commits to database
    - Returns review_id
11. **Frontend confirms:** "Review saved successfully!"
12. **User navigates to "My Reviews"**
13. **Frontend sends** → `GET /reviews/?page=1`
14. **Backend queries:** `SELECT * FROM saved_reviews WHERE user_id = ? ORDER BY created_at DESC`
15. **Backend returns:** Paginated list of user's reviews
16. **User selects review** → `GET /reviews/{review_id}`
17. **Backend verifies ownership** (current_user.id == review.user_id)
18. **Returns full review** with all summaries and metrics
19. **User can delete** → `DELETE /reviews/{review_id}`
20. **Backend deletes** record and soft-deletes from user's review list

---

## 9. Limitations & Scope

### Design Limitations (By Requirement)
- **Single-user model**: Each user sees only their reviews
- **No sharing**: Reviews cannot be shared between users
- **No password reset**: Users cannot recover deleted accounts (thesis scope)
- **No email verification**: Emails assumed valid
- **No social login**: Google, GitHub integration not included
- **No RBAC**: No admin/reviewer/contributor roles

### Operational Limitations
- **SQLite in development**: Suitable for single-user thesis testing
- **No backup strategy**: Thesis project focused on functionality, not ops
- **No audit logging**: Security events not logged
- **Manual secret rotation**: JWT_SECRET_KEY changed manually (ops issue)

### Performance Limitations
- **No caching**: All queries hit database
- **No indexing strategy**: Suitable for thesis scale but would need optimization at scale
- **Synchronous ORM**: FastAPI async with blocking SQLAlchemy calls (could use async SQLAlchemy)
- **No pagination optimization**: Offset-based (works well for <10k reviews)

---

## 10. Future Enhancements

After thesis submission, potential improvements:

1. **Token Refresh Flow**: Short-lived access tokens + long-lived refresh tokens
2. **Rate Limiting**: Prevent brute-force attacks on auth endpoints  
3. **Audit Logging**: Track login, review creation, deletions for security
4. **Email Verification**: Confirm email ownership before account activation
5. **Password Reset**: Send reset link via email
6. **2FA**: Two-factor authentication support
7. **Multi-User Collaboration**: Shared reviews with comment threads
8. **Export Functionality**: Download reviews as PDF or markdown
9. **Search & Filters**: Find reviews by title, theme, date range
10. **Analytics Dashboard**: User's review statistics (average ROUGE, themes over time)

---

## 11. Reproducibility & Documentation

### For Readers Replicating the System
1. **Database Migrations**: Alembic ensures schema is reproducible
   - `alembic upgrade head` creates exact same schema
   - Version control tracks all schema changes

2. **Dependency Management**: `requirements.txt` pins all versions
   - Exact package versions ensure reproducibility
   - No "latest" dependencies that change

3. **Configuration**: `.env.example` documents all required variables
   - Any reader can copy and configure for their environment

4. **Documentation**: `SETUP.md` and `QUICKSTART.md` provide step-by-step instructions
   - Anyone can follow instructions to get system running
   - No hidden assumptions or manual steps

---

## 12. Conclusion

The authentication and persistence layer provides a lightweight but secure foundation for user account management and review storage. It maintains separation of concerns with the core hybrid summarization pipeline while providing necessary functionality for a thesis project with user workflows. The implementation prioritizes security best practices (bcrypt hashing, JWT validation, ownership verification) while remaining simple and thesis-appropriate in scope (no multi-user collaboration, sharing, or complex IAM).

---

**Use this entire section as your Chapter 3 reference when writing about system architecture.**
