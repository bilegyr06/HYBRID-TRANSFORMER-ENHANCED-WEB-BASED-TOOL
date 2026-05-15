# Quick Start Guide

## 🚀 Getting Started (5 minutes)

### Backend Setup

```bash
cd backend

# 1. Install Python dependencies
pip install -r requirements.txt

# 2. Initialize database (creates SQLite)
alembic upgrade head

# 3. Start backend server
python -m uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

✅ Backend running at: **http://localhost:8000**  
📚 API docs at: **http://localhost:8000/docs**

### Frontend Setup

```bash
cd frontend

# 1. Install Node dependencies
npm install  # (zustand already added)

# 2. Start development server
npm run dev
```

✅ Frontend running at: **http://localhost:5173**

---

## 📝 First Test: Registration & Login

1. **Open** `http://localhost:5173` in browser
2. **You're redirected to login page** (no session yet)
3. **Click** "Create a new account"
4. **Fill registration form:**
   - Email: `test@example.com`
   - Password: `password123` (8+ characters)
   - Full Name: `Test User`
5. **Click** "Create Account"
6. **✅ Redirected to dashboard**
   - Sidebar shows your name and email
   - Welcome message displays
7. **Test logout:** Click "Logout" in sidebar
8. **Test login:** Use same email/password to login again
9. **✅ Session persists** across page refreshes

---

## 💾 Saving & Viewing Reviews

1. **Upload files:**
   - Click "Upload & Process"
   - Drag-drop or select PDF/TXT files
   - Click "Process"

2. **Save review:**
   - After processing, results appear
   - Enter optional review title
   - Click "Save Review"
   - ✅ Success message appears

3. **View saved reviews:**
   - Click "My Reviews" in sidebar
   - See list of all your saved reviews
   - Click review to view full details
   - Click delete to remove review

---

## 🔑 Environment Configuration

Edit `backend/.env` if needed:

```
DATABASE_URL=sqlite:///./litreview.db
JWT_SECRET_KEY=your-secret-key-here  # Change in production!
JWT_ALGORITHM=HS256
JWT_EXPIRATION_HOURS=8760
```

Or for PostgreSQL (optional):
```
DATABASE_URL=postgresql://user:password@localhost/litreview_db
```

---

## 🛠️ Database Management

### View database structure
```bash
cd backend
sqlite3 litreview.db ".schema"
```

### Reset database (start fresh)
```bash
cd backend
rm litreview.db  # Delete file
alembic upgrade head  # Recreate tables
```

### Create new migration (after model changes)
```bash
cd backend
alembic revision --autogenerate -m "describe your changes"
alembic upgrade head
```

---

## 🧪 Testing Endpoints (via Swagger)

1. Go to `http://localhost:8000/docs`
2. **Register:** Try `/auth/register` with test data
3. **Login:** Try `/auth/login`  
4. **Get Me:** Try `/auth/me` (shows logged-in user)
5. **Get Reviews:** Try `GET /reviews/` (shows your saved reviews)
6. **Save Review:** Try `POST /reviews/save` with test data
7. Click "Authorize" button to use token

---

## 🐛 Troubleshooting

### Backend won't start
```bash
# Check if backend dependencies installed
pip list | grep sqlalchemy

# Reinstall dependencies
pip install -r requirements.txt --force-reinstall
```

### Database error: "unable to open database file"
```bash
# Check file permissions
ls -la backend/litreview.db

# Recreate database
rm backend/litreview.db
cd backend && alembic upgrade head
```

### Frontend won't start
```bash
# Clear node_modules and reinstall
rm -rf frontend/node_modules
cd frontend && npm install
npm run dev
```

### Login not working
1. Check backend is running (`http://localhost:8000/docs` accessible)
2. Check browser console for errors (F12)
3. Verify `.env` has `JWT_SECRET_KEY` set
4. Try registering new account instead

### Can't save reviews
1. Make sure you're logged in (see user email in sidebar)
2. Check backend is running
3. Backend console should show POST `/reviews/save` request
4. Browser console (F12) should show response or error

---

## 📊 Database Tables

### Users
```sql
SELECT * FROM users;
```

### SavedReviews  
```sql
SELECT id, user_id, title, created_at FROM saved_reviews;
```

---

## 🔐 Security Reminders

✅ **DO:**
- Change `JWT_SECRET_KEY` in production
- Use HTTPS in production
- Rotate secrets regularly

❌ **DON'T:**
- Commit `.env` to Git
- Use default secrets
- Store passwords in plain text
- Expose JWT_SECRET_KEY

---

## 📖 Full Documentation

- **Backend Setup**: See `backend/SETUP.md`
- **API Endpoints**: See `backend/SETUP.md` (extensive examples)
- **Implementation Details**: See root `IMPLEMENTATION_COMPLETE.md`

---

## 🎯 What's Running

| Component | URL | Purpose |
|-----------|-----|---------|
| Backend API | http://localhost:8000 | FastAPI server |
| Swagger Docs | http://localhost:8000/docs | Interactive API testing |
| Frontend | http://localhost:5173 | React app |
| SQLite DB | `backend/litreview.db` | User & review data |

---

## ✨ Features

✅ User registration & login  
✅ Session persistence (httpOnly cookies)  
✅ Save literature reviews to database  
✅ View saved reviews (paginated)  
✅ Delete reviews  
✅ Secure password hashing (bcrypt)  
✅ JWT authentication  
✅ User ownership isolation  
✅ Responsive UI (mobile + desktop)  
✅ Type-safe code (TypeScript + Pydantic)  

---

## 🚢 Ready for Deployment

Backend and frontend are production-ready. Before final deployment:

1. ✅ Set `JWT_SECRET_KEY` to secure random value
2. ✅ Enable HTTPS
3. ✅ Update `allow_origins` in `src/main.py` CORS config
4. ✅ Review security checklist in `backend/SETUP.md`
5. ✅ Consider PostgreSQL for prod database
6. ✅ Setup environment variables on server

---

**Happy coding! 🎉**
