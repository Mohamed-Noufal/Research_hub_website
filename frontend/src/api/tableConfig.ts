// API client for table configuration endpoints
import apiClient from './client';

export interface ColumnConfig {
    id: string;
    label: string;
    field: string;
    type: 'text' | 'number' | 'select' | 'rating';
    width: number;
    visible: boolean;
    order: number;
    editable: boolean;
    isDefault: boolean;
}

export interface TableConfig {
    columns: ColumnConfig[];
    filters: any[];
    sort_config: Record<string, any>;
}

export interface CustomFieldUpdate {
    field_id: string;
    value: string;
}

// Get table configuration for a specific tab
export async function getTableConfig(projectId: string, tabName: string): Promise<TableConfig> {
    const response = await apiClient.get(`/api/v1/projects/${projectId}/tables/${tabName}/config`);
    return response.data;
}

// Update table configuration
export async function updateTableConfig(
    projectId: string,
    tabName: string,
    config: Partial<TableConfig>
): Promise<void> {
    await apiClient.put(
        `/api/v1/projects/${projectId}/tables/${tabName}/config`,
        config
    );
}

// Update custom field value for a paper
export async function updateCustomField(
    projectId: string,
    paperId: string,
    fieldUpdate: CustomFieldUpdate
): Promise<void> {
    await apiClient.patch(
        `/api/v1/projects/${projectId}/papers/${paperId}/custom-fields`,
        fieldUpdate
    );
}

// Get all papers in a project with custom fields
export async function getProjectPapers(projectId: string): Promise<any> {
    const response = await apiClient.get(`/api/v1/projects/${projectId}/papers`);
    return response.data;
}
