import apiClient from './client';

export const papersApi = {
    /**
     * Search papers across academic databases
     * @param query - Search query
     * @param category - Research category (ai_cs, medicine_biology, etc.)
     * @param mode - Search mode (auto, quick, ai)
     * @param limit - Maximum results
     */
    search: async (query: string, category: string, mode = 'auto', limit = 20) => {
        const response = await apiClient.get('/api/v1/papers/search', {
            params: { query, category, mode, limit }
        });
        return response.data;
    },

    /**
     * Get database statistics
     */
    getStats: async () => {
        const response = await apiClient.get('/api/v1/papers/stats');
        return response.data;
    },

    /**
     * Health check for academic sources
     */
    healthCheck: async () => {
        const response = await apiClient.get('/api/v1/papers/health');
        return response.data;
    },

    /**
     * Save search to history
     */
    saveSearchHistory: async (query: string, category: string, resultsCount: number) => {
        const response = await apiClient.post('/api/v1/search-history/save', {
            query,
            category,
            results_count: resultsCount
        });
        return response.data;
    },

    /**
     * Get search history
     */
    getSearchHistory: async (limit = 50) => {
        const response = await apiClient.get('/api/v1/search-history/list', {
            params: { limit }
        });
        return response.data;
    },

    /**
     * Clear all search history
     */
    clearSearchHistory: async () => {
        const response = await apiClient.delete('/api/v1/search-history/clear');
        return response.data;
    },

    /**
     * Delete specific search entry
     */
    deleteSearchEntry: async (searchId: number) => {
        const response = await apiClient.delete(`/api/v1/search-history/${searchId}`);
        return response.data;
    }
};
