// React Query hooks for methodology data

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import * as methodologyApi from '../api/methodology';

// Hook to fetch methodology data
export function useMethodologyData(projectId: string) {
    return useQuery({
        queryKey: ['methodology', projectId],
        queryFn: () => methodologyApi.getMethodologyData(projectId),
        enabled: !!projectId,
    });
}

// Hook to update methodology data
export function useUpdateMethodology() {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: ({
            projectId,
            paperId,
            data,
        }: {
            projectId: string;
            paperId: string;
            data: methodologyApi.MethodologyUpdate;
        }) => methodologyApi.updateMethodologyData(projectId, paperId, data),
        onSuccess: (_, { projectId }) => {
            queryClient.invalidateQueries({ queryKey: ['methodology', projectId] });
        },
    });
}
