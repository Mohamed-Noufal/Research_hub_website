// Mock data for Literature Review components
import type { Project, ResearchPaper, ResearchGap } from './types';

export const MOCK_PAPERS: ResearchPaper[] = [
    {
        id: 1,
        title: "Deep Learning for Medical Diagnosis: A Systematic Review",
        authors: ["Smith, J.", "Johnson, M.", "Williams, R."],
        year: 2023,
        methodology: "Experimental",
        methodologyType: "Randomized Controlled Trial",
        methodologySummary: "Double-blind RCT comparing AI diagnosis vs. human radiologists across 3 hospitals.",
        methodologyDescription: "Utilized a multi-center randomized controlled trial design. Patients were randomly assigned to either standard radiologist diagnosis or AI-assisted diagnosis groups. The AI model was pre-trained on a dataset of 100,000 images.",
        methodologyContext: "Builds on previous retrospective studies (e.g., Jones et al., 2021) that suggested potential AI superiority but lacked clinical validation.",
        approachNovelty: "First study to implement this specific deep learning architecture in a live clinical workflow rather than a simulation.",
        dataCollection: "Clinical measurements, EHR data",
        analysisMethod: "ANOVA, Logistic Regression",
        sampleSize: "150 patients",
        keyFindings: "95% accuracy in diagnosis, significant improvement over baseline (p<0.001).",
        qualityScore: 5,
        limitations: "Small sample size, single center study",
        strengths: ["Large sample for pilot", "RCT design"],
        venue: "Nature Medicine",
        doi: "10.1038/s41591-023-xxxxx"
    },
    {
        id: 2,
        title: "AI Adoption in Clinical Practice: Barriers and Opportunities",
        authors: ["Johnson, K.", "Lee, S.", "Chen, W."],
        year: 2022,
        methodology: "Survey",
        methodologyType: "Cross-sectional",
        methodologySummary: "National online survey of clinical directors assessing AI readiness and barriers.",
        methodologyDescription: "Employed a cross-sectional survey design using a validated technology acceptance instrument. Distributed via national medical association mailing lists.",
        methodologyContext: "Contrasts with earlier qualitative interviews that identified barriers but could not quantify their prevalence.",
        approachNovelty: "Focuses specifically on the 'post-implementation' phase, whereas most prior work looked at 'pre-implementation' intent.",
        dataCollection: "Online questionnaires (Likert scale)",
        analysisMethod: "Descriptive statistics, Chi-square",
        sampleSize: "500 clinics",
        keyFindings: "60% adoption rate. Top barriers: cost (45%), training (30%).",
        qualityScore: 3,
        limitations: "Self-reported data, response bias",
        strengths: ["Large sample", "Diverse settings"],
        venue: "JAMA",
        doi: "10.1001/jama.2022.xxxxx"
    },
    {
        id: 3,
        title: "Neural Networks in Radiology: Real-World Implementation",
        authors: ["Chen, L.", "Wang, X.", "Kumar, P."],
        year: 2023,
        methodology: "Case Study",
        methodologyType: "Qualitative",
        methodologySummary: "In-depth observational study of a single radiology department implementing a new AI tool.",
        methodologyDescription: "Longitudinal case study over 6 months. Researchers conducted weekly observations of radiologist workflows and semi-structured interviews at multiple timepoints.",
        methodologyContext: "Extends the 'workflow disruption' theory proposed by Brown (2019) by applying it to AI tools specifically.",
        approachNovelty: "Uses ethnographic methods to capture the 'hidden work' of AI integration often missed in quantitative performance metrics.",
        dataCollection: "Semi-structured interviews, observations",
        analysisMethod: "Thematic analysis, Grounded theory",
        sampleSize: "50 scans",
        keyFindings: "30% time reduction in workflow, improved accuracy.",
        qualityScore: 4,
        limitations: "Single institution, small sample",
        strengths: ["Real-world data", "Detailed analysis"],
        venue: "Radiology",
        doi: "10.1148/radiol.2023xxxxx"
    },
    {
        id: 4,
        title: "Machine Learning in Predictive Healthcare Analytics",
        authors: ["Brown, A.", "Davis, M."],
        year: 2023,
        methodology: "Meta-Analysis",
        methodologyType: "Systematic Review",
        methodologySummary: "Systematic review and meta-analysis of predictive ML models in critical care.",
        methodologyDescription: "Followed PRISMA guidelines. Searched 4 major databases. Included studies reporting AUC-ROC for mortality prediction models.",
        methodologyContext: "Updates the 2018 review by Wilson et al., incorporating the wave of transformer-based models released since then.",
        approachNovelty: "First meta-analysis to stratify results by 'data modality' (images vs. tabular data), revealing significant performance gaps.",
        dataCollection: "Database search (PubMed, IEEE, Scopus)",
        analysisMethod: "Meta-regression, Subgroup analysis",
        sampleSize: "45 studies",
        keyFindings: "Pooled accuracy 87% (95% CI: 84-90%). ML shows promise.",
        qualityScore: 5,
        limitations: "Publication bias, heterogeneous methodologies",
        strengths: ["Comprehensive search", "Large study pool"],
        venue: "The Lancet Digital Health",
        doi: "10.1016/S2589-7500(23)xxxxx"
    },
    {
        id: 5,
        title: "Ethical Considerations in AI-Driven Diagnosis",
        authors: ["Martinez, R.", "Thompson, K.", "Anderson, J."],
        year: 2022,
        methodology: "Review",
        methodologyType: "Literature Review",
        methodologySummary: "Critical narrative review of ethical frameworks applied to AI diagnostic tools.",
        methodologyDescription: "Narrative synthesis of ethical guidelines published by major medical bodies and AI ethics institutes.",
        methodologyContext: "Responds to the 'black box' problem highlighted in technical literature, translating it into clinical ethical terms.",
        approachNovelty: "Proposes a new 'Clinical AI Ethics Framework' that integrates patient autonomy with algorithmic transparency.",
        dataCollection: "Narrative synthesis of existing literature",
        analysisMethod: "Critical framework analysis",
        sampleSize: "120 papers",
        keyFindings: "Key ethical concerns: bias, transparency, accountability.",
        qualityScore: 4,
        limitations: "Rapidly evolving field",
        strengths: ["Comprehensive coverage", "Multidisciplinary perspective"],
        venue: "AI & Ethics",
        doi: "10.1007/s43681-022-xxxxx"
    }
];

export const MOCK_PROJECTS: Project[] = [
    {
        id: 1,
        name: "AI in Healthcare Review",
        description: "Systematic review of AI adoption barriers and clinical outcomes in healthcare settings (2020-2024).",
        paperIds: [1, 2, 3, 4, 5],
        createdAt: "2023-10-15",
        updatedAt: "2023-11-20"
    },
    {
        id: 2,
        name: "LLM Hallucination Mitigation",
        description: "Survey of techniques for reducing hallucinations in large language models.",
        paperIds: [1, 4],
        createdAt: "2023-11-01",
        updatedAt: "2023-11-22"
    }
];

export const MOCK_GAPS: ResearchGap[] = [
    {
        id: 'g1',
        description: "Lack of longitudinal studies on long-term patient outcomes after AI diagnosis",
        priority: 'High',
        relatedPaperIds: [1, 3]
    },
    {
        id: 'g2',
        description: "Limited research on AI adoption in low-resource healthcare settings",
        priority: 'Medium',
        relatedPaperIds: [2]
    }
];
