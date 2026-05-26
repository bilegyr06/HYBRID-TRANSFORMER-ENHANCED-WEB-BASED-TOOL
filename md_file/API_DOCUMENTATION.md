# API Documentation (Phase 3.3)

**Hybrid Transformer-Enhanced Literature Review Assistant**

Base URL: `http://localhost:8000/api` (development)

## Overview

This API provides endpoints for user authentication, profile management, document analysis, and literature review persistence. All endpoints use JWT-based authentication with tokens stored in secure httpOnly cookies.

### Authentication

All endpoints (except `/auth/register` and `/auth/login`) require Bearer token authentication:

```
Authorization: Bearer <jwt_token>
```

Tokens are automatically set in httpOnly cookies on successful login/registration and are valid for 24 hours.

---

## Endpoints by Category

### Authentication (`/auth`)

#### POST `/auth/register`
Register a new user account.

**Request:**
```json
{
  "email": "user@company.com",
  "password": "SecurePass123",
  "full_name": "John Doe"
}
```

**Response (201):**
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "token_type": "bearer",
  "user": {
    "id": 1,
    "email": "user@company.com",
    "full_name": "John Doe",
    "created_at": "2026-05-26T10:00:00"
  }
}
```

**Errors:**
- `400` - Invalid email (format or disposable service)
- `409` - Email already registered
- `422` - Validation error (password too weak, name too long)

**Security Notes:**
- Email must not be from disposable service (tempmail, etc.)
- Password must be 8-72 characters with uppercase, lowercase, and digits
- Tokens expire after 24 hours
- Token set in httpOnly cookie (HTTPS only in production)

---

#### POST `/auth/login`
Authenticate existing user and obtain JWT token.

**Request:**
```json
{
  "email": "user@company.com",
  "password": "SecurePass123"
}
```

**Response (200):**
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "token_type": "bearer",
  "user": {
    "id": 1,
    "email": "user@company.com",
    "full_name": "John Doe",
    "created_at": "2026-05-26T10:00:00",
    "last_login": "2026-05-26T10:05:00"
  }
}
```

**Errors:**
- `401` - Invalid credentials
- `429` - Too many login attempts (5/15 minutes per IP)

**Security Notes:**
- Rate limited to 5 attempts per 15 minutes per IP
- Error messages are generic (no user enumeration)
- Password verified with Argon2
- Last login timestamp updated

---

#### POST `/auth/logout`
Invalidate current JWT token and logout user.

**Response (200):**
```json
{
  "message": "Successfully logged out"
}
```

**Security Notes:**
- Clears httpOnly cookie on client
- Token expires after 24 hours if not cleared

---

### User Profile (`/api/profile`) - Phase 3.1

#### GET `/api/profile`
Retrieve authenticated user's complete profile.

**Response (200):**
```json
{
  "id": 1,
  "email": "user@company.com",
  "full_name": "John Doe",
  "bio": "Research scientist specializing in NLP",
  "avatar_url": "https://example.com/avatars/user123.jpg",
  "organization": "Tech Research Lab",
  "is_active": true,
  "created_at": "2026-05-26T10:00:00",
  "last_login": "2026-05-26T10:05:00",
  "profile_updated_at": "2026-05-26T10:10:00"
}
```

**Errors:**
- `401` - Missing or invalid token
- `404` - User not found

---

#### PUT `/api/profile`
Update authenticated user's profile information.

**Request:**
```json
{
  "full_name": "Jane Doe",
  "bio": "Senior ML researcher",
  "avatar_url": "https://example.com/avatars/jane.jpg",
  "organization": "AI Institute"
}
```

**Response (200):**
```json
{
  "id": 1,
  "email": "user@company.com",
  "full_name": "Jane Doe",
  "bio": "Senior ML researcher",
  "avatar_url": "https://example.com/avatars/jane.jpg",
  "organization": "AI Institute",
  "is_active": true,
  "created_at": "2026-05-26T10:00:00",
  "profile_updated_at": "2026-05-26T11:00:00"
}
```

**Field Constraints:**
- `full_name`: max 255 characters
- `bio`: max 500 characters
- `organization`: max 255 characters
- `avatar_url`: must start with `http://` or `https://`

**Errors:**
- `400` - Invalid data (e.g., invalid URL format)
- `401` - Missing or invalid token
- `422` - Validation error (field too long)
- `500` - Database error

---

#### GET `/api/profile/stats`
Get user account statistics and review metrics.

**Response (200):**
```json
{
  "total_reviews": 42,
  "last_review_date": "2026-05-26T09:30:00",
  "account_age_days": 180,
  "member_since": "2026-05-26T10:00:00"
}
```

**Fields:**
- `total_reviews`: Total number of saved reviews
- `last_review_date`: Timestamp of most recent review (null if no reviews)
- `account_age_days`: Days since account creation
- `member_since`: ISO timestamp of account creation

**Errors:**
- `401` - Missing or invalid token
- `404` - User not found

---

### Reviews (`/reviews`)

#### GET `/api/reviews`
List all reviews for authenticated user (paginated).

**Query Parameters:**
- `skip`: Number of reviews to skip (default: 0)
- `limit`: Maximum reviews to return (default: 10, max: 100)

**Response (200):**
```json
[
  {
    "id": 1,
    "title": "Review Title",
    "created_at": "2026-05-26T10:00:00"
  }
]
```

---

#### POST `/api/reviews/save`
Save a new review (synthesis result).

