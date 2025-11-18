# CorpFinity Backend

FastAPI backend for CorpFinity application using Neon Postgres database, deployed on Vercel.

## 🚀 Quick Start

### Local Development

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure environment variables:**
   ```bash
   cp .env.example .env
   ```
   Edit `.env` and add your Neon Postgres connection string and secret key.

3. **Initialize database:**
   ```bash
   python init_db.py
   ```

4. **Run the development server:**
   ```bash
   uvicorn app.main:app --reload
   ```
   
   API available at: `http://localhost:8000`
   
   API docs: `http://localhost:8000/docs`

### Deploy to Vercel

1. **Install Vercel CLI:**
   ```bash
   npm i -g vercel
   ```

2. **Login to Vercel:**
   ```bash
   vercel login
   ```

3. **Deploy:**
   ```bash
   cd backend
   vercel
   ```

4. **Set environment variables in Vercel:**
   ```bash
   vercel env add DATABASE_URL
   vercel env add SECRET_KEY
   ```
   
   Or set them in the Vercel dashboard under Project Settings → Environment Variables.

5. **Deploy to production:**
   ```bash
   vercel --prod
   ```

## 🗄️ Database Configuration

The backend uses **Neon Postgres** with connection pooling optimized for Vercel's serverless environment.

### Required Environment Variables

- `DATABASE_URL` - Neon Postgres connection string (use pooled connection)
- `SECRET_KEY` - JWT secret key (generate a strong random key)
- `JWT_ALGORITHM` - JWT algorithm (default: HS256)
- `ACCESS_TOKEN_EXPIRE_MINUTES` - Access token expiry (default: 30)
- `REFRESH_TOKEN_EXPIRE_MINUTES` - Refresh token expiry (default: 10080)

### Connection Pooling

Optimized for serverless:
- Pool size: 5 connections
- Max overflow: 10 connections
- Pool recycle: 300 seconds
- Pre-ping enabled for connection health checks

## 📡 API Endpoints

### Authentication
- `POST /auth/register` - Register new user
- `POST /auth/login` - Login user
- `POST /auth/refresh` - Refresh access token
- `GET /auth/me` - Get current user

### Challenges
- `GET /challenges` - List all challenges
- `GET /challenges/next` - Get next challenge
- `POST /challenges/{id}/complete` - Mark challenge as complete

### Sessions
- `POST /sessions` - Create new session
- `GET /activity/recent` - Get recent activity

### Progress
- `GET /progress/summary` - Get progress summary
- `GET /progress/breakdown` - Get progress by pillar
- `GET /progress/calendar` - Get calendar activity
- `GET /progress/weekly` - Get weekly stats
- `GET /progress/monthly` - Get monthly stats
- `GET /progress/yearly` - Get yearly stats

## 🔧 Project Structure

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI application
│   ├── config.py            # Configuration
│   ├── database.py          # Database connection
│   ├── models.py            # SQLAlchemy models
│   ├── schemas.py           # Pydantic schemas
│   ├── auth.py              # Authentication logic
│   └── import_challenges.py # Challenge import script
├── init_db.py               # Database initialization
├── requirements.txt         # Python dependencies
├── vercel.json             # Vercel configuration
├── .env                    # Environment variables (local)
├── .env.example            # Environment template
├── .gitignore              # Git ignore rules
├── .vercelignore           # Vercel ignore rules
└── README.md               # This file
```

## 🌐 API Base URL

After deployment, your API will be available at:

**Production:** `https://your-project-name.vercel.app`

Update your Flutter frontend to use this base URL.

## 🔐 Security Notes

- Never commit `.env` file to git
- Use strong random keys for `SECRET_KEY`
- Always use the pooled Neon connection URL for production
- SSL mode is enforced for all Neon connections

## 📝 Notes

- SQLite has been completely removed
- All database operations use Neon Postgres
- Optimized for Vercel's serverless environment
- Connection pooling configured for serverless constraints
