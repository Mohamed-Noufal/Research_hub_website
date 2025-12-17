import { useState } from 'react';
import { Search, Clipboard, Trash2, Download, BookmarkPlus, ExternalLink, Eye } from 'lucide-react';

interface FetchedPaper {
    doi: string;
    title: string;
    authors: string[];
    journal: string;
    year: number;
    citations: number;
    impactFactor?: number;
    abstract: string;
    tags?: string[];
    openAccess?: boolean;
    pdfUrl?: string;
    status: 'fetched' | 'loading' | 'error';
}

interface DOIFetcherProps {
    onPaperSaved?: () => void;  // Callback to refresh library
}

export default function DOIFetcher({ onPaperSaved }: DOIFetcherProps = {}) {
    const [doiInput, setDoiInput] = useState('');
    const [fetchedPapers, setFetchedPapers] = useState<FetchedPaper[]>([]);
    const [isLoading, setIsLoading] = useState(false);

    // Validate DOI format
    const validateDOI = (doi: string): boolean => {
        const doiRegex = /^10\.\d{4,}\/[^\s]+$/;
        return doiRegex.test(doi.trim());
    };

    // Parse DOIs from input (one per line)
    const parseDOIs = (input: string): string[] => {
        return input
            .split('\n')
            .map(line => line.trim())
            .filter(line => line.length > 0);
    };

    // Get validation status for each line
    const getValidationStatus = () => {
        const dois = parseDOIs(doiInput);
        const valid = dois.filter(validateDOI).length;
        const invalid = dois.length - valid;
        return { total: dois.length, valid, invalid };
    };

    // Fetch paper from backend API
    const fetchPaperByDOI = async (doi: string): Promise<FetchedPaper> => {
        try {
            const { apiService } = await import('../../services/api');

            const response = await apiService.fetchPaperByDOI(doi);
            const paper = response.paper;

            return {
                doi: paper.doi || doi,
                title: paper.title || `Paper for DOI: ${doi}`,
                authors: paper.authors || [],
                journal: paper.venue || 'Unknown Journal',
                year: paper.publication_date ? new Date(paper.publication_date).getFullYear() : new Date().getFullYear(),
                citations: paper.citation_count || 0,
                abstract: paper.abstract || 'Abstract not available.',
                openAccess: paper.pdf_url ? true : false,
                pdfUrl: paper.pdf_url,
                status: 'fetched',
            };
        } catch (error) {
            console.error(`Failed to fetch DOI ${doi}:`, error);
            throw error;
        }
    };

    // Fetch all papers
    const handleFetchAll = async () => {
        const dois = parseDOIs(doiInput).filter(validateDOI);
        if (dois.length === 0) return;

        setIsLoading(true);
        const papers: FetchedPaper[] = [];

        for (const doi of dois) {
            try {
                const paper = await fetchPaperByDOI(doi);
                papers.push(paper);
                setFetchedPapers([...papers]);
            } catch (error) {
                papers.push({
                    doi,
                    title: 'Error fetching paper',
                    authors: [],
                    journal: '',
                    year: 0,
                    citations: 0,
                    abstract: '',
                    status: 'error',
                });
            }
        }

        setIsLoading(false);
    };

    // Paste from clipboard
    const handlePaste = async () => {
        try {
            const text = await navigator.clipboard.readText();
            setDoiInput(text);
        } catch (error) {
            console.error('Failed to read clipboard:', error);
        }
    };

    // Clear all
    const handleClear = () => {
        setDoiInput('');
        setFetchedPapers([]);
    };

    const status = getValidationStatus();

    return (
        <div className="h-full w-full flex flex-col bg-white">
            {/* Header */}
            <div className="h-12 border-b border-gray-200 flex items-center justify-between px-4 bg-gradient-to-r from-purple-50 to-blue-50">
                <div className="flex items-center gap-2">
                    <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-purple-500 to-blue-500 flex items-center justify-center">
                        <Search className="w-5 h-5 text-white" />
                    </div>
                    <h2 className="text-sm font-semibold text-gray-900">DOI Fetching Tool</h2>
                </div>
                <div className="text-xs text-gray-500">
                    Fetch papers by DOI instantly
                </div>
            </div>

            {/* Main Content */}
            <div className="flex-1 flex overflow-hidden">
                {/* LEFT PANEL - Input */}
                <div className="w-1/3 min-w-[320px] max-w-[450px] border-r border-gray-200 flex flex-col bg-gray-50">
                    <div className="p-4 border-b border-gray-200 bg-white">
                        <h3 className="text-sm font-semibold text-gray-700 mb-1">📝 Enter DOI(s)</h3>
                        <p className="text-xs text-gray-500">One DOI per line</p>
                    </div>

                    <div className="flex-1 p-4">
                        <textarea
                            value={doiInput}
                            onChange={(e) => setDoiInput(e.target.value)}
                            placeholder="10.1038/nature12345&#10;10.1145/3...&#10;10.1016/j..."
                            className="w-full h-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent resize-none font-mono text-sm"
                        />
                    </div>

                    <div className="p-4 border-t border-gray-200 bg-white space-y-3">
                        <div className="flex gap-2">
                            <button
                                onClick={handlePaste}
                                className="flex-1 px-3 py-2 text-xs font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors flex items-center justify-center gap-1"
                            >
                                <Clipboard className="w-3.5 h-3.5" />
                                Paste
                            </button>
                            <button
                                onClick={handleClear}
                                className="flex-1 px-3 py-2 text-xs font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors flex items-center justify-center gap-1"
                            >
                                <Trash2 className="w-3.5 h-3.5" />
                                Clear
                            </button>
                        </div>

                        <div className="p-3 bg-blue-50 rounded-lg border border-blue-200">
                            <div className="text-xs font-semibold text-gray-700 mb-2">Status:</div>
                            <div className="space-y-1 text-xs">
                                <div className="flex items-center justify-between">
                                    <span className="text-gray-600">✅ Valid DOIs:</span>
                                    <span className="font-semibold text-green-600">{status.valid}</span>
                                </div>
                                <div className="flex items-center justify-between">
                                    <span className="text-gray-600">⏳ Pending:</span>
                                    <span className="font-semibold text-gray-600">{status.total - status.valid}</span>
                                </div>
                                <div className="flex items-center justify-between">
                                    <span className="text-gray-600">❌ Errors:</span>
                                    <span className="font-semibold text-red-600">{status.invalid}</span>
                                </div>
                            </div>
                        </div>

                        <button
                            onClick={handleFetchAll}
                            disabled={status.valid === 0 || isLoading}
                            className="w-full px-4 py-3 text-sm font-semibold text-white bg-gradient-to-r from-purple-600 to-blue-600 rounded-lg hover:from-purple-700 hover:to-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all flex items-center justify-center gap-2 shadow-md hover:shadow-lg"
                        >
                            <Search className="w-4 h-4" />
                            {isLoading ? 'Fetching...' : `Fetch ${status.valid} Paper${status.valid !== 1 ? 's' : ''}`}
                        </button>

                        <div className="p-3 bg-gray-100 rounded-lg">
                            <div className="text-xs font-semibold text-gray-700 mb-1">💡 Tips:</div>
                            <ul className="text-xs text-gray-600 space-y-0.5">
                                <li>• One DOI per line</li>
                                <li>• Format: 10.xxxx/...</li>
                                <li>• Max 50 DOIs at once</li>
                            </ul>
                        </div>
                    </div>
                </div>

                {/* RIGHT PANEL - Results */}
                <div className="flex-1 flex flex-col bg-white">
                    <div className="p-4 border-b border-gray-200 flex items-center justify-between">
                        <h3 className="text-sm font-semibold text-gray-700">
                            📊 Found Papers ({fetchedPapers.length})
                        </h3>
                        {fetchedPapers.length > 0 && (
                            <div className="flex gap-2">
                                <button className="px-3 py-1.5 text-xs font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors flex items-center gap-1">
                                    <BookmarkPlus className="w-3.5 h-3.5" />
                                    Save All
                                </button>
                                <button className="px-3 py-1.5 text-xs font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors flex items-center gap-1">
                                    <Download className="w-3.5 h-3.5" />
                                    Export BibTeX
                                </button>
                            </div>
                        )}
                    </div>

                    <div className="flex-1 overflow-y-auto p-4 space-y-3">
                        {fetchedPapers.length === 0 ? (
                            <div className="flex flex-col items-center justify-center h-full text-gray-400">
                                <div className="w-16 h-16 bg-gray-100 rounded-2xl flex items-center justify-center mb-3">
                                    <Search className="w-8 h-8 text-gray-300" />
                                </div>
                                <p className="text-sm font-medium">No papers fetched yet</p>
                                <p className="text-xs text-gray-400 mt-1">Enter DOIs and click "Fetch Papers"</p>
                            </div>
                        ) : (
                            fetchedPapers.map((paper, index) => (
                                <PaperCard key={paper.doi} paper={paper} index={index} onPaperSaved={onPaperSaved} />
                            ))
                        )}
                    </div>
                </div>
            </div>
        </div>
    );
}

