import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000/api/v1';

// Create axios instance with default config
const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 90000, // 90 seconds (increased from 30s for comprehensive searches)
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor for auth
api.interceptors.request.use(
  (config) => {
    // Add auth headers here when implementing authentication
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor for error handling
api.interceptors.response.use(
  (response) => {
    return response;
  },
  (error) => {
    console.error('API Error:', error);
    return Promise.reject(error);
  }
);



// Helper function to map backend source names to frontend expected values
function mapBackendSourceToFrontend(backendSource: string): string {
  const sourceMap: { [key: string]: string } = {
    'semantic_scholar': 'semantic',
    'openalex': 'openalex',
    'arxiv': 'arxiv',
    'pubmed': 'pubmed',
    'crossref': 'crossref',
    'europe_pmc': 'europe_pmc',
    'core': 'core',
    'eric': 'eric',
    'biorxiv': 'biorxiv'
  };

  return sourceMap[backendSource] || backendSource;
}

// TypeScript interfaces
export interface Paper {
  id: string;
  title: string;
  abstract: string;
  authors: string[];
  publication_date: string;
  source: string;
  doi?: string;
  citation_count: number;
  venue?: string;
  pdf_url?: string;
  category: string;
  saved?: boolean;
  openAccess?: boolean;
}

export interface SearchRequest {
  query: string;
  category: string;
  mode?: 'auto' | 'quick' | 'ai';
  limit?: number;
}

export interface SearchResponse {
  papers: Paper[];
  total: number;
  metadata: any;
}

export interface Category {
  id: string;
  name: string;
  description: string;
  sources: string[];
  source_count: number;
}

export interface UserStats {
  saved_papers: number;
  notes: number;
  literature_reviews: number;
  total_searches: number;
}

export interface Note {
  id: number;
  paper_id?: number;
  title?: string;
  content: string;
  content_type: string;
  created_at: string;
  updated_at: string;
}

export interface NoteItem {
  id: number;
  paper_id?: number;
  title: string;
  content?: string;
  content_type?: string;
  parent_id?: number;
  path?: string;
  is_folder: boolean;
  level: number;
  created_at: string;
  updated_at: string;
  children?: NoteItem[];
}

export interface LiteratureReview {
  id: number;
  title: string;
  description?: string;
  paper_ids: number[];
  created_at: string;
  updated_at: string;
}

// API Service Class
class ApiService {
  // User Management
  async initUser(): Promise<{ user_id: string; status: string }> {
    const response = await api.post('/users/init');
    return response.data;
  }

  async getUserStats(): Promise<UserStats> {
    const response = await api.get('/users/stats');
    return response.data;
  }

  // Search
  async searchPapers(params: SearchRequest): Promise<SearchResponse> {
    const response = await api.get('/papers/search', { params });
    const data = response.data;

    // Transform backend response to match frontend interfaces
    return {
      papers: data.papers.map((paper: any) => ({
        ...paper,
        id: paper.id?.toString() || '',  // Convert integer ID to string
        saved: false,  // Default value, will be overridden by saved papers check
        authors: paper.authors || [],  // Ensure authors array
        category: paper.category || '',  // Ensure category string
        citation_count: paper.citation_count || 0,  // Ensure integer
        // Map source names to frontend expected values
        source: mapBackendSourceToFrontend(paper.source),
        // Ensure all other fields have default values
        abstract: paper.abstract || '',
        title: paper.title || '',
        publication_date: paper.publication_date || '',
        doi: paper.doi || undefined,
        venue: paper.venue || '',
        pdf_url: paper.pdf_url || undefined
      })),
      total: data.total || 0,
      metadata: data.metadata || {}
    };
  }

  async getCategories(): Promise<{ categories: Record<string, Category>; total: number }> {
    const response = await api.get('/papers/categories');
    return response.data;
  }

  // Saved Papers
  async savePaper(paperId: number, data?: { tags?: string[]; personal_notes?: string }): Promise<any> {
    const response = await api.post('/users/saved-papers', { paper_id: paperId, ...data });
    return response.data;
  }

  async getSavedPapers(): Promise<{ papers: Paper[]; total: number }> {
    const response = await api.get('/users/saved-papers');
    return response.data;
  }

  async unsavePaper(paperId: number): Promise<void> {
    await api.delete(`/users/saved-papers/${paperId}`);
  }

  async checkPaperSaved(paperId: number): Promise<{ is_saved: boolean }> {
    const response = await api.get(`/users/saved-papers/${paperId}/check`);
    return response.data;
  }

  // Notes
  async createNote(data: {
    paper_id?: number;
    title?: string;
    content: string;
    content_type?: string;
  }): Promise<any> {
    const response = await api.post('/users/notes', data);
    return response.data;
  }

  async getNotes(paperId?: number): Promise<{ notes: Note[]; total: number }> {
    const params = paperId ? { paper_id: paperId } : {};
    const response = await api.get('/users/notes', { params });
    return response.data;
  }

  async updateNote(noteId: number, data: { title?: string; content?: string }): Promise<void> {
    await api.put(`/users/notes/${noteId}`, data);
  }

  async deleteNote(noteId: number): Promise<void> {
    await api.delete(`/users/notes/${noteId}`);
  }

  // Notes Hierarchy (new folder/file system)
  async getNotesHierarchy(): Promise<{ hierarchy: NoteItem[] }> {
    const response = await api.get('/users/notes/hierarchy');
    return response.data;
  }

  async createFolder(data: { title: string; parent_id?: number }): Promise<NoteItem> {
    const response = await api.post('/users/notes/folder', data);
    return response.data;
  }

  async createNoteFile(data: {
    title: string;
    content?: string;
    content_type?: string;
    parent_id?: number;
    paper_id?: number;
  }): Promise<NoteItem> {
    const response = await api.post('/users/notes/file', data);
    return response.data;
  }

  async renameNoteItem(itemId: number, newTitle: string): Promise<void> {
    await api.patch(`/users/notes/${itemId}/rename`, { new_title: newTitle });
  }

  async moveNoteItem(itemId: number, newParentId?: number): Promise<void> {
    await api.patch(`/users/notes/${itemId}/move`, { new_parent_id: newParentId });
  }

  async deleteNoteItemRecursive(itemId: number): Promise<void> {
    await api.delete(`/users/notes/${itemId}/recursive`);
  }

  // Literature Reviews
  async createLiteratureReview(data: {
    title: string;
    description?: string;
    paper_ids?: number[];
  }): Promise<any> {
    const response = await api.post('/users/literature-reviews', data);
    return response.data;
  }

  async getLiteratureReviews(): Promise<{ reviews: LiteratureReview[]; total: number }> {
    const response = await api.get('/users/literature-reviews');
    return response.data;
  }

  async updateLiteratureReview(reviewId: number, data: {
    title?: string;
    description?: string;
    paper_ids?: number[];
  }): Promise<void> {
    await api.put(`/users/literature-reviews/${reviewId}`, data);
  }

  async deleteLiteratureReview(reviewId: number): Promise<void> {
    await api.delete(`/users/literature-reviews/${reviewId}`);
  }

  // Search History
  async getSearchHistory(limit: number = 50): Promise<{ history: any[]; total: number }> {
    const response = await api.get('/users/search-history', { params: { limit } });
    return response.data;
  }

  // AI Features
  async aiChat(message: string, context?: any[]): Promise<{ response: string }> {
    const response = await api.post('/ai/chat', { message, context });
    return response.data;
  }

  async aiAnalyzeQuery(query: string): Promise<{ search_queries: string[] }> {
    const response = await api.post('/ai/analyze', { query });
    return response.data;
  }

  // File Upload
  async uploadFile(file: File): Promise<any> {
    const formData = new FormData();
    formData.append('file', file);

    const response = await api.post('/files/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  }

  // Health Check
  async healthCheck(): Promise<any> {
    const response = await api.get('/papers/health');
    return response.data;
  }

  // DOI-Based Paper Fetching
  async fetchPaperByDOI(doi: string, category?: string): Promise<{
    paper: Paper;
    status: 'created' | 'already_exists';
    message: string;
    already_in_library: boolean;
    source?: string;
  }> {
    const response = await api.post('/papers/fetch-by-doi', {
      doi: doi.trim(),
      category: category || null
    });

    // Transform response to match Paper interface
    const data = response.data;
    return {
      ...data,
      paper: {
        ...data.paper,
        id: data.paper.id?.toString() || '',
        authors: data.paper.authors || [],
        category: data.paper.category || category || '',
        citation_count: data.paper.citation_count || 0,
        saved: data.already_in_library || false
      }
    };
  }

  async uploadPaperPdf(paperId: string, file: File): Promise<{ message: string; pdf_url: string }> {
    const formData = new FormData();
    formData.append('file', file);

    const response = await api.post(`/papers/${paperId}/upload-pdf`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  }

  async downloadPaperPdf(paperId: string): Promise<{ message: string; pdf_url: string; file_size?: number; already_local?: boolean }> {
    const response = await api.post(`/papers/${paperId}/download-pdf`);
    return response.data;
  }

  // Paper Folder Management APIs
  async getPaperFolders(): Promise<any[]> {
    const response = await api.get('/folders');
    return response.data;
  }

  async createPaperFolder(name: string, description?: string): Promise<any> {
    const response = await api.post('/folders', { name, description });
    return response.data;
  }

  async updatePaperFolder(folderId: string, name?: string, description?: string): Promise<any> {
    const response = await api.put(`/folders/${folderId}`, { name, description });
    return response.data;
  }

  async deletePaperFolder(folderId: string): Promise<void> {
    await api.delete(`/folders/${folderId}`);
  }

  async addPaperToFolder(folderId: string, paperId: string): Promise<void> {
    await api.post(`/folders/${folderId}/papers/${paperId}`);
  }

  async removePaperFromFolder(folderId: string, paperId: string): Promise<void> {
    await api.delete(`/folders/${folderId}/papers/${paperId}`);
  }

  async getFolderPapers(folderId: string): Promise<{ paper_ids: string[] }> {
    const response = await api.get(`/folders/${folderId}/papers`);
    return response.data;
  }

  async createManualPaper(paperData: FormData): Promise<any> {
    const response = await api.post('/papers/manual', paperData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  }
}

// Export singleton instance
export const apiService = new ApiService();
export default apiService;
