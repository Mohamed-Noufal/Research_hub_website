// Literature Review API Service Layer
// Connects frontend to our comprehensive Literature Review backend APIs

import { toast } from 'sonner';

const API_BASE = '/api/v1/users';

// Types matching our backend models
export interface LiteratureReviewProject {
  id: number;
  user_id: string;
  title: string;
  description?: string;
  paper_ids: number[];
  status: 'draft' | 'active' | 'completed' | 'archived';
  review_metadata: Record<string, any>;
  export_data: Record<string, any>;
  ai_features_enabled: boolean;
  advanced_analytics: Record<string, any>;
  custom_views: Record<string, any>;
  created_at: string;
  updated_at: string;
}

export interface LiteratureReviewAnnotation {
  id: number;
  review_id: number;
  paper_id: number;
  methodology?: string;
  sample_size?: string;
  key_findings: string[];
  limitations: string[];
  notes?: string;
  created_at: string;
  updated_at: string;
}

export interface LiteratureReviewFinding {
  id: number;
  review_id: number;
  description: string;
  supporting_papers: number[];
  finding_type?: 'positive' | 'negative' | 'neutral';
  evidence_level?: 'strong' | 'moderate' | 'weak';
  citation_count: number;
  methodology_match?: Record<string, any>;
  created_at: string;
  updated_at: string;
}

export interface PaperComparison {
  id: number;
  project_id: number;
  paper_ids: number[];
  comparison_data?: Record<string, any>;
  created_at: string;
  updated_at: string;
}

export interface CitationFormat {
  id: number;
  project_id: number;
  format_type: 'APA' | 'MLA' | 'Chicago' | 'Harvard';
  custom_template?: string;
  created_at: string;
  updated_at: string;
}

export interface ResearchTheme {
  id: number;
  project_id: number;
  theme_name: string;
  theme_description?: string;
  supporting_findings: number[];
  paper_count: number;
  theme_strength?: 'strong' | 'moderate' | 'weak';
  created_at: string;
  updated_at: string;
}

// Phase 3 Advanced Features
export interface SpreadsheetTemplate {
  id: number;
  project_id: number;
  template_name: string;
  template_config?: Record<string, any>;
  created_at: string;
  updated_at: string;
}

export interface SpreadsheetData {
  id: number;
  template_id: number;
  project_id: number;
  row_data: Record<string, any>;
  cell_data?: Record<string, any>;
  created_at: string;
  updated_at: string;
}

export interface AISynthesis {
  id: number;
  project_id: number;
  synthesis_type: 'summary' | 'comparison' | 'theme_analysis' | 'methodology' | 'gap_analysis';
  input_data?: Record<string, any>;
  ai_prompt: string;
  ai_response?: string;
  confidence_score?: number;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  created_at: string;
  completed_at?: string;
  updated_at: string;
}

export interface ExportConfiguration {
  id: number;
  project_id: number;
  export_type: 'word' | 'excel' | 'pdf' | 'csv';
  template_name?: string;
  configuration?: Record<string, any>;
  output_path?: string;
  status: 'draft' | 'generating' | 'completed' | 'failed';
  created_at: string;
  updated_at: string;
}

export interface AnalysisTemplate {
  id: number;
  project_id: number;
  template_type: 'comparison_matrix' | 'evidence_table' | 'methodology_table';
  template_config: Record<string, any>;
  custom_fields?: Record<string, any>;
  is_public: boolean;
  created_at: string;
  updated_at: string;
}

// Request/Response types
export interface CreateProjectRequest {
  title: string;
  description?: string;
  paper_ids?: number[];
}

export interface CreateAnnotationRequest {
  review_id: number;
  paper_id: number;
  methodology?: string;
  sample_size?: string;
  key_findings: string[];
  limitations: string[];
  notes?: string;
}

export interface CreateFindingRequest {
  review_id: number;
  description: string;
  supporting_papers: number[];
  finding_type?: 'positive' | 'negative' | 'neutral';
  evidence_level?: 'strong' | 'moderate' | 'weak';
}

export interface CreateSpreadsheetTemplateRequest {
  project_id: number;
  template_name: string;
  template_config?: Record<string, any>;
}

export interface CreateAISynthesisRequest {
  project_id: number;
  synthesis_type: 'summary' | 'comparison' | 'theme_analysis' | 'methodology' | 'gap_analysis';
  input_data?: Record<string, any>;
  ai_prompt: string;
}

export interface CreateExportConfigurationRequest {
  project_id: number;
  export_type: 'word' | 'excel' | 'pdf' | 'csv';
  template_name?: string;
  configuration?: Record<string, any>;
}

