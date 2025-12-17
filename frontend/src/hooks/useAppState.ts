import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import type { Paper, Note, LiteratureReview, UserStats } from '../services/api';
import { apiService } from '../services/api';

interface AppState {
  // User
  userId: string | null;
  userStats: UserStats | null;
  isInitialized: boolean;
  isInitializing: boolean;

  // Papers
  savedPapers: Paper[];
  currentSearch: {
    query: string;
    category: string;
    results: Paper[];
    total: number;
    metadata: any;
  } | null;

  // UI State
  currentView: 'search' | 'results' | 'workspace' | 'blog';
  sidebarOpen: boolean;
  loading: boolean;
  error: string | null;

  // Search State
  searchQuery: string | null;
  searchCategory: string | null;

  // Workspace
  selectedPaper: Paper | null;
  notes: Note[];
  literatureReviews: LiteratureReview[];

  // Actions
  setUserId: (id: string) => void;
  setUserStats: (stats: UserStats) => void;
  initUser: () => Promise<void>;

  // Paper actions
  savePaper: (paper: Paper, tags?: string[], notes?: string) => Promise<void>;
  unsavePaper: (paperId: string) => Promise<void>;
  loadSavedPapers: () => Promise<void>;
  setCurrentSearch: (search: any) => void;
  clearSearch: () => void;

  // UI actions
  setCurrentView: (view: 'search' | 'results' | 'workspace' | 'blog') => void;
  setSidebarOpen: (open: boolean) => void;
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;

  // Workspace actions
  setSelectedPaper: (paper: Paper | null) => void;
  loadNotes: (paperId?: number) => Promise<void>;
  createNote: (data: { paper_id?: number; title?: string; content: string }) => Promise<void>;
  updateNote: (noteId: number, data: { title?: string; content?: string }) => Promise<void>;
  deleteNote: (noteId: number) => Promise<void>;

  loadLiteratureReviews: () => Promise<void>;
  createLiteratureReview: (data: { title: string; description?: string; paper_ids?: number[] }) => Promise<void>;
  updateLiteratureReview: (reviewId: number, data: any) => Promise<void>;
  deleteLiteratureReview: (reviewId: number) => Promise<void>;
}

