// React Query hooks for table configuration

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import * as tableConfigApi from '../api/tableConfig';

// Hook to fetch table configuration
export function useTableConfig(projectId: string, tabName: string) {
    return useQuery({
        queryKey: ['tableConfig', projectId, tabName],
        queryFn: () => tableConfigApi.getTableConfig(projectId, tabName),
        enabled: !!projectId && !!tabName,
    });
}

// Hook to update table configuration
export function useUpdateTableConfig() {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: ({
            projectId,
            tabName,
            config,
        }: {
            projectId: string;
            tabName: string;
            config: Partial<tableConfigApi.TableConfig>;
        }) => tableConfigApi.updateTableConfig(projectId, tabName, config),
        onSuccess: (_, { projectId, tabName }) => {
            queryClient.invalidateQueries({ queryKey: ['tableConfig', projectId, tabName] });
        },
    });
}

// Hook to fetch project papers
export function useProjectPapers(projectId: string) {
    return useQuery({
        queryKey: ['project-papers', projectId],
        queryFn: () => tableConfigApi.getProjectPapers(projectId),
        enabled: !!projectId,
    });
}

// Hook to update custom field
export function useUpdateCustomField() {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: ({
            projectId,
            paperId,
            fieldUpdate,
        }: {
            projectId: string;
            paperId: string;
            fieldUpdate: tableConfigApi.CustomFieldUpdate;
        }) => tableConfigApi.updateCustomField(projectId, paperId, fieldUpdate),
        onSuccess: (_, { projectId }) => {
            queryClient.invalidateQueries({ queryKey: ['project-papers', projectId] });
        },
    });
}
