import React, { useState, useEffect } from 'react';
import { Search, BookOpen, Sparkles, Loader2, FileText, Users, ArrowRight, ChevronDown, Wand2, X, Lightbulb } from 'lucide-react';
import type { View } from '../App';

const ResearchHub = ({ onSearch, onNavigate }: { onSearch: (query: string, category?: string) => void; onNavigate: (view: View) => void }) => {
  const [activeCategory, setActiveCategory] = useState('AI & CS');
  const [query, setQuery] = useState('');
  const [isSearching, setIsSearching] = useState(false);
  const [scrollY, setScrollY] = useState(0);

  // AI Suggestion state
  const [showAIModal, setShowAIModal] = useState(false);
  const [problemStatement, setProblemStatement] = useState('');
  const [researchGoals, setResearchGoals] = useState('');
  const [aiSuggestions, setAISuggestions] = useState<any[]>([]);
  const [isLoadingSuggestions, setIsLoadingSuggestions] = useState(false);

  useEffect(() => {
    const handleScroll = () => setScrollY(window.scrollY);
    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  const categories = [
    'AI & CS',
    'Medicine & Biology',
    'Agriculture & Animal Science',
    'Humanities & Social Sciences',
    'Economics & Business'
  ];

  const stats = [
    { count: '2M+', label: 'arXiv Papers', gradient: 'from-blue-400 to-blue-600' },
    { count: '200M+', label: 'Semantic Scholar', gradient: 'from-purple-400 to-purple-600' },
    { count: '250M+', label: 'OpenAlex', gradient: 'from-green-400 to-green-600' }
  ];

  const categoryMap: Record<string, string> = {
    'AI & CS': 'ai_cs',
    'Medicine & Biology': 'medicine_biology',
    'Agriculture & Animal Science': 'agriculture_animal',
    'Humanities & Social Sciences': 'humanities_social',
    'Economics & Business': 'economics_business'
  };

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    if (query.trim()) {
      setIsSearching(true);
      // Call parent's onSearch which will trigger the API call
      onSearch(query, categoryMap[activeCategory] || 'ai_cs');
      // Reset searching state after a short delay for UX
      setTimeout(() => setIsSearching(false), 500);
    }
  };

  const handleGetAISuggestions = async () => {
    if (!problemStatement.trim()) return;

    setIsLoadingSuggestions(true);
    try {
      const response = await fetch(`http://localhost:8000/api/v1/papers/ai-suggestions?problem_statement=${encodeURIComponent(problemStatement)}&goals=${encodeURIComponent(researchGoals)}&category=${categoryMap[activeCategory]}`, {
        method: 'POST'
      });

      if (response.ok) {
        const data = await response.json();
        setAISuggestions(data.suggestions || []);
      }
    } catch (error) {
      console.error('Failed to get AI suggestions:', error);
    } finally {
      setIsLoadingSuggestions(false);
    }
  };

  const handleUseSuggestion = (suggestion: any) => {
    setQuery(suggestion.query);
    setShowAIModal(false);
    // Optionally trigger search immediately
    // onSearch(suggestion.query, categoryMap[activeCategory] || 'ai_cs');
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-purple-50">
      {/* Header with Glassmorphism */}
      <header className="sticky top-0 z-50 backdrop-blur-xl bg-white/70 border-b border-white/20 shadow-sm">
        <div className="max-w-7xl mx-auto px-8 py-4">
          <div className="flex items-center">
            {/* Logo - Far Left */}
            <div className="flex items-center gap-2 group cursor-pointer">
              <div className="relative">
                <BookOpen className="w-6 h-6 text-blue-600 transition-transform group-hover:rotate-12 duration-300" />
                <div className="absolute inset-0 bg-blue-400 blur-xl opacity-0 group-hover:opacity-50 transition-opacity duration-300" />
              </div>
              <span className="text-lg font-semibold bg-gradient-to-r from-gray-900 to-gray-700 bg-clip-text text-transparent">
                ResearchHub
              </span>
            </div>

            {/* Navigation - Centered with flex-1 */}
            <nav className="flex-1 flex justify-center">
              <div className="flex items-center gap-8">
                {['Features', 'Pricing', 'Blog', 'About', 'Contact'].map((item) => (
                  <a
                    key={item}
                    href="#"
                    className="text-sm text-gray-700 hover:text-blue-600 transition-colors relative group"
                  >
                    {item}
                    <span className="absolute -bottom-1 left-0 w-0 h-0.5 bg-gradient-to-r from-blue-500 to-purple-500 group-hover:w-full transition-all duration-300" />
                  </a>
                ))}
              </div>
            </nav>

            {/* Auth Buttons - Far Right */}
            <div className="flex items-center gap-4">
              <button
                onClick={() => onNavigate('workspace')}
                className="text-sm text-gray-700 hover:text-gray-900 transition-colors"
              >
                Sign In
              </button>
              <button
                onClick={() => onNavigate('workspace')}
                className="px-6 py-2.5 bg-gradient-to-r from-blue-600 to-purple-600 text-white text-sm font-medium rounded-xl hover:shadow-lg hover:shadow-blue-500/50 transition-all duration-300 hover:scale-105"
              >
                My Workspace
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-6xl mx-auto px-8">
        {/* Hero Section with Animated Gradient */}
        <div className="text-center pt-24 pb-12 relative">
          {/* Floating Background Elements */}
          <div className="absolute top-20 left-10 w-72 h-72 bg-gradient-to-br from-blue-400/30 to-purple-400/30 rounded-full blur-3xl animate-pulse" />
          <div className="absolute top-40 right-10 w-96 h-96 bg-gradient-to-br from-purple-400/20 to-pink-400/20 rounded-full blur-3xl animate-pulse delay-1000" />

          <div className="relative z-10">
            {/* Title with Icon - Animated */}
            <div className="flex items-center justify-center gap-4 mb-6">
              <div className="relative">
                <Sparkles
                  className="w-12 h-12 text-blue-600 animate-pulse"
                  style={{ transform: `translateY(${scrollY * 0.05}px)` }}
                />
                <div className="absolute inset-0 bg-blue-500 blur-2xl opacity-40" />
              </div>
              <h1 className="text-7xl font-bold bg-gradient-to-r from-gray-900 via-blue-900 to-purple-900 bg-clip-text text-transparent tracking-tight">
                ResearchHub
              </h1>
            </div>

            {/* Subtitle with Gradient */}
            <p className="text-xl text-gray-700 mb-8 max-w-3xl mx-auto font-light leading-relaxed">
              Search millions of academic papers from arXiv, Semantic Scholar, and OpenAlex
            </p>

            {/* Feature Badges */}
            <div className="flex items-center justify-center gap-3 mb-1">
              {[
                { icon: Sparkles, text: 'AI-Powered' },
                { icon: FileText, text: '250M+ Papers' },
                { icon: Users, text: 'Trusted by Researchers' }
              ].map((badge, idx) => (
                <div
                  key={idx}
                  className="flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-gray-200 hover:bg-gray-300 transition-colors duration-200 cursor-pointer"
                >
                  <badge.icon className="w-3.5 h-3 text-gray-700" />
                  <span className="text-xs text-gray-800 font-medium">{badge.text}</span>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Category Pills with Modern Design */}
        <div className="flex items-center justify-center gap-3 mb-12 flex-wrap">
          {categories.map((category) => (
            <button
              key={category}
              onClick={() => setActiveCategory(category)}
              disabled={isSearching}
              className={`px-6 py-3 rounded-full text-sm font-medium transition-all duration-300 ${activeCategory === category
                ? 'bg-gradient-to-r from-blue-600 to-purple-600 text-white shadow-lg shadow-blue-500/50 scale-105'
                : 'bg-white/80 backdrop-blur-sm text-gray-700 hover:bg-white hover:shadow-md border border-gray-200'
                } disabled:opacity-50 disabled:cursor-not-allowed`}
            >
              {category}
            </button>
          ))}
        </div>

        {/* Search Bar with Glassmorphism */}
        {/* Search Bar with Ultra-Modern Design */}
        {/* Search Bar with Clean Modern Design */}
        <form onSubmit={handleSearch} className="max-w-3xl mx-auto mb-20 relative group z-20">
          {/* Soft Shadow/Glow - Much subtler and static */}
          <div className="absolute -inset-0.5 bg-gradient-to-r from-blue-200 via-purple-200 to-blue-200 rounded-[2.5rem] opacity-30 blur-lg transition-all duration-500" />

          {/* Main Card */}
          <div className="relative bg-white/80 backdrop-blur-3xl rounded-[2.5rem] border border-white/60 shadow-xl overflow-hidden transition-all duration-300 hover:shadow-2xl hover:bg-white/90">

            {/* Input Area */}
            <div
              className="flex gap-4 px-8 pt-8 pb-4 cursor-text"
              onClick={() => document.getElementById('search-query')?.focus()}
            >
              <Search className="w-6 h-6 text-gray-400 mt-1.5 shrink-0" />
              <textarea
                id="search-query"
                name="query"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    handleSearch(e as any);
                  }
                }}
                placeholder="What are you looking for? (e.g., 'Impact of AI on healthcare')"
                disabled={isSearching}
                rows={2}
                className="flex-1 bg-transparent text-xl text-gray-900 placeholder-gray-400 focus:outline-none resize-none leading-relaxed font-medium font-sans tracking-tight"
                aria-label="Search for research papers"
              />
            </div>

            {/* Footer / Actions */}
            <div className="flex items-center justify-between px-6 pb-6 pt-2">
              {/* Left: Keyboard Hints */}
              <div className="hidden sm:flex items-center gap-4 pl-14 text-xs font-medium text-gray-400 select-none opacity-0 group-hover:opacity-100 transition-opacity duration-300">
                <span className="flex items-center gap-2">
                  <kbd className="px-2 py-1 rounded-md bg-gray-100 border border-gray-200 text-gray-500 font-sans text-[11px] min-w-[20px] text-center">↵</kbd>
                  <span>search</span>
                </span>
                <span className="flex items-center gap-2">
                  <kbd className="px-2 py-1 rounded-md bg-gray-100 border border-gray-200 text-gray-500 font-sans text-[11px]">Shift ↵</kbd>
                  <span>new line</span>
                </span>
              </div>

              {/* Right: Actions */}
              <div className="flex items-center gap-3 ml-auto">
                <button
                  type="button"
                  onClick={(e) => {
                    e.stopPropagation();
                    setShowAIModal(true);
                  }}
                  className="p-3 rounded-xl text-purple-600 hover:bg-purple-50 transition-all duration-200 hover:scale-105 active:scale-95 relative group"
                >
                  <Wand2 className="w-5 h-5" />
                  {/* Custom Tooltip */}
                  <div className="absolute right-full top-1/2 -translate-y-1/2 mr-3 px-3 py-1.5 bg-white/90 backdrop-blur-sm text-purple-700 text-xs font-medium rounded-xl shadow-lg border border-purple-100 opacity-0 group-hover:opacity-100 transition-all duration-200 translate-x-2 group-hover:translate-x-0 pointer-events-none whitespace-nowrap z-50">
                    AI Search Suggestion
                    <div className="absolute top-1/2 -right-1 -translate-y-1/2 w-2 h-2 bg-white rotate-45 border-t border-r border-purple-100"></div>
                  </div>
                </button>

                <button
                  type="submit"
                  disabled={isSearching || !query.trim()}
                  className="px-6 py-3 bg-blue-600 hover:bg-blue-700 text-white text-sm font-semibold rounded-xl transition-all duration-200 hover:shadow-lg hover:shadow-blue-500/20 active:scale-95 flex items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  <span>Search Papers</span>
                  <ArrowRight className="w-4 h-4" />
                </button>
              </div>
            </div>
          </div>
        </form>

        {/* Search Animation */}
        {isSearching && (
          <div className="flex items-center justify-center gap-4 mb-8">
            <div className="flex gap-2">
              <div className="w-3 h-3 bg-blue-600 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
              <div className="w-3 h-3 bg-blue-600 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
              <div className="w-3 h-3 bg-blue-600 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
            </div>
            <span className="text-gray-600">Searching across databases...</span>
          </div>
        )}

        {/* Stats Cards with Modern Gradient Design */}
        <div className="grid grid-cols-3 gap-8 mb-24">
          {stats.map((stat, idx) => (
            <div
              key={idx}
              className="relative group cursor-pointer"
              style={{ animationDelay: `${idx * 100}ms` }}
            >
              {/* Gradient Background with Glassmorphism */}
              <div className={`absolute inset-0 bg-gradient-to-br ${stat.gradient} rounded-3xl opacity-10 group-hover:opacity-20 transition-opacity duration-300`} />
              <div className="relative backdrop-blur-sm bg-white/70 rounded-3xl border border-white/40 p-12 text-center transition-all duration-300 group-hover:scale-105 group-hover:shadow-2xl">
                {/* Animated Number */}
                <div className={`text-6xl font-light bg-gradient-to-br ${stat.gradient} bg-clip-text text-transparent mb-4 tracking-tight`}>
                  {stat.count}
                </div>
                <div className="text-base text-gray-700 font-normal">
                  {stat.label}
                </div>
                {/* Hover Effect Line */}
                <div className={`mt-6 h-1 w-0 bg-gradient-to-r ${stat.gradient} rounded-full mx-auto group-hover:w-full transition-all duration-500`} />
              </div>
            </div>
          ))}
        </div>

        {/* Scroll Indicator */}
        <div className="flex justify-center pb-12">
          <div className="animate-bounce">
            <ChevronDown className="w-6 h-6 text-gray-400" />
          </div>
        </div>
      </main>

      {/* AI Suggestion Modal */}
      {showAIModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm animate-fadeIn">
          <div className="relative w-full max-w-3xl bg-white rounded-3xl shadow-2xl animate-slideUp">
            {/* Modal Header */}
            <div className="flex items-center justify-between p-6 border-b border-gray-200">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-gradient-to-r from-purple-500 to-pink-500 rounded-xl">
                  <Wand2 className="w-6 h-6 text-white" />
                </div>
                <div>
                  <h2 className="text-2xl font-bold text-gray-900">AI Search Suggestion</h2>
                  <p className="text-sm text-gray-600">Describe your research to get smart query suggestions</p>
                </div>
              </div>
              <button
                onClick={() => {
                  setShowAIModal(false);
                  setAISuggestions([]);
                  setProblemStatement('');
                  setResearchGoals('');
                }}
                className="p-2 hover:bg-gray-100 rounded-xl transition-colors"
              >
                <X className="w-6 h-6 text-gray-500" />
              </button>
            </div>

            {/* Modal Body */}
            <div className="p-6 max-h-[70vh] overflow-y-auto">
              {/* Input Form */}
              <div className="space-y-4 mb-6">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Research Problem / Topic <span className="text-red-500">*</span>
                  </label>
                  <textarea
                    id="problem-statement"
                    name="problemStatement"
                    value={problemStatement}
                    onChange={(e) => setProblemStatement(e.target.value)}
                    placeholder="Describe your research problem, topic, or area of interest in detail. For example: 'I'm studying the impact of climate change on agricultural productivity in sub-Saharan Africa...'"
                    className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-purple-500 focus:border-transparent resize-none"
                    rows={4}
                    aria-label="Research problem description"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Research Goals (Optional)
                  </label>
                  <textarea
                    id="research-goals"
                    name="researchGoals"
                    value={researchGoals}
                    onChange={(e) => setResearchGoals(e.target.value)}
                    placeholder="What are you trying to achieve? What specific aspects are you interested in? For example: 'Find recent studies on climate adaptation strategies, focus on empirical data...'"
                    className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-purple-500 focus:border-transparent resize-none"
                    rows={3}
                    aria-label="Research goals (optional)"
                  />
                </div>

                <button
                  onClick={handleGetAISuggestions}
                  disabled={!problemStatement.trim() || isLoadingSuggestions}
                  className="w-full px-6 py-3 bg-gradient-to-r from-purple-600 to-pink-600 text-white font-medium rounded-xl hover:shadow-lg hover:shadow-purple-500/50 transition-all duration-300 hover:scale-105 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
                >
                  {isLoadingSuggestions ? (
                    <>
                      <Loader2 className="w-5 h-5 animate-spin" />
                      <span>Generating Suggestions...</span>
                    </>
                  ) : (
                    <>
                      <Lightbulb className="w-5 h-5" />
                      <span>Get AI Suggestions</span>
                    </>
                  )}
                </button>
              </div>

              {/* Suggestions Display */}
              {aiSuggestions.length > 0 && (
                <div className="space-y-3">
                  <h3 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
                    <Sparkles className="w-5 h-5 text-purple-600" />
                    Suggested Search Queries
                  </h3>
                  {aiSuggestions.map((suggestion, idx) => (
                    <div
                      key={idx}
                      className="p-4 border border-gray-200 rounded-xl hover:border-purple-500 hover:shadow-md transition-all duration-300 cursor-pointer group"
                      onClick={() => handleUseSuggestion(suggestion)}
                    >
                      <div className="flex items-start justify-between gap-4">
                        <div className="flex-1">
                          <div className="flex items-center gap-2 mb-2">
                            <Search className="w-4 h-4 text-purple-600" />
                            <p className="font-medium text-gray-900 group-hover:text-purple-600 transition-colors">
                              {suggestion.query}
                            </p>
                          </div>
                          {suggestion.reasoning && (
                            <p className="text-sm text-gray-600">{suggestion.reasoning}</p>
                          )}
                        </div>
                        {suggestion.relevance_score && (
                          <div className="flex-shrink-0">
                            <div className="px-3 py-1 bg-purple-100 text-purple-700 text-xs font-medium rounded-full">
                              {Math.round(suggestion.relevance_score * 100)}% match
                            </div>
                          </div>
                        )}
                      </div>
                    </div>
                  ))}
                  <p className="text-sm text-gray-500 text-center mt-4">
                    Click any suggestion to use it in your search
                  </p>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default ResearchHub;
