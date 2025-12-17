// API client for methodology endpoints
import apiClient from './client';

export interface MethodologyData {
    paper_id: string;
    title: string;
    methodology: string;
    methodology_type: string;
    methodology_description: string;
    methodology_context: string;
    approach_novelty: string;
    custom_attributes: Record<string, any>;
}

export interface MethodologyUpdate {
    methodology_description?: string;
    methodology_context?: string;
    approach_novelty?: string;
}

// Get methodology data for all papers in a project
export async function getMethodologyData(projectId: string): Promise<{ papers: MethodologyData[] }> {
    const response = await apiClient.get(`/api/v1/projects/${projectId}/methodology`);
    return response.data;
}

// Update methodology data for a specific paper
export async function updateMethodologyData(
    projectId: string,
    paperId: string,
    data: MethodologyUpdate
): Promise<void> {
    await apiClient.patch(
        `/api/v1/projects/${projectId}/methodology/${paperId}`,
        data
    );
}
