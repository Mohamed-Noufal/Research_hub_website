# 📂 Project Structure & File Guide

This document provides a comprehensive map of the project's file structure, explaining the purpose of key directories and files to help new developers navigate the codebase.

## 🏗️ Root Directory (`/`)
- **`backend/`**: Python/FastAPI backend source code.
- **`frontend/`**: React/TypeScript frontend source code.
- **`INFO/`**: Documentation and analysis files (this directory).
- **`*.md`**: Various architectural documentation files (e.g., `API_REFERENCE.md`, `DATABASE_ARCHITECTURE_ANALYSIS.md`).

## 🐍 Backend Structure (`/backend/app`)
The backend follows a standard FastAPI application structure.

### **Core (`/backend/app/core`)**
- **`config.py`**: Configuration settings (loaded from `.env`).
- **`database.py`**: Database connection logic (`get_db`, engine creation).
- **`search_config.py`**: Configuration for search sources and categories.

### **API Routers (`/backend/app/api/v1`)**
- **`papers.py`**: Main endpoints for search (`/search`), stats, and categories.
- **`users.py`**: User-related endpoints (library, notes, reviews).
- **`search_history.py`**: Endpoints for managing user search history.

### **Models (`/backend/app/models`)**
- **`paper.py`**: SQLAlchemy model for the `papers` table (includes `embedding` column).
- **`user_models.py`**: SQLAlchemy models for users, notes, saved papers, reviews, etc.
- **`schemas.py`**: Pydantic models for request/response validation.

### **Services (`/backend/app/services`)**
Business logic layer.
- **`unified_search_service.py`**: Orchestrates the search flow (Cache -> Local DB -> External APIs).
- **`enhanced_vector_service.py`**: Handles embedding generation and vector search logic.
- **`ai_query_analyzer.py`**: Logic for AI-powered search suggestions.
- **`user_service.py`**: Logic for user operations (saving papers, creating notes).
- **`*source*_service.py`** (e.g., `arxiv_service.py`, `semantic_scholar_service.py`): Connectors for specific external APIs.

## ⚛️ Frontend Structure (`/frontend/src`)
The frontend is a React + Vite application.

### **API Layer (`/frontend/src/api`)**
- **`client.ts`**: Axios instance configuration (base URL, interceptors).
- **`papers.ts`**: API functions for paper operations (`search`, `getStats`).
- **`users.ts`**: API functions for user operations (`savePaper`, `getSavedPapers`).

### **Components (`/frontend/src/components`)**
- **`SearchPage.tsx`**: Main landing and search interface.
- **`SearchResults.tsx`**: List of paper results.
- **`PaperCard.tsx`**: Individual paper display component.
- **`workspace/`**: Components for the user's private workspace (Library, Notes).

### **Hooks (`/frontend/src/hooks`)**
- **`useSearch.ts`**: State management for search operations.
- **`useUser.ts`**: User session management logic.

## 🔄 Key Feature - File Connections

### **1. Search Flow**
- **Frontend**: `SearchPage.tsx` -> `useSearch.ts` -> `api/papers.ts`
- **API**: `POST /api/v1/papers/search` (in `backend/app/api/v1/papers.py`)
- **Service**: `unified_search_service.py`
    - Checks `Redis Cache`
    - Calls `enhanced_vector_service.py` (Local DB Search)
    - Calls `arxiv_service.py`, etc. (External Search)
- **Database**: `models/paper.py` (Reads/Writes papers)

### **2. Saving a Paper**
- **Frontend**: `PaperCard.tsx` (Save Button) -> `api/users.ts`
- **API**: `POST /api/v1/users/saved-papers` (in `backend/app/api/v1/users.py`)
- **Service**: `user_service.py` -> `save_paper` method.
- **Database**: `models/user_models.py` (Writes to `user_saved_papers` table)

## 🛠️ Setup & Configuration Files
- **`backend/.env`**: Environment variables (Database URL, API Keys).
- **`frontend/.env`**: Frontend environment variables (API Base URL).
- **`backend/requirements.txt`**: Python dependencies.
- **`frontend/package.json`**: Node.js dependencies.
