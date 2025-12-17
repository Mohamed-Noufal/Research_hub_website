import { useState, useEffect } from 'react';
import { papersApi } from '../api/papers';

interface SearchResult {
    papers: any[];
    total: number;
    query: string;
    sources_used: string[];
    cached: boolean;
}

/**
 * Hook to search papers using backend API
 * @param query - Search query
 * @param category - Research category
 * @param enabled - Whether to execute the search
 */
export const useSearch = (query: string, category: string, enabled = false) => {
    const [data, setData] = useState<SearchResult | null>(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<Error | null>(null);

    useEffect(() => {
        if (!enabled || !query || !category) {
            return;
        }

        const fetchResults = async () => {
            try {
                setLoading(true);
                setError(null);

                // Safety timeout - force loading to false after 60 seconds (increased from 30s)
                const timeoutId = setTimeout(() => {
                    console.warn('⚠️ Search timeout - forcing loading state to false');
                    setLoading(false);
                    setError(new Error('Search timed out after 60 seconds'));
                }, 60000); // 60 seconds

                console.log('🔍 Searching:', { query, category });
                // Fetch 100 results to enable client-side pagination
                const results = await papersApi.search(query, category, 'auto', 100);
                console.log('✅ Search results:', results);
                setData(results);
                clearTimeout(timeoutId); // Clear timeout on success
            } catch (err) {
                console.error('❌ Search failed:', err);
                setError(err as Error);
            } finally {
                setLoading(false);
            }
        };

        fetchResults();
    }, [query, category, enabled]);

    return { data, loading, error };
};
