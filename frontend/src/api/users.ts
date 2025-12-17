import apiClient from './client';

export const usersApi = {
    /**
     * Initialize a new user (no auth required)
     * Returns a user_id to store in localStorage
     */
    initUser: async () => {
        const response = await apiClient.post('/api/v1/users/init');
        return response.data;
    },

    /**
     * Save a paper to user's library
     */
    savePaper: async (paperId: number, tags?: string[], notes?: string) => {
        const response = await apiClient.post('/api/v1/users/saved-papers', {
            paper_id: paperId,
            tags,
            personal_notes: notes
        });
        return response.data;
    },

    /**
     * Remove a paper from user's library
     */
    unsavePaper: async (paperId: number) => {
        const response = await apiClient.delete(`/api/v1/users/saved-papers/${paperId}`);
        return response.data;
    },

    /**
     * Get all saved papers
     */
    getSavedPapers: async () => {
        const response = await apiClient.get('/api/v1/users/saved-papers');
        return response.data;
    },

    /**
     * Check if a paper is saved
     */
    isPaperSaved: async (paperId: number) => {
        const response = await apiClient.get(`/api/v1/users/saved-papers/${paperId}/check`);
        return response.data;
    },

    // Notes API
    createNote: async (data: { paper_id?: number; title?: string; content: string }) => {
        const response = await apiClient.post('/api/v1/users/notes', data);
        return response.data;
    },

    getNotes: async (paperId?: number) => {
        const response = await apiClient.get('/api/v1/users/notes', {
            params: { paper_id: paperId }
        });
        return response.data;
    },

    getNotesHierarchy: async () => {
        const response = await apiClient.get('/api/v1/users/notes/hierarchy');
        return response.data;
    },

    // Literature Reviews API
    createReview: async (data: { title: string; description?: string; paper_ids?: number[] }) => {
        const response = await apiClient.post('/api/v1/users/literature-reviews', data);
        return response.data;
    },

    getReviews: async () => {
        const response = await apiClient.get('/api/v1/users/literature-reviews');
        return response.data;
    },

    updateReview: async (reviewId: string | number, data: { title?: string; description?: string; paper_ids?: number[] }) => {
        const response = await apiClient.put(`/api/v1/users/literature-reviews/${reviewId}`, data);
        return response.data;
    },

    deleteReview: async (reviewId: string | number) => {
        const response = await apiClient.delete(`/api/v1/users/literature-reviews/${reviewId}`);
        return response.data;
    },

    seedProject: async (reviewId: string | number) => {
        const response = await apiClient.post(`/api/v1/users/literature-reviews/${reviewId}/seed`);
        return response.data;
    },

    getProjectPapers: async (projectId: string | number) => {
        const response = await apiClient.get(`/api/v1/projects/${projectId}/papers`);
        return response.data;
    }
};
