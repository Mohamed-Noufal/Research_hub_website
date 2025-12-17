// React Query hooks for synthesis data

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import * as synthesisApi from '../api/synthesis';

// Hook to fetch synthesis data
export function useSynthesisData(projectId: string) {
    return useQuery({
        queryKey: ['synthesis-data', projectId],
        queryFn: () => synthesisApi.getSynthesisData(projectId),
        enabled: !!projectId,
    });
}

// Hook to update synthesis structure
export function useUpdateSynthesisStructure() {
    const queryClient = useQueryClient();
    return useMutation({
        mutationFn: ({ projectId, structure }: { projectId: string; structure: synthesisApi.SynthesisStructure }) =>
            synthesisApi.updateSynthesisStructure(projectId, structure),
        onSuccess: (_, { projectId }) => {
            queryClient.invalidateQueries({ queryKey: ['synthesis-data', projectId] });
        },
    });
}

// Hook to update synthesis cell
export function useUpdateSynthesisCell() {
    const queryClient = useQueryClient();
    return useMutation({
        mutationFn: ({ projectId, cell }: { projectId: string; cell: synthesisApi.CellUpdate }) =>
            synthesisApi.updateSynthesisCell(projectId, cell),
        onSuccess: (_, { projectId }) => {
            queryClient.invalidateQueries({ queryKey: ['synthesis-data', projectId] });
        },
    });
}
