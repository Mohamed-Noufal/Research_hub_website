import { useState, useEffect } from 'react';
import { usersApi } from '../api/users';

/**
 * Hook to manage user session
 * Auto-initializes user on first visit and stores user ID in localStorage
 */
export const useUser = () => {
    const [userId, setUserId] = useState<string | null>(
        localStorage.getItem('userId')
    );
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<Error | null>(null);

    useEffect(() => {
        const initUser = async () => {
            if (!userId) {
                setLoading(true);
                try {
                    const response = await usersApi.initUser();
                    const newUserId = response.user_id;
                    localStorage.setItem('userId', newUserId);
                    setUserId(newUserId);
                    console.log('✅ User initialized:', newUserId);
                } catch (err) {
                    console.error('Failed to initialize user:', err);
                    setError(err as Error);
                } finally {
                    setLoading(false);
                }
            }
        };

        initUser();
    }, [userId]);

    return { userId, loading, error };
};