// Paper Card Component
function PaperCard({ paper, index, onPaperSaved }: { paper: FetchedPaper; index: number; onPaperSaved?: () => void }) {
    const [isExpanded, setIsExpanded] = useState(false);
    const [isSaving, setIsSaving] = useState(false);
    const [isSaved, setIsSaved] = useState(false);

    const getIcon = () => {
        if (paper.journal.toLowerCase().includes('conference') || paper.journal.toLowerCase().includes('acl')) {
            return '🔬';
        }
        return '🎓';
    };

    const formatAuthors = (authors: string[]) => {
        if (authors.length === 0) return 'Unknown';
        if (authors.length <= 3) return authors.join(', ');
        return `${authors.slice(0, 3).join(', ')}, et al. (${authors.length} authors)`;
    };

    const handleSaveToLibrary = async () => {
        setIsSaving(true);
        try {
            const { apiService } = await import('../../services/api');

            const response = await apiService.fetchPaperByDOI(paper.doi);
            const paperId = parseInt(response.paper.id);

            await apiService.savePaper(paperId);
            setIsSaved(true);

            // Call callback to refresh library
            if (onPaperSaved) {
                onPaperSaved();
            }

            alert('✅ Paper saved to library! Check the Library tab to see it.');
        } catch (error) {
            console.error('Failed to save paper:', error);
            alert('❌ Failed to save paper. Please try again.');
        } finally {
            setIsSaving(false);
        }
    };

    const handleViewPDF = () => {
        if (paper.pdfUrl) {
            window.open(paper.pdfUrl, '_blank', 'noopener,noreferrer');
        } else {
            const doiUrl = `https://doi.org/${paper.doi}`;
            window.open(doiUrl, '_blank', 'noopener,noreferrer');
        }
    };

    const handleOpenDOI = () => {
        const doiUrl = `https://doi.org/${paper.doi}`;
        window.open(doiUrl, '_blank', 'noopener,noreferrer');
    };

    return (
        <div
            className="bg-white border border-gray-200 rounded-xl p-4 hover:shadow-lg transition-all duration-300 hover:-translate-y-1"
            style={{ animationDelay: `${index * 100}ms` }}
        >
            <div className="flex items-start gap-2 mb-2">
                <span className="text-xl">{getIcon()}</span>
                <h4 className="flex-1 text-sm font-semibold text-gray-900 leading-snug">
                    {paper.title}
                </h4>
            </div>

            <div className="flex items-center gap-1.5 text-xs text-gray-600 mb-2">
                <span>👥</span>
                <span>{formatAuthors(paper.authors)}</span>
            </div>

            <div className="flex items-center gap-3 text-xs text-gray-500 mb-3">
                <span>📅 {paper.journal} • {paper.year}</span>
                {paper.citations > 0 && <span>📊 {paper.citations} citations</span>}
                {paper.impactFactor && <span>• IF: {paper.impactFactor}</span>}
                {paper.openAccess && <span className="text-green-600">🔓 Open Access</span>}
            </div>

            {paper.abstract && (
                <div className="mb-3">
                    <p className="text-xs text-gray-600 leading-relaxed">
                        📄 {isExpanded ? paper.abstract : `${paper.abstract.substring(0, 120)}...`}
                        {paper.abstract.length > 120 && (
                            <button
                                onClick={() => setIsExpanded(!isExpanded)}
                                className="text-purple-600 hover:text-purple-700 ml-1 font-medium"
                            >
                                {isExpanded ? 'Show less' : 'Read more'}
                            </button>
                        )}
                    </p>
                </div>
            )}

            {paper.tags && paper.tags.length > 0 && (
                <div className="flex flex-wrap gap-1.5 mb-3">
                    {paper.tags.map((tag, i) => (
                        <span
                            key={i}
                            className="px-2 py-0.5 text-xs font-medium text-purple-700 bg-purple-50 rounded-full"
                        >
                            {tag}
                        </span>
                    ))}
                </div>
            )}

            <div className="flex items-center gap-2 mb-3">
                {isSaved ? (
                    <span className="text-xs text-green-600 font-medium">✅ Saved to Library</span>
                ) : (
                    <span className="text-xs text-green-600 font-medium">✅ Fetched</span>
                )}
                <span className="text-xs text-gray-400">• {paper.doi}</span>
            </div>

            <div className="flex gap-2">
                <button
                    onClick={handleSaveToLibrary}
                    disabled={isSaving || isSaved}
                    className="flex-1 px-3 py-2 text-xs font-semibold text-white bg-gradient-to-r from-purple-600 to-blue-600 rounded-lg hover:from-purple-700 hover:to-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all flex items-center justify-center gap-1.5 shadow-sm"
                >
                    <BookmarkPlus className="w-3.5 h-3.5" />
                    {isSaving ? 'Saving...' : isSaved ? 'Saved ✓' : 'Save to Library'}
                </button>
                <button
                    onClick={handleViewPDF}
                    className="px-3 py-2 text-xs font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors flex items-center gap-1"
                    title={paper.pdfUrl ? "View PDF" : "View paper (opens DOI link)"}
                >
                    <Eye className="w-3.5 h-3.5" />
                    {paper.pdfUrl ? 'PDF' : 'View'}
                </button>
                <button
                    onClick={handleOpenDOI}
                    className="px-3 py-2 text-xs font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors flex items-center gap-1"
                    title={`Open publisher page: https://doi.org/${paper.doi}`}
                >
                    <ExternalLink className="w-3.5 h-3.5" />
                    DOI
                </button>
            </div>
        </div>
    );
}
