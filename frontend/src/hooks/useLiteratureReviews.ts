import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { usersApi } from '../api/users';
import type { Project } from '../components/workspace/literature-review/types';
// import type { AxiosError } from 'axios';

// Map API response to Project interface
const mapReviewToProject = (review: any): Project => ({
    id: review.id,
    name: review.title,
    description: review.description || '',
    paperIds: review.paper_ids || [],
    createdAt: review.created_at,
    updatedAt: review.updated_at
});

export function useLiteratureReviews() {
    return useQuery({
        queryKey: ['literature-reviews'],
        queryFn: async () => {
            const data = await usersApi.getReviews();
            return {
                reviews: data.reviews.map(mapReviewToProject),
                total: data.total
            };
        }
    });
}

export function useCreateLiteratureReview() {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: async (data: { title: string; description?: string; paperIds?: number[] }) => {
            return await usersApi.createReview({
                title: data.title,
                description: data.description,
                paper_ids: data.paperIds
            });
        },
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['literature-reviews'] });
        }
    });
}

export function useUpdateLiteratureReview() {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: async ({ id, data }: { id: number; data: { title?: string; description?: string; paperIds?: number[] } }) => {
            return await usersApi.updateReview(id, {
                title: data.title,
                description: data.description,
                paper_ids: data.paperIds
            });
        },
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['literature-reviews'] });
        }
    });
}

export function useDeleteLiteratureReview() {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: async (id: number) => {
            return await usersApi.deleteReview(id);
        },
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['literature-reviews'] });
        }
    });
}

// Hook to fetch User's Saved Papers for selection
export function useSavedPapers() {
    return useQuery({
        queryKey: ['saved-papers'],
        queryFn: async () => {
            const data = await usersApi.getSavedPapers();
            return data.papers || [];
        }
    });
}

// Hook to fetch papers for a specific project
export function useProjectPapers(projectId: string | number) {
    return useQuery({
        queryKey: ['project-papers', String(projectId)],
        queryFn: async () => {
            const data = await usersApi.getProjectPapers(projectId);
            return data.papers || [];
        },
        enabled: !!projectId
    });
}
