// React Query hooks for findings and gaps

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import * as findingsApi from '../api/findings';

// ===== GAPS HOOKS =====

export function useGaps(projectId: string) {
    return useQuery({
        queryKey: ['gaps', projectId],
        queryFn: () => findingsApi.getGaps(projectId),
        enabled: !!projectId,
    });
}

export function useCreateGap() {
    const queryClient = useQueryClient();
    return useMutation({
        mutationFn: ({ projectId, gap }: { projectId: string; gap: findingsApi.GapCreate }) =>
            findingsApi.createGap(projectId, gap),
        onSuccess: (_, { projectId }) => {
            queryClient.invalidateQueries({ queryKey: ['gaps', projectId] });
        },
    });
}

export function useUpdateGap() {
    const queryClient = useQueryClient();
    return useMutation({
        mutationFn: ({ projectId, gapId, gap }: { projectId: string; gapId: string; gap: findingsApi.GapUpdate }) =>
            findingsApi.updateGap(projectId, gapId, gap),
        onSuccess: (_, { projectId }) => {
            queryClient.invalidateQueries({ queryKey: ['gaps', projectId] });
        },
    });
}

export function useDeleteGap() {
    const queryClient = useQueryClient();
    return useMutation({
        mutationFn: ({ projectId, gapId }: { projectId: string; gapId: string }) =>
            findingsApi.deleteGap(projectId, gapId),
        onSuccess: (_, { projectId }) => {
            queryClient.invalidateQueries({ queryKey: ['gaps', projectId] });
        },
    });
}

// ===== FINDINGS HOOKS =====

export function useFindings(projectId: string) {
    return useQuery({
        queryKey: ['findings', projectId],
        queryFn: () => findingsApi.getFindings(projectId),
        enabled: !!projectId,
    });
}

export function useUpdateFinding() {
    const queryClient = useQueryClient();
    return useMutation({
        mutationFn: ({ projectId, paperId, finding }: { projectId: string; paperId: string; finding: findingsApi.FindingUpdate }) =>
            findingsApi.updateFinding(projectId, paperId, finding),
        onSuccess: (_, { projectId }) => {
            queryClient.invalidateQueries({ queryKey: ['findings', projectId] });
        },
    });
}
