// API client for comparison endpoints
import apiClient from './client';

export interface ComparisonConfig {
    selected_paper_ids: string[];
    insights_similarities: string;
    insights_differences: string;
}

export interface ComparisonConfigUpdate {
    selected_paper_ids?: string[];
    insights_similarities?: string;
    insights_differences?: string;
}

export interface AttributeUpdate {
    attribute_name: string;
    attribute_value: string;
}

// Get comparison configuration
export async function getComparisonConfig(projectId: string): Promise<ComparisonConfig> {
    const response = await apiClient.get(`/api/v1/projects/${projectId}/comparison/config`);
    return response.data;
}

// Update comparison configuration
export async function updateComparisonConfig(projectId: string, config: ComparisonConfigUpdate): Promise<void> {
    await apiClient.put(`/api/v1/projects/${projectId}/comparison/config`, config);
}

// Update comparison attribute for a paper
export async function updateComparisonAttribute(
    projectId: string,
    paperId: string,
    attribute: AttributeUpdate
): Promise<void> {
    await apiClient.patch(`/api/v1/projects/${projectId}/comparison/attributes/${paperId}`, attribute);
}

export interface ComparisonAttributes {
    attributes: Record<string, string>;
}

// Get comparison attributes
export async function getComparisonAttributes(projectId: string): Promise<ComparisonAttributes> {
    const response = await apiClient.get(`/api/v1/projects/${projectId}/comparison/attributes`);
    return response.data;
}
