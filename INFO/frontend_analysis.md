# Frontend Analysis & Architecture

## Overview
The frontend is a **React** application built with **Vite** and **TypeScript**. It is designed to be a modern, responsive interface for searching and managing research papers.

**Key Technologies:**
- **Framework**: React 18
- **Language**: TypeScript
- **Styling**: TailwindCSS
- **State Management**: React Hooks (`useState`, `useEffect`, custom hooks).
- **Routing**: Client-side routing (likely `react-router-dom`).

## � Key Files
- **Entry Point**: `frontend/src/main.tsx`
- **App Root**: `frontend/src/App.tsx`
- **API Layer**: `frontend/src/api/`
- **State/Hooks**: `frontend/src/hooks/`
- **Components**: `frontend/src/components/`

## �🔗 Connections to Backend

The frontend communicates with the backend exclusively via HTTP requests.

### 1. API Client (`src/api/client.ts`)
A centralized **Axios** instance is configured here.
- **Base URL**: Loaded from `VITE_API_URL` (defaults to `http://localhost:8000`).
- **Interceptors**:
    - **Request**: Automatically attaches the `X-User-ID` header from `localStorage`. This ensures every request is authenticated to the correct user session.
    - **Response**: Global error handling.

### 2. Custom Hooks (State & Logic)
Hooks encapsulate API logic to keep components clean.

- **`useUser`**: 
    - Manages the user session.
    - On load: Checks `localStorage` for `userId`. If missing, calls `POST /users/init` to get a new ID.
- **`useSearch`**:
    - Parameters: `query`, `category`.
    - Action: Calls `papersApi.search`.
    - State: Returns `{ data, loading, error }`.
    - **Optimizations**: Includes debounce logic and loading states.

### 3. API Modules (`src/api/`)
Specific API calls are grouped by domain:
- **`papers.ts`**: `search()`, `getStats()`.
- **`users.ts`**: `savePaper()`, `getSavedPapers()`, `createNote()`.

## 🖥️ Component Architecture

### 1. `SearchPage.tsx` (Main View)
- **Role**: The landing and results page.
- **State**:
    - `activeCategory`: Defaults to 'AI & CS'.
    - `query`: User input.
    - `aiSuggestions`: Stores AI-generated queries from `/ai-suggestions`.
- **Connections**:
    - `handleSearch`: Triggers the parent `onSearch` callback.
    - `handleGetAISuggestions`: Calls `POST /api/v1/papers/ai-suggestions` to get smart query refinements.
    - **UI**: Displays `stats` grid with animated gradients.

### 2. `SearchResults.tsx`
- **Role**: Renders the list of papers.
- **Connections**:
    - Receives `results` prop.
    - Renders list of `PaperCard` components.
    - Handles "Load More" (if pagination is implemented).

### 3. `PaperCard.tsx`
- **Role**: Displays individual paper details (Title, Abstract, Citations).
- **Connections**:
    - **Save Button**: Calls `usersApi.savePaper(id)`.
    - **View PDF**: Links to `pdf_url` (e.g., arXiv PDF).
    - **Source Badge**: Displays source (arXiv, Semantic Scholar) with specific color coding.

### 4. `LibraryPanel.tsx` (or similar)
- **Role**: Shows saved papers.
- **Connections**:
    - Calls `usersApi.getSavedPapers()` on mount.
    - Displays user's personal collection.

## 🔄 Data Flow Example (User Action)

**Scenario: User saves a paper.**
1. **User Click**: User clicks the "Save" bookmark icon on a `PaperCard`.
2. **Component Logic**: The `handleSave` function is triggered.
3. **API Call**: Invokes `usersApi.savePaper(paperId)`.
4. **Network Request**: `POST /api/v1/users/saved-papers` sent with `X-User-ID` header.
5. **UI Update**: 
    - Optimistic update: Icon turns filled immediately.
    - On success: Toast notification "Paper saved".
    - On error: Reverts icon and shows error message.
