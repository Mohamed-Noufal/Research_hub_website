import { QueryClient } from '@tanstack/react-query';

// Create a client with optimized settings for academic research app
export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      // Cache data for 5 minutes - perfect for academic content
      staleTime: 1000 * 60 * 5, // 5 minutes

      // Don't refetch when user focuses window (annoying for research)
      refetchOnWindowFocus: false,

      // Don't retry on 4xx errors (client errors), retry 2x on 5xx/server errors
      retry: (failureCount, error: any) => {
        if (error?.response?.status >= 400 && error?.response?.status < 500) {
          return false; // Don't retry client errors
        }
        return failureCount < 2; // Retry up to 2 times for server errors
      },

      // Network mode for offline support
      networkMode: 'online',
    },
    mutations: {
      // Retry mutations once on failure
      retry: 1,
    },
  },
});
