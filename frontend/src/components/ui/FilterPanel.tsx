import React from 'react';
import { Filter, ChevronDown, Sparkles, Calendar, TrendingUp } from 'lucide-react';

interface FilterPanelProps {
    sortBy: string;
    setSortBy: (value: string) => void;
    selectedSources: Record<string, boolean>;
    toggleSource: (source: string) => void;
    showAllSources: boolean;
    setShowAllSources: (value: boolean) => void;
    yearRange: number[];
    setYearRange: (range: number[]) => void;
    minCitations: number;
    setMinCitations: (value: number) => void;
    showOnlyWithPDF: boolean;
    setShowOnlyWithPDF: (value: boolean) => void;
    showOnlyWithDOI: boolean;
    setShowOnlyWithDOI: (value: boolean) => void;
    showOnlyWithAbstract: boolean;
    setShowOnlyWithAbstract: (value: boolean) => void;
    hideSeen: boolean;
    setHideSeen: (value: boolean) => void;
    setShowFilters: (value: boolean) => void;
}

export const FilterPanel: React.FC<FilterPanelProps> = ({
    sortBy,
    setSortBy,
    selectedSources,
    toggleSource,
    showAllSources,
    setShowAllSources,
    yearRange,
    setYearRange,
    minCitations,
    setMinCitations,
    showOnlyWithPDF,
    setShowOnlyWithPDF,
    showOnlyWithDOI,
    setShowOnlyWithDOI,
    showOnlyWithAbstract,
    setShowOnlyWithAbstract,
    hideSeen,
    setHideSeen,
    setShowFilters,
}) => {
    return (
        <aside className="w-64 p-4">
            <div className="sticky top-20 backdrop-blur-xl bg-white/70 rounded-xl border border-white/30 shadow-lg p-4">
                <div className="flex items-center justify-between mb-4">
                    <div className="flex items-center gap-2">
                        <Filter className="w-4 h-4 text-blue-600" />
                        <h3 className="text-sm font-semibold text-gray-900">Filters</h3>
                    </div>
                    <button onClick={() => setShowFilters(false)} className="p-1 hover:bg-gray-100 rounded-md">
                        <ChevronDown className="w-4 h-4 text-gray-500" />
                    </button>
                </div>

                {/* Quick Sort */}
                <div className="mb-4">
                    <label className="text-xs font-medium text-gray-600 mb-2 block">Sort</label>
                    <div className="space-y-1">
                        {[
                            { value: 'relevance', label: 'Relevance', icon: Sparkles },
                            { value: 'year', label: 'Recent', icon: Calendar },
                            { value: 'citations', label: 'Cited', icon: TrendingUp }
                        ].map((opt) => (
                            <button
                                key={opt.value}
                                onClick={() => setSortBy(opt.value)}
                                className={`w-full flex items-center gap-2 px-3 py-2 rounded-lg text-xs font-medium transition-all ${sortBy === opt.value
                                    ? 'bg-gradient-to-r from-blue-600 to-purple-600 text-white shadow-md'
                                    : 'bg-white/60 hover:bg-white text-gray-700'
                                    }`}
                            >
                                <opt.icon className="w-3.5 h-3.5" />
                                {opt.label}
                            </button>
                        ))}
                    </div>
                </div>

                {/* Source Checkboxes - Show 2 by default */}
                <div className="mb-4">
                    <label className="text-xs font-medium text-gray-600 mb-2 block">Sources</label>
                    <div className="space-y-1.5">
                        {[
                            { key: 'arxiv', label: 'arXiv' },
                            { key: 'crossref', label: 'Crossref' },
                            { key: 'semantic-scholar', label: 'Semantic Scholar' },
                            { key: 'semantic_scholar', label: 'Semantic Scholar (alt)' },
                            { key: 'openalex', label: 'OpenAlex' },
                            { key: 'pubmed', label: 'PubMed' },
                            { key: 'europe_pmc', label: 'Europe PMC' },
                            { key: 'biorxiv', label: 'bioRxiv' },
                            { key: 'core', label: 'CORE' },
                            { key: 'eric', label: 'ERIC' }
                        ].slice(0, showAllSources ? undefined : 2).map((src) => (
                            <label key={src.key} className="flex items-center gap-2 p-2 rounded-md hover:bg-white/50 cursor-pointer">
                                <input
                                    type="checkbox"
                                    checked={selectedSources[src.key as keyof typeof selectedSources]}
                                    onChange={() => toggleSource(src.key as keyof typeof selectedSources)}
                                    className="w-4 h-4 rounded border-gray-300"
                                />
                                <span className="text-xs text-gray-700">{src.label}</span>
                            </label>
                        ))}
                        <button
                            onClick={() => setShowAllSources(!showAllSources)}
                            className="text-xs text-blue-600 hover:text-blue-700 font-medium mt-1"
                        >
                            {showAllSources ? 'Show less' : 'Show all sources (8 more)'}
                        </button>
                    </div>
                </div>

                {/* Compact Sliders */}
                <div className="space-y-3">
                    <div>
                        <label className="text-xs font-medium text-gray-600 mb-1 block">
                            Year: {yearRange[0]}-{yearRange[1]}
                        </label>
                        <input
                            type="range"
                            min="2015"
                            max="2025"
                            value={yearRange[0]}
                            onChange={(e) => setYearRange([parseInt(e.target.value), yearRange[1]])}
                            className="w-full h-1.5 bg-gradient-to-r from-blue-200 to-purple-200 rounded-full"
                        />
                    </div>
                    <div>
                        <label className="text-xs font-medium text-gray-600 mb-1 block">
                            Min Citations: {minCitations}
                        </label>
                        <input
                            type="range"
                            min="0"
                            max="100"
                            step="10"
                            value={minCitations}
                            onChange={(e) => setMinCitations(parseInt(e.target.value))}
                            className="w-full h-1.5 bg-gradient-to-r from-blue-200 to-purple-200 rounded-full"
                        />
                    </div>
                </div>

                {/* PDF and DOI Filters */}
                <div>
                    <label className="text-xs font-medium text-gray-600 mb-2 block">
                        Availability
                    </label>
                    <div className="space-y-1.5">
                        <label className="flex items-center gap-2 p-2 rounded-md hover:bg-white/50 cursor-pointer">
                            <input
                                type="checkbox"
                                checked={showOnlyWithPDF}
                                onChange={(e) => setShowOnlyWithPDF(e.target.checked)}
                                className="w-4 h-4 rounded border-gray-300"
                            />
                            <span className="text-xs text-gray-700">PDF Available</span>
                        </label>
                        <label className="flex items-center gap-2 p-2 rounded-md hover:bg-white/50 cursor-pointer">
                            <input
                                type="checkbox"
                                checked={showOnlyWithDOI}
                                onChange={(e) => setShowOnlyWithDOI(e.target.checked)}
                                className="w-4 h-4 rounded border-gray-300"
                            />
                            <span className="text-xs text-gray-700">DOI Available</span>
                        </label>
                        <label className="flex items-center gap-2 p-2 rounded-md hover:bg-white/50 cursor-pointer">
                            <input
                                type="checkbox"
                                checked={showOnlyWithAbstract}
                                onChange={(e) => setShowOnlyWithAbstract(e.target.checked)}
                                className="w-4 h-4 rounded border-gray-300"
                            />
                            <span className="text-xs text-gray-700">Abstract Available</span>
                        </label>

                        <div className="pt-2 border-t border-gray-100 mt-2">
                            <label className="flex items-center gap-2 text-sm text-gray-700 font-medium cursor-pointer">
                                <div className="relative inline-flex items-center cursor-pointer">
                                    <input
                                        type="checkbox"
                                        checked={hideSeen}
                                        onChange={(e) => setHideSeen(e.target.checked)}
                                        className="sr-only peer"
                                    />
                                    <div className="w-9 h-5 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-4 after:w-4 after:transition-all peer-checked:bg-blue-600"></div>
                                </div>
                                Hide Seen Papers
                            </label>
                        </div>
                    </div>
                </div>
            </div>
        </aside>
    );
};
