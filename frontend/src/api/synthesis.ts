// API client for synthesis endpoints
import apiClient from './client';

export interface ColumnDef {
    id: string;
    title: string;
    type: string; // added type to match backend expectation if needed
}

export interface RowDef {
    id: string;
    label: string;
}

export interface SynthesisData {
    columns: ColumnDef[];
    rows: RowDef[];
    cells: Record<string, string>;
}

export interface SynthesisStructure {
    columns: ColumnDef[];
    rows: RowDef[];
}

export interface CellUpdate {
    row_id: string;
    column_id: string;
    value: string;
}

// Get synthesis data
export async function getSynthesisData(projectId: string): Promise<SynthesisData> {
    const response = await apiClient.get(`/api/v1/projects/${projectId}/synthesis`);
    return response.data;
}

// Update synthesis structure
export async function updateSynthesisStructure(projectId: string, structure: SynthesisStructure): Promise<void> {
    await apiClient.put(`/api/v1/projects/${projectId}/synthesis/structure`, structure);
}

// Update synthesis cell
export async function updateSynthesisCell(projectId: string, cell: CellUpdate): Promise<void> {
    await apiClient.patch(`/api/v1/projects/${projectId}/synthesis/cells`, cell);
}
