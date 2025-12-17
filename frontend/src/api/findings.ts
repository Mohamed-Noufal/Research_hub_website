// API client for findings and gaps endpoints
import apiClient from './client';

export interface Gap {
    id: string;
    description: string;
    priority: 'High' | 'Medium' | 'Low';
    notes: string;
    related_paper_ids: string[];
}

export interface GapCreate {
    description: string;
    priority: 'High' | 'Medium' | 'Low';
    notes?: string;
}

export interface GapUpdate {
    description?: string;
    priority?: string;
    notes?: string;
}

export interface Finding {
    paper_id: string;
    title: string;
    key_finding: string;
    limitations: string;
}

export interface FindingUpdate {
    key_finding?: string;
    limitations?: string;
    custom_notes?: string;
}

// ===== GAPS API =====

export async function getGaps(projectId: string): Promise<{ gaps: Gap[] }> {
    const response = await apiClient.get(`/api/v1/projects/${projectId}/gaps`);
    return response.data;
}

export async function createGap(projectId: string, gap: GapCreate): Promise<void> {
    await apiClient.post(`/api/v1/projects/${projectId}/gaps`, gap);
}

export async function updateGap(projectId: string, gapId: string, gap: GapUpdate): Promise<void> {
    await apiClient.patch(`/api/v1/projects/${projectId}/gaps/${gapId}`, gap);
}

export async function deleteGap(projectId: string, gapId: string): Promise<void> {
    await apiClient.delete(`/api/v1/projects/${projectId}/gaps/${gapId}`);
}

// ===== FINDINGS API =====

export async function getFindings(projectId: string): Promise<{ findings: Finding[] }> {
    const response = await apiClient.get(`/api/v1/projects/${projectId}/findings`);
    return response.data;
}

export async function updateFinding(projectId: string, paperId: string, finding: FindingUpdate): Promise<void> {
    await apiClient.patch(`/api/v1/projects/${projectId}/findings/${paperId}`, finding);
}
