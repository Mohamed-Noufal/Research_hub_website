import { useState, useMemo, useEffect } from 'react';
import { Search, Filter, ArrowLeft, Sparkles, ChevronLeft, ChevronRight } from 'lucide-react';
import type { View, Paper } from '../App';
import { useSearch } from '../hooks/useSearch';
import { usersApi } from '../api/users';
import { papersApi } from '../api/papers';
import { FilterPanel } from './ui/FilterPanel';
import { PaperCard } from './ui/PaperCard';
import { SearchStats } from './ui/SearchStats';

interface SearchResultsProps {
  searchQuery: string;
  searchCategory?: string;
  onNavigate: (view: View) => void;
  onSavePaper: (paper: Paper) => void;
  isPaperSaved: (paperId: string) => boolean;
  cachedResults?: { query: string; category?: string; results: any } | null;
  onResultsLoaded?: (cache: { query: string; category?: string; results: any }) => void;
}

const SearchResults = ({
  searchQuery,
  searchCategory,
  onNavigate,
  onSavePaper,
  isPaperSaved,
  cachedResults,
  onResultsLoaded
}: SearchResultsProps) => {
  const [sortBy, setSortBy] = useState('relevance');
  const [yearRange, setYearRange] = useState([2000, 2025]);
  const [selectedSources, setSelectedSources] = useState({
    arxiv: true,
    'semantic-scholar': true,
    semantic_scholar: true,
    openalex: true,
    crossref: true,
    pubmed: true,
    europe_pmc: true,
    core: true,
    eric: true,
    biorxiv: true
  });
  const [minCitations, setMinCitations] = useState(0);
  const [showOnlyWithPDF, setShowOnlyWithPDF] = useState(false);
  const [showOnlyWithDOI, setShowOnlyWithDOI] = useState(false);
  const [showOnlyWithAbstract, setShowOnlyWithAbstract] = useState(false);
  const [showAllSources, setShowAllSources] = useState(false);
  const [showFilters, setShowFilters] = useState(true);
  const [expandedPaper, setExpandedPaper] = useState<string | null>(null);
  const [viewedPapers, setViewedPapers] = useState(new Set<string>());
  const [hideSeen, setHideSeen] = useState(false);
  const [currentPage, setCurrentPage] = useState(1);
  const pageSize = 20;

  // Check if we have cached results for this query
  const useCachedResults = cachedResults &&
    cachedResults.query === searchQuery &&
    cachedResults.category === searchCategory;

  // Fetch real data from backend API only if not using cache
  const { data: searchData, loading, error } = useSearch(
    searchQuery,
    searchCategory || 'ai_cs',
    !useCachedResults // Only search if we don't have cached results
  );

  // Use cached results if available, otherwise use fresh data
  const activeSearchData = useCachedResults ? cachedResults.results : searchData;

  // Cache the results when they're loaded
  useEffect(() => {
    if (searchData && !useCachedResults && onResultsLoaded) {
      onResultsLoaded({
        query: searchQuery,
        category: searchCategory,
        results: searchData
      });
    }
  }, [searchData, searchQuery, searchCategory, useCachedResults, onResultsLoaded]);

  // Convert backend papers to frontend Paper format
  const papers: Paper[] = useMemo(() => {
    if (!activeSearchData?.papers) return [];

    return activeSearchData.papers.map((p: any) => {
      let pdfUrl = p.pdf_url || p.pdfUrl || null;
      if (!pdfUrl && p.arxiv_id) {
        pdfUrl = `https://arxiv.org/pdf/${p.arxiv_id}.pdf`;
      }

      let paperUrl = p.url || null;
      if (!paperUrl && p.arxiv_id) {
        paperUrl = `https://arxiv.org/abs/${p.arxiv_id}`;
      } else if (!paperUrl && p.doi) {
        paperUrl = `https://doi.org/${p.doi}`;
      } else if (!paperUrl && pdfUrl) {
        paperUrl = pdfUrl;
      }

      return {
        id: p.id?.toString() || p.arxiv_id || p.doi || Math.random().toString(),
        title: p.title || 'Untitled',
        authors: Array.isArray(p.authors)
          ? p.authors.map((a: any) => typeof a === 'string' ? a : a.name)
          : [],
        abstract: p.abstract || '',
        year: p.publication_date ? new Date(p.publication_date).getFullYear() : 2024,
        citations: p.citation_count || 0,
        source: (p.source || 'arxiv') as Paper['source'],
        url: paperUrl || '#',
        pdfUrl: pdfUrl,
        doi: p.doi,
        venue: p.venue || p.source
      };
    });
  }, [activeSearchData]);

  const filteredPapers = useMemo(() => {
    return papers.filter(paper => {
      const sourceMatch = selectedSources[paper.source as keyof typeof selectedSources];
      const yearMatch = paper.year >= yearRange[0] && paper.year <= yearRange[1];
      const citationMatch = paper.citations >= minCitations;
      const pdfMatch = !showOnlyWithPDF || (paper.pdfUrl && paper.pdfUrl !== '#');
      const doiMatch = !showOnlyWithDOI || (paper.doi && paper.doi !== 'N/A');
      const abstractMatch = !showOnlyWithAbstract || (paper.abstract && paper.abstract.trim().length > 0);
      const seenMatch = !hideSeen || !viewedPapers.has(paper.id);

      return sourceMatch && yearMatch && citationMatch && pdfMatch && doiMatch && abstractMatch && seenMatch;
    }).sort((a, b) => {
      if (sortBy === 'year') return b.year - a.year;
      if (sortBy === 'citations') return b.citations - a.citations;
      return 0;
    });
  }, [papers, selectedSources, yearRange, minCitations, sortBy, showOnlyWithPDF, showOnlyWithDOI, showOnlyWithAbstract, hideSeen, viewedPapers]);

  // Reset to page 1 when filters change
  useEffect(() => {
    setCurrentPage(1);
  }, [filteredPapers.length, sortBy, hideSeen]);

  const paginatedPapers = useMemo(() => {
    const startIndex = (currentPage - 1) * pageSize;
    return filteredPapers.slice(startIndex, startIndex + pageSize);
  }, [filteredPapers, currentPage]);

  const totalPages = Math.ceil(filteredPapers.length / pageSize);

  const handlePageChange = (newPage: number) => {
    setCurrentPage(newPage);
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  // Auto-save search to history
  useEffect(() => {
    if (activeSearchData && activeSearchData.papers && activeSearchData.papers.length > 0) {
      papersApi.saveSearchHistory(
        searchQuery,
        searchCategory || 'ai_cs',
        activeSearchData.total || activeSearchData.papers.length
      ).catch(err => console.error('Failed to save search history:', err));
    }
  }, [activeSearchData, searchQuery, searchCategory]);

  const toggleSource = (source: string) => {
    setSelectedSources(prev => ({ ...prev, [source]: !prev[source as keyof typeof selectedSources] }));
  };

  const toggleSave = async (paperId: string) => {
    const paper = papers.find(p => p.id === paperId);
    if (paper) {
      try {
        if (isPaperSaved(paperId)) {
          await usersApi.unsavePaper(parseInt(paperId));
        } else {
          await usersApi.savePaper(parseInt(paperId));
        }
        onSavePaper(paper);
      } catch (error) {
        console.error('Failed to save/unsave paper:', error);
      }
    }
  };

  const markAsViewed = (paperId: string) => {
    setViewedPapers(prev => new Set(prev).add(paperId));
  };

  const categoryLabel = searchCategory ? {
    'ai-cs': 'AI & Computer Science',
    'medicine_biology': 'Medicine & Biology',
    'agriculture_animal': 'Agriculture & Animal Science',
    'humanities_social': 'Humanities & Social Sciences',
    'economics_business': 'Economics & Business'
  }[searchCategory] : null;

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-purple-50">
      {/* Compact Header */}
      <header className="sticky top-0 z-50 backdrop-blur-xl bg-white/80 border-b border-white/20 shadow-sm">
        <div className="max-w-7xl mx-auto px-6 py-3">
          <div className="flex items-center gap-3">
            <button
              className="p-2 hover:bg-white/60 rounded-lg transition-all hover:scale-105"
              onClick={() => onNavigate('search')}
            >
              <ArrowLeft className="w-5 h-5 text-gray-700" />
            </button>
            <div className="flex-1 max-w-3xl">
              <div className="relative backdrop-blur-md bg-white/90 rounded-xl border border-white/40 shadow-sm">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
                <input
                  type="text"
                  value={searchQuery}
                  readOnly
                  className="w-full pl-10 pr-3 py-2.5 text-sm bg-transparent text-gray-900 focus:outline-none rounded-xl"
                />
              </div>
            </div>
            <button
              onClick={() => onNavigate('workspace')}
              className="px-5 py-2.5 bg-gradient-to-r from-blue-600 to-purple-600 text-white text-sm font-medium rounded-lg hover:shadow-lg transition-all hover:scale-105"
            >
              Workspace
            </button>
            {categoryLabel && (
              <div className="flex items-center px-3 py-1 bg-blue-50 text-blue-700 rounded-full text-xs font-medium">
                {categoryLabel}
              </div>
            )}
          </div>
        </div>
      </header>

      <div className="flex max-w-7xl mx-auto">
        {/* Compact Filters Sidebar */}
        {showFilters && (
          <FilterPanel
            sortBy={sortBy}
            setSortBy={setSortBy}
            selectedSources={selectedSources}
            toggleSource={toggleSource}
            showAllSources={showAllSources}
            setShowAllSources={setShowAllSources}
            yearRange={yearRange}
            setYearRange={setYearRange}
            minCitations={minCitations}
            setMinCitations={setMinCitations}
            showOnlyWithPDF={showOnlyWithPDF}
            setShowOnlyWithPDF={setShowOnlyWithPDF}
            showOnlyWithDOI={showOnlyWithDOI}
            setShowOnlyWithDOI={setShowOnlyWithDOI}
            showOnlyWithAbstract={showOnlyWithAbstract}
            setShowOnlyWithAbstract={setShowOnlyWithAbstract}
            hideSeen={hideSeen}
            setHideSeen={setHideSeen}
            setShowFilters={setShowFilters}
          />
        )}

        {/* Results - Optimized for Scanning */}
        <main className="flex-1 p-6">
          {/* Results Header with Stats */}
          <SearchStats
            filteredCount={filteredPapers.length}
            searchQuery={searchQuery}
          />

          {/* Paper Cards - Advanced Design */}
          <div className="space-y-4">
            {/* Loading State */}
            {loading && (
              <div className="flex flex-col items-center justify-center py-20">
                <div className="relative">
                  <div className="w-16 h-16 border-4 border-blue-200 border-t-blue-600 rounded-full animate-spin"></div>
                  <Sparkles className="w-6 h-6 text-blue-600 absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2" />
                </div>
                <p className="mt-6 text-lg font-medium text-gray-700">Searching academic databases...</p>
                <p className="mt-2 text-sm text-gray-500">This usually takes 2-5 seconds</p>
              </div>
            )}

            {/* Error State */}
            {error && !loading && (
              <div className="flex flex-col items-center justify-center py-20">
                <div className="w-16 h-16 bg-red-100 rounded-full flex items-center justify-center mb-4">
                  <span className="text-3xl">⚠️</span>
                </div>
                <p className="text-lg font-medium text-gray-900">Search Failed</p>
                <p className="mt-2 text-sm text-gray-600">{error.message || 'An error occurred while searching'}</p>
                <button
                  onClick={() => window.location.reload()}
                  className="mt-4 px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
                >
                  Try Again
                </button>
              </div>
            )}

            {/* No Results State */}
            {!loading && !error && filteredPapers.length === 0 && papers.length === 0 && (
              <div className="flex flex-col items-center justify-center py-20">
                <div className="w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center mb-4">
                  <Search className="w-8 h-8 text-gray-400" />
                </div>
                <p className="text-lg font-medium text-gray-900">No papers found</p>
                <p className="mt-2 text-sm text-gray-600">Try adjusting your search query or filters</p>
              </div>
            )}

            {/* Results */}
            {!loading && !error && paginatedPapers.map((paper) => (
              <PaperCard
                key={paper.id}
                paper={paper}
                isViewed={viewedPapers.has(paper.id)}
                markAsViewed={markAsViewed}
                expandedPaper={expandedPaper}
                setExpandedPaper={setExpandedPaper}
                isPaperSaved={isPaperSaved}
                toggleSave={toggleSave}
                onNavigate={onNavigate}
              />
            ))}

            {/* Pagination Controls */}
            {!loading && !error && filteredPapers.length > 0 && (
              <div className="flex justify-center items-center gap-4 mt-8 pb-8">
                <button
                  onClick={() => handlePageChange(currentPage - 1)}
                  disabled={currentPage === 1}
                  className={`flex items-center gap-2 px-4 py-2 rounded-lg border transition-all ${currentPage === 1
                    ? 'bg-gray-100 text-gray-400 border-gray-200 cursor-not-allowed'
                    : 'bg-white text-gray-700 border-gray-300 hover:bg-blue-50 hover:border-blue-300 hover:text-blue-600 shadow-sm'
                    }`}
                >
                  <ChevronLeft className="w-4 h-4" />
                  Previous
                </button>

                <span className="text-sm font-medium text-gray-600">
                  Page {currentPage} of {totalPages || 1}
                </span>

                <button
                  onClick={() => handlePageChange(currentPage + 1)}
                  disabled={currentPage === totalPages}
                  className={`flex items-center gap-2 px-4 py-2 rounded-lg border transition-all ${currentPage === totalPages
                    ? 'bg-gray-100 text-gray-400 border-gray-200 cursor-not-allowed'
                    : 'bg-white text-gray-700 border-gray-300 hover:bg-blue-50 hover:border-blue-300 hover:text-blue-600 shadow-sm'
                    }`}
                >
                  Next
                  <ChevronRight className="w-4 h-4" />
                </button>
              </div>
            )}
          </div>
        </main>
      </div>

      {/* Floating Filter Toggle */}
      {!showFilters && (
        <button
          onClick={() => setShowFilters(true)}
          className="fixed left-6 top-24 p-3 bg-gradient-to-r from-blue-600 to-purple-600 text-white rounded-lg shadow-lg hover:shadow-xl transition-all hover:scale-105 z-40"
        >
          <Filter className="w-4 h-4" />
        </button>
      )}
    </div>
  );
};

export default SearchResults;