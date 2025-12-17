// Shared types for Literature Review components

export interface Project {
    id: number;
    name: string;
    description: string;
    paperIds: number[];
    createdAt: string;
    updatedAt: string;
}

export interface ResearchPaper {
    id: number;
    title: string;
    authors: string[];
    year: number;
    methodology: string;
    methodologyType: string;
    methodologySummary: string;
    methodologyDescription: string;
    methodologyContext: string; // Previous work/lineage
    approachNovelty: string; // How it differs
    dataCollection: string;
    analysisMethod: string;
    sampleSize: string;
    keyFindings: string;
    qualityScore: number;
    limitations: string;
    strengths: string[];
    venue: string;
    doi: string;
    custom_fields?: Record<string, any>;
}

export interface ResearchGap {
    id: string;
    description: string;
    priority: 'High' | 'Medium' | 'Low';
    relatedPaperIds: number[];
}

export type Tab = 'summary' | 'analysis' | 'findings' | 'comparison' | 'synthesis' | 'methodology';
