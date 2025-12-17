import { useState } from 'react';
import SearchPage from './components/SearchPage';
import SearchResults from './components/SearchResults';
import Workspace from './components/Workspace';
import Blog from './components/Blog';
import { useUser } from './hooks/useUser';

export type View = 'search' | 'results' | 'workspace' | 'blog';

export interface Paper {
  id: string;
  title: string;
  authors: string[];
  abstract: string;
  year: number;
  citations: number;
  source: 'arxiv' | 'semantic-scholar' | 'openalex';
  url: string;
  pdfUrl?: string;
  doi?: string;
  venue?: string;
  saved?: boolean;
  openAccess?: boolean;
}

function App() {
  // Initialize user session
  useUser();

  const [currentView, setCurrentView] = useState<View>('search');
  const [searchQuery, setSearchQuery] = useState('');
  const [searchCategory, setSearchCategory] = useState<string | undefined>();
  const [savedPapers, setSavedPapers] = useState<Paper[]>([]);

  // Cache search results to avoid re-searching when navigating back
  const [cachedSearchResults, setCachedSearchResults] = useState<{
    query: string;
    category?: string;
    results: any;
  } | null>(null);

  const handleSearch = (query: string, category?: string) => {
    setSearchQuery(query);
    setSearchCategory(category);
    // Clear cached results when doing a new search
    setCachedSearchResults(null);
    setCurrentView('results');
  };

  const handleSavePaper = (paper: Paper) => {
    setSavedPapers(prev => {
      const exists = prev.find(p => p.id === paper.id);
      if (exists) {
        return prev.filter(p => p.id !== paper.id);
      }
      return [...prev, paper];
    });
  };

  const isPaperSaved = (paperId: string) => {
    return savedPapers.some(p => p.id === paperId);
  };

  return (
    <div className="min-h-screen bg-white">
      {currentView === 'search' && (
        <SearchPage onSearch={handleSearch} onNavigate={setCurrentView} />
      )}
      {currentView === 'results' && (
        <SearchResults
          searchQuery={searchQuery}
          searchCategory={searchCategory}
          onNavigate={setCurrentView}
          onSavePaper={handleSavePaper}
          isPaperSaved={isPaperSaved}
          cachedResults={cachedSearchResults}
          onResultsLoaded={setCachedSearchResults}
        />
      )}
      {currentView === 'workspace' && (
        <Workspace
          savedPapers={savedPapers}
          onNavigate={setCurrentView}
          onSavePaper={handleSavePaper}
          onSearch={handleSearch}
        />
      )}
      {currentView === 'blog' && (
        <Blog onNavigate={setCurrentView} />
      )}
    </div>
  );
}

export default App;