class LiteratureReviewAPI {
  // Helper method for API calls
  private async apiCall<T>(endpoint: string, options?: RequestInit): Promise<T> {
    try {
      const response = await fetch(`${API_BASE}${endpoint}`, {
        headers: {
          'Content-Type': 'application/json',
          ...options?.headers,
        },
        ...options,
      });

      if (!response.ok) {
        const error = await response.json().catch(() => ({ detail: 'Unknown error' }));
        throw new Error(error.detail || `HTTP ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error('API Error:', error);
      toast.error(`API Error: ${error instanceof Error ? error.message : 'Unknown error'}`);
      throw error;
    }
  }

  // Phase 1: Core Literature Review Management
  async getProjects(): Promise<LiteratureReviewProject[]> {
    const response = await this.apiCall<{ reviews: LiteratureReviewProject[]; total: number }>(
      '/literature-reviews'
    );
    return response.reviews;
  }

  async createProject(data: CreateProjectRequest): Promise<LiteratureReviewProject> {
    return await this.apiCall<LiteratureReviewProject>('/literature-reviews', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async updateProject(
    id: number, 
    data: Partial<CreateProjectRequest>
  ): Promise<void> {
    await this.apiCall(`/literature-reviews/${id}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  }

  async deleteProject(id: number): Promise<void> {
    await this.apiCall(`/literature-reviews/${id}`, {
      method: 'DELETE',
    });
  }

  // Phase 1: Paper Annotations & Findings
  async createAnnotation(data: CreateAnnotationRequest): Promise<LiteratureReviewAnnotation> {
    return await this.apiCall<LiteratureReviewAnnotation>(
      `/literature-reviews/${data.review_id}/annotations`,
      {
        method: 'POST',
        body: JSON.stringify(data),
      }
    );
  }

  async getAnnotations(reviewId: number, paperId?: number): Promise<LiteratureReviewAnnotation[]> {
    const params = paperId ? `?paper_id=${paperId}` : '';
    const response = await this.apiCall<{ annotations: LiteratureReviewAnnotation[]; total: number }>(
      `/literature-reviews/${reviewId}/annotations${params}`
    );
    return response.annotations;
  }

  async updateAnnotation(
    id: number,
    data: Partial<CreateAnnotationRequest>
  ): Promise<void> {
    await this.apiCall(`/literature-reviews/annotations/${id}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  }

  async deleteAnnotation(id: number): Promise<void> {
    await this.apiCall(`/literature-reviews/annotations/${id}`, {
      method: 'DELETE',
    });
  }

  async createFinding(data: CreateFindingRequest): Promise<LiteratureReviewFinding> {
    return await this.apiCall<LiteratureReviewFinding>(
      `/literature-reviews/${data.review_id}/findings`,
      {
        method: 'POST',
        body: JSON.stringify(data),
      }
    );
  }

  async getFindings(reviewId: number): Promise<LiteratureReviewFinding[]> {
    const response = await this.apiCall<{ findings: LiteratureReviewFinding[]; total: number }>(
      `/literature-reviews/${reviewId}/findings`
    );
    return response.findings;
  }

  async updateFinding(
    id: number,
    data: Partial<CreateFindingRequest>
  ): Promise<void> {
    await this.apiCall(`/literature-reviews/findings/${id}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  }

  async deleteFinding(id: number): Promise<void> {
    await this.apiCall(`/literature-reviews/findings/${id}`, {
      method: 'DELETE',
    });
  }

  // Phase 2: Research Analysis Features
  async createPaperComparison(
    projectId: number,
    paperIds: number[],
    comparisonData?: Record<string, any>
  ): Promise<PaperComparison> {
    return await this.apiCall<PaperComparison>(
      `/literature-reviews/${projectId}/comparisons`,
      {
        method: 'POST',
        body: JSON.stringify({
          project_id: projectId,
          paper_ids: paperIds,
          comparison_data: comparisonData,
        }),
      }
    );
  }

  async getPaperComparisons(projectId: number): Promise<PaperComparison[]> {
    const response = await this.apiCall<{ comparisons: PaperComparison[]; total: number }>(
      `/literature-reviews/${projectId}/comparisons`
    );
    return response.comparisons;
  }

  async updatePaperComparison(
    id: number,
    comparisonData: Record<string, any>
  ): Promise<void> {
    await this.apiCall(`/literature-reviews/comparisons/${id}`, {
      method: 'PUT',
      body: JSON.stringify({ comparison_data: comparisonData }),
    });
  }

  async deletePaperComparison(id: number): Promise<void> {
    await this.apiCall(`/literature-reviews/comparisons/${id}`, {
      method: 'DELETE',
    });
  }

  async createCitationFormat(
    projectId: number,
    formatType: 'APA' | 'MLA' | 'Chicago' | 'Harvard',
    customTemplate?: string
  ): Promise<CitationFormat> {
    return await this.apiCall<CitationFormat>(
      `/literature-reviews/${projectId}/citations`,
      {
        method: 'POST',
        body: JSON.stringify({
          project_id: projectId,
          format_type: formatType,
          custom_template: customTemplate,
        }),
      }
    );
  }

  async getCitationFormats(projectId: number, formatType?: string): Promise<CitationFormat[]> {
    const params = formatType ? `?format_type=${formatType}` : '';
    const response = await this.apiCall<{ formats: CitationFormat[]; total: number }>(
      `/literature-reviews/${projectId}/citations${params}`
    );
    return response.formats;
  }

  async updateCitationFormat(
    id: number,
    formatType?: string,
    customTemplate?: string
  ): Promise<void> {
    await this.apiCall(`/literature-reviews/citations/${id}`, {
      method: 'PUT',
      body: JSON.stringify({
        format_type: formatType,
        custom_template: customTemplate,
      }),
    });
  }

  async deleteCitationFormat(id: number): Promise<void> {
    await this.apiCall(`/literature-reviews/citations/${id}`, {
      method: 'DELETE',
    });
  }

  async createResearchTheme(
    projectId: number,
    themeName: string,
    themeDescription?: string,
    supportingFindings: number[] = [],
    themeStrength?: 'strong' | 'moderate' | 'weak'
  ): Promise<ResearchTheme> {
    return await this.apiCall<ResearchTheme>(
      `/literature-reviews/${projectId}/themes`,
      {
        method: 'POST',
        body: JSON.stringify({
          project_id: projectId,
          theme_name: themeName,
          theme_description: themeDescription,
          supporting_findings: supportingFindings,
          theme_strength: themeStrength,
        }),
      }
    );
  }

  async getResearchThemes(projectId: number): Promise<ResearchTheme[]> {
    const response = await this.apiCall<{ themes: ResearchTheme[]; total: number }>(
      `/literature-reviews/${projectId}/themes`
    );
    return response.themes;
  }

  async updateResearchTheme(
    id: number,
    data: Partial<{
      theme_name: string;
      theme_description: string;
      supporting_findings: number[];
      theme_strength: 'strong' | 'moderate' | 'weak';
    }>
  ): Promise<void> {
    await this.apiCall(`/literature-reviews/themes/${id}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  }

  async deleteResearchTheme(id: number): Promise<void> {
    await this.apiCall(`/literature-reviews/themes/${id}`, {
      method: 'DELETE',
    });
  }

  // Phase 3: Advanced Features
  async createSpreadsheetTemplate(
    data: CreateSpreadsheetTemplateRequest
  ): Promise<SpreadsheetTemplate> {
    return await this.apiCall<SpreadsheetTemplate>(
      `/literature-reviews/${data.project_id}/spreadsheet-templates`,
      {
        method: 'POST',
        body: JSON.stringify(data),
      }
    );
  }

  async getSpreadsheetTemplates(projectId: number): Promise<SpreadsheetTemplate[]> {
    const response = await this.apiCall<{ templates: SpreadsheetTemplate[]; total: number }>(
      `/literature-reviews/${projectId}/spreadsheet-templates`
    );
    return response.templates;
  }

  async createAISynthesis(data: CreateAISynthesisRequest): Promise<AISynthesis> {
    return await this.apiCall<AISynthesis>(
      `/literature-reviews/${data.project_id}/ai-synthesis`,
      {
        method: 'POST',
        body: JSON.stringify(data),
      }
    );
  }

  async getAISynthesis(projectId: number): Promise<AISynthesis[]> {
    const response = await this.apiCall<{ synthesis: AISynthesis[]; total: number }>(
      `/literature-reviews/${projectId}/ai-synthesis`
    );
    return response.synthesis;
  }

  async createExportConfiguration(
    data: CreateExportConfigurationRequest
  ): Promise<ExportConfiguration> {
    return await this.apiCall<ExportConfiguration>(
      `/literature-reviews/${data.project_id}/export-configurations`,
      {
        method: 'POST',
        body: JSON.stringify(data),
      }
    );
  }

  async getExportConfigurations(projectId: number): Promise<ExportConfiguration[]> {
    const response = await this.apiCall<{ configurations: ExportConfiguration[]; total: number }>(
      `/literature-reviews/${projectId}/export-configurations`
    );
    return response.configurations;
  }

  // Analysis endpoints
  async getMethodologyAnalysis(projectId: number): Promise<any> {
    const response = await this.apiCall<{ analysis: any; methodologies: string[] }>(
      `/literature-reviews/${projectId}/methodology-analysis`
    );
    return response;
  }

  async comparePapers(
    projectId: number,
    paperId1: number,
    paperId2: number
  ): Promise<any> {
    const response = await this.apiCall<{ comparison: any }>(
      `/literature-reviews/${projectId}/comparison/${paperId1}/${paperId2}`
    );
    return response.comparison;
  }

  async analyzeThemes(projectId: number): Promise<any> {
    const response = await this.apiCall<{ themes: any[]; analysis: any }>(
      `/literature-reviews/${projectId}/theme-analysis`,
      {
        method: 'POST',
      }
    );
    return response;
  }
}

// Export singleton instance
export const literatureReviewAPI = new LiteratureReviewAPI();

// Default export for convenience
export default literatureReviewAPI;