export const useAppState = create<AppState>()(
  persist(
    (set, get) => ({
      // Initial state
      userId: null,
      userStats: null,
      isInitialized: false,
      isInitializing: false,
      savedPapers: [],
      currentSearch: null,
      currentView: 'search',
      sidebarOpen: true,
      loading: false,
      error: null,
      searchQuery: null,
      searchCategory: null,
      selectedPaper: null,
      notes: [],
      literatureReviews: [],

      // User actions
      setUserId: (id) => set({ userId: id }),
      setUserStats: (stats) => set({ userStats: stats }),

      initUser: async () => {
        // 🚀 INITIALIZATION GUARD - Prevents API call storm!
        if (get().isInitialized || get().isInitializing) {
          console.log('Initialization already done or in progress, skipping...');
          return; // Exit early - no API calls!
        }

        console.log('Starting user initialization...');
        set({ isInitializing: true });

        try {
          set({ loading: true, error: null });

          const response = await apiService.initUser();
          set({ userId: response.user_id });

          // Load user stats
          const stats = await apiService.getUserStats();
          set({ userStats: stats });

          // Load saved papers
          await get().loadSavedPapers();

          // Load literature reviews
          await get().loadLiteratureReviews();

          // ✅ Mark as initialized - prevents future calls
          set({ isInitialized: true });
          console.log('User initialization completed successfully!');

        } catch (error) {
          console.error('Failed to initialize user:', error);
          set({ error: 'Failed to initialize user' });
        } finally {
          set({ loading: false, isInitializing: false });
        }
      },

      // Paper actions
      savePaper: async (paper, tags, personalNotes) => {
        try {
          set({ loading: true, error: null });
          await apiService.savePaper(parseInt(paper.id), { tags, personal_notes: personalNotes });

          // Update local state
          const savedPapers = [...get().savedPapers, { ...paper, saved: true }];
          set({ savedPapers });

          // Update stats
          const stats = await apiService.getUserStats();
          set({ userStats: stats });

        } catch (error) {
          console.error('Failed to save paper:', error);
          set({ error: 'Failed to save paper' });
          throw error;
        } finally {
          set({ loading: false });
        }
      },

      unsavePaper: async (paperId) => {
        try {
          set({ loading: true, error: null });
          await apiService.unsavePaper(parseInt(paperId));

          // Update local state
          const savedPapers = get().savedPapers.filter(p => p.id !== paperId);
          set({ savedPapers });

          // Update stats
          const stats = await apiService.getUserStats();
          set({ userStats: stats });

        } catch (error) {
          console.error('Failed to unsave paper:', error);
          set({ error: 'Failed to unsave paper' });
          throw error;
        } finally {
          set({ loading: false });
        }
      },

      loadSavedPapers: async () => {
        try {
          const response = await apiService.getSavedPapers();
          set({ savedPapers: response.papers });
        } catch (error) {
          console.error('Failed to load saved papers:', error);
          set({ error: 'Failed to load saved papers' });
        }
      },

      setCurrentSearch: (search) => set({ currentSearch: search }),
      clearSearch: () => set({ currentSearch: null }),

      // UI actions
      setCurrentView: (view) => set({ currentView: view }),
      setSidebarOpen: (open) => set({ sidebarOpen: open }),
      setLoading: (loading) => set({ loading }),
      setError: (error) => set({ error }),

      // Workspace actions
      setSelectedPaper: (paper) => set({ selectedPaper: paper }),

      loadNotes: async (paperId) => {
        try {
          const response = await apiService.getNotes(paperId);
          set({ notes: response.notes });
        } catch (error) {
          console.error('Failed to load notes:', error);
          set({ error: 'Failed to load notes' });
        }
      },

      createNote: async (data) => {
        try {
          set({ loading: true, error: null });
          await apiService.createNote(data);

          // Reload notes
          await get().loadNotes(data.paper_id);

          // Update stats
          const stats = await apiService.getUserStats();
          set({ userStats: stats });

        } catch (error) {
          console.error('Failed to create note:', error);
          set({ error: 'Failed to create note' });
          throw error;
        } finally {
          set({ loading: false });
        }
      },

      updateNote: async (noteId, data) => {
        try {
          set({ loading: true, error: null });
          await apiService.updateNote(noteId, data);

          // Reload notes
          const currentPaper = get().selectedPaper;
          await get().loadNotes(currentPaper ? parseInt(currentPaper.id) : undefined);

        } catch (error) {
          console.error('Failed to update note:', error);
          set({ error: 'Failed to update note' });
          throw error;
        } finally {
          set({ loading: false });
        }
      },

      deleteNote: async (noteId) => {
        try {
          set({ loading: true, error: null });
          await apiService.deleteNote(noteId);

          // Reload notes
          const currentPaper = get().selectedPaper;
          await get().loadNotes(currentPaper ? parseInt(currentPaper.id) : undefined);

          // Update stats
          const stats = await apiService.getUserStats();
          set({ userStats: stats });

        } catch (error) {
          console.error('Failed to delete note:', error);
          set({ error: 'Failed to delete note' });
          throw error;
        } finally {
          set({ loading: false });
        }
      },

      loadLiteratureReviews: async () => {
        try {
          const response = await apiService.getLiteratureReviews();
          set({ literatureReviews: response.reviews });
        } catch (error) {
          console.error('Failed to load literature reviews:', error);
          set({ error: 'Failed to load literature reviews' });
        }
      },

      createLiteratureReview: async (data) => {
        try {
          set({ loading: true, error: null });
          await apiService.createLiteratureReview(data);

          // Reload reviews
          await get().loadLiteratureReviews();

          // Update stats
          const stats = await apiService.getUserStats();
          set({ userStats: stats });

        } catch (error) {
          console.error('Failed to create literature review:', error);
          set({ error: 'Failed to create literature review' });
          throw error;
        } finally {
          set({ loading: false });
        }
      },

      updateLiteratureReview: async (reviewId, data) => {
        try {
          set({ loading: true, error: null });
          await apiService.updateLiteratureReview(reviewId, data);

          // Reload reviews
          await get().loadLiteratureReviews();

        } catch (error) {
          console.error('Failed to update literature review:', error);
          set({ error: 'Failed to update literature review' });
          throw error;
        } finally {
          set({ loading: false });
        }
      },

      deleteLiteratureReview: async (reviewId) => {
        try {
          set({ loading: true, error: null });
          await apiService.deleteLiteratureReview(reviewId);

          // Reload reviews
          await get().loadLiteratureReviews();

          // Update stats
          const stats = await apiService.getUserStats();
          set({ userStats: stats });

        } catch (error) {
          console.error('Failed to delete literature review:', error);
          set({ error: 'Failed to delete literature review' });
          throw error;
        } finally {
          set({ loading: false });
        }
      },
    }),
    {
      name: 'researchhub-storage',
      partialize: (state) => ({
        userId: state.userId,
        savedPapers: state.savedPapers,
        sidebarOpen: state.sidebarOpen,
        userStats: state.userStats,
      }),
    }
  )
);
