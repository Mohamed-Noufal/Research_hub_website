# Future Authentication System Implementation Plan

This document outlines the roadmap for upgrading from the current "Local/Anonymous" user system to a fully secured **Email/Password Authentication System** using JWT (JSON Web Tokens).

---

## 🏗️ Architecture Overview

| Component | Technology | Responsibility |
|-----------|------------|----------------|
| **Database** | PostgreSQL | Store user credentials (hashed) and profile data |
| **Backend** | FastAPI / Python-Jose | Handle Logic, Login, Register, Issue JWTs |
| **Security** | OAuth2 / Bcrypt | Password hashing and Token validation |
| **Frontend** | React Context + Axios | Manage Login State, store tokens, protect routes |

---

## 1. 🗄️ Database Schema Updates

We need to modify the existing `users` table or create a new one to support credentials.

### SQL Migration (`migrations/030_auth_system.sql`)

```sql
-- Enable crypto extension for UUIDs if not already
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

CREATE TABLE IF NOT EXISTS auth_users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    full_name VARCHAR(100),
    is_active BOOLEAN DEFAULT TRUE,
    is_verified BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP WITH TIME ZONE
);

-- Optional: Link existing local workspace data to auth users
-- This allows "claiming" a guest session after signing up
ALTER TABLE local_users ADD COLUMN auth_user_id UUID REFERENCES auth_users(id);
```

---

## 2. 🔙 Backend Implementation

### Dependencies
Add to `requirements.txt`:
```txt
passlib[bcrypt]  # For password hashing
python-jose      # For JWT token creation/decoding
python-multipart # For OAuth2 form data
```

### 2.1 Security Utility (`app/core/security.py`)
- `verify_password(plain, hashed)`
- `get_password_hash(password)`
- `create_access_token(data, expires_delta)`

### 2.2 Auth Router (`app/api/v1/auth.py`)

#### POST `/auth/register`
- Inputs: Email, Password, Full Name
- Action: Checks dupes, hashes password, saves to DB.

#### POST `/auth/login` (or `/auth/token`)
- Inputs: Email, Password
- Action: Verifies credentials.
- Returns: `access_token` (JWT), `token_type`: "bearer"

#### GET `/auth/me`
- Action: Decodes current token.
- Returns: Current user profile.

### 2.3 Dependency Injection (`app/core/deps.py`)
Create a `get_current_user` dependency that:
1.  Reads `Authorization: Bearer <token>` header.
2.  Decodes JWT.
3.  Fetches user from DB.
4.  Raises 401 if invalid.

---

## 3. 🖥️ Frontend Implementation

### 3.1 Auth Context (`src/contexts/AuthContext.tsx`)
Create a global provider to manage state:
- `user`: User profile object or null
- `isLoading`: Loading state
- `login(email, password)`: Calls API, saves token to localStorage
- `register(email, password)`: Calls API
- `logout()`: Clears token and state

### 3.2 Private Route Wrapper (`src/components/auth/PrivateRoute.tsx`)
```tsx
const PrivateRoute = ({ children }) => {
  const { user, isLoading } = useAuth();
  if (isLoading) return <Loader />;
  if (!user) return <Navigate to="/login" />;
  return children;
};
```

### 3.3 Axios Interceptor (`src/services/api.ts`)
Update the existing request interceptor to attach the token:

```typescript
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});
```

---

## 4. 🔄 Migration Strategy (Guest -> User)

How to keep data when a guest signs up?

1.  **Current State**: User has `paper-search-user-id` (Local UUID) in localStorage.
2.  **On Register**: Send the *existing* Local ID along with the new Email/Password.
3.  **Backend Logic**: 
    - Create new `auth_user`.
    - Find all data (papers, chats) linked to the Local ID.
    - Update them to link to the new `auth_user` ID.
    - Or, simply link the `local_users` record to the `auth_user`.

---

## 5. ✅ Implementation Checklist

- [ ] Install backend dependencies (`passlib`, `python-jose`, `python-multipart`).
- [ ] Create `auth_users` table migration.
- [ ] Implement `security.py` utilities.
- [ ] Create `/auth` API endpoints.
- [ ] Build Login and Register UI pages.
- [ ] Implement `AuthProvider` in Frontend.
- [ ] Protect sensitive routes (e.g., `/dashboard`, `/library`).
- [ ] (Optional) Add "Continue as Guest" vs "Sign In" on landing page.
