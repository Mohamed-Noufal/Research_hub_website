// React Query hooks for comparison data

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import * as comparisonApi from '../api/comparison';

// Hook to fetch comparison config
export function useComparisonConfig(projectId: string) {
    return useQuery({
        queryKey: ['comparison-config', projectId],
        queryFn: () => comparisonApi.getComparisonConfig(projectId),
        enabled: !!projectId,
    });
}

// Hook to update comparison config
export function useUpdateComparisonConfig() {
    const queryClient = useQueryClient();
    return useMutation({
        mutationFn: ({ projectId, config }: { projectId: string; config: comparisonApi.ComparisonConfigUpdate }) =>
            comparisonApi.updateComparisonConfig(projectId, config),
        onSuccess: (_, { projectId }) => {
            queryClient.invalidateQueries({ queryKey: ['comparison-config', projectId] });
        },
    });
}

// Hook to update comparison attribute
export function useUpdateComparisonAttribute() {
    const queryClient = useQueryClient();
    return useMutation({
        mutationFn: ({ projectId, paperId, attribute }: { projectId: string; paperId: string; attribute: comparisonApi.AttributeUpdate }) =>
            comparisonApi.updateComparisonAttribute(projectId, paperId, attribute),
        onSuccess: (_, { projectId }) => {
            queryClient.invalidateQueries({ queryKey: ['comparison-attributes', projectId] });
        },
    });
}

// Hook to fetch comparison attributes
export function useComparisonAttributes(projectId: string) {
    return useQuery({
        queryKey: ['comparison-attributes', projectId],
        queryFn: () => comparisonApi.getComparisonAttributes(projectId),
        enabled: !!projectId,
    });
}