**Request:**
```json
{
  "title": "ML Architecture Review",
  "synthesis": "Summary of analyzed papers...",
  "papers": [{"title": "Paper 1", "abstract": "..."}]
}
```

**Response (201):**
```json
{
  "id": 1,
  "title": "ML Architecture Review",
  "owner_id": 1,
  "created_at": "2026-05-26T10:00:00"
}
```

---

#### GET `/api/reviews/{review_id}`
Retrieve specific review by ID.

**Response (200):**
```json
{
  "id": 1,
  "title": "Review Title",
  "synthesis": "...",
  "created_at": "2026-05-26T10:00:00"
}
```

**Errors:**
- `401` - Not authenticated
- `403` - Not review owner
- `404` - Review not found

---

#### DELETE `/api/reviews/{review_id}`
Delete a review (owner only).

**Response (200):**
```json
{
  "message": "Review deleted successfully"
}
```

**Errors:**
- `401` - Not authenticated
- `403` - Not review owner
- `404` - Review not found

---

### Analysis (`/api/analyze`)

#### POST `/api/analyze/upload`
Upload document for analysis.

**Request:** `multipart/form-data`
- `file`: Document file (PDF, TXT)
- `analysis_type`: "extract" | "summarize" | "synthesize" (optional)

**Response (200):**
```json
{
  "file_id": "upload_abc123",
  "filename": "paper.pdf",
  "size_bytes": 102400,
  "uploaded_at": "2026-05-26T10:00:00"
}
```

**Constraints:**
- File size: max 100MB per file
- Total upload: max 500MB per request
- Allowed types: PDF, TXT, JSONL

**Errors:**
- `400` - Invalid file or exceeds limits
- `413` - Payload too large
- `422` - Unsupported file type

---

#### POST `/api/analyze/process`
Analyze uploaded documents with specified method.

**Request:**
```json
{
  "file_id": "upload_abc123",
  "method": "extract",
  "parameters": {
    "num_sentences": 5
  }
}
```

**Response (200):**
```json
{
  "method": "extract",
  "results": {
    "sentences": ["Sentence 1...", "Sentence 2..."],
    "score": 0.85
  },
  "processed_at": "2026-05-26T10:00:00"
}
```

---

### Synthesis (`/api/synthesize`)

#### POST `/api/synthesize`
Generate synthesis from multiple documents.

**Request:**
```json
{
  "abstracts": ["Abstract 1...", "Abstract 2..."],
  "method": "combined",
  "max_length": 500
}
```

**Response (200):**
```json
{
  "synthesis": "Combined analysis of papers...",
  "method": "combined",
  "source_count": 2,
  "generated_at": "2026-05-26T10:00:00"
}
```

---

## Error Handling

All error responses follow this format:

```json
{
  "detail": "Human-readable error message (generic for security)"
}
```

**Status Codes:**
- `200` OK - Successful GET/PUT
- `201` Created - Successful POST with resource creation
- `400` Bad Request - Invalid input
- `401` Unauthorized - Missing/invalid authentication
- `403` Forbidden - Insufficient permissions (e.g., not review owner)
- `404` Not Found - Resource doesn't exist
- `409` Conflict - Resource already exists (e.g., email registered)
- `422` Unprocessable Entity - Validation error
- `429` Too Many Requests - Rate limit exceeded
- `500` Internal Server Error - Server error (generic message)

**Security Notes:**
- Error messages never expose database paths, IDs, or internal details
- Full error details logged server-side for debugging
- Rate limits return 429 with generic "Too many requests" message

---

## Rate Limiting

- **Login**: 5 attempts per 15 minutes per IP
- **Register**: 3 attempts per 15 minutes per IP
- **Other endpoints**: No limit (protected by authentication)

---

## Authentication Flow

1. **Register** → POST `/auth/register` → Receive JWT in httpOnly cookie
2. **Login** → POST `/auth/login` → Receive JWT in httpOnly cookie
3. **Authenticated Requests** → Include `Authorization: Bearer <token>` or use cookie
4. **Logout** → POST `/auth/logout` → Cookie cleared

JWT expires after 24 hours. Requests with expired token return 401.

---

## API Access

### Documentation UIs
- **Swagger UI**: http://localhost:8000/api/docs
- **ReDoc**: http://localhost:8000/api/redoc
- **OpenAPI JSON**: http://localhost:8000/api/openapi.json

### Example Request (with cURL)
```bash
# Register
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"user@company.com","password":"Pass123","full_name":"John"}'

# Get profile (using token from response)
curl -X GET http://localhost:8000/api/profile \
  -H "Authorization: Bearer <token>"

# Update profile
curl -X PUT http://localhost:8000/api/profile \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"bio":"Updated bio"}'
```

---

## Pagination

Endpoints returning lists support pagination:

**Query Parameters:**
- `skip`: Number of items to skip (default: 0)
- `limit`: Number of items to return (default: 10)

Example: `GET /api/reviews?skip=20&limit=10`

---

## Filtering & Search

Some endpoints support filtering:

**Query Parameters:**
- `search`: Search term for text fields
- `sort`: Sort field ("created_at", "title", etc.)
- `order`: Sort direction ("asc" or "desc")

---

## Versioning

Current API version: **1.0.0**

Future versions will be indicated in response headers:
- `X-API-Version: 1.0.0`

---

## Support & Questions

For issues or questions:
1. Check error message and HTTP status code
2. Review this documentation
3. Check server logs for detailed error information
4. Contact development team with issue details
