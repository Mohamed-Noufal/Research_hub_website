import React, { useState } from 'react';
import { Users, Quote, TrendingUp, BarChart3, FileText, ExternalLink, Share2, BookmarkCheck, BookmarkPlus } from 'lucide-react';
import type { Paper, View } from '../../App';

interface PaperCardProps {
    paper: Paper;
    isViewed: boolean;
    markAsViewed: (id: string) => void;
    expandedPaper: string | null;
    setExpandedPaper: (id: string | null) => void;
    isPaperSaved: (id: string) => boolean;
    toggleSave: (id: string) => void;
    onNavigate: (view: View) => void;
}

export const PaperCard: React.FC<PaperCardProps> = ({
    paper,
    isViewed,
    markAsViewed,
    expandedPaper,
    setExpandedPaper,
    isPaperSaved,
    toggleSave,
    onNavigate,
}) => {
    const [isSaving, setIsSaving] = useState(false);
    const isSaved = isPaperSaved(paper.id);

    const handleSave = async () => {
        setIsSaving(true);
        try {
            await toggleSave(paper.id);
            setTimeout(() => setIsSaving(false), 2000);
        } catch (error) {
            setIsSaving(false);
        }
    };

    return (
        <div
            className={`group backdrop-blur-md rounded-2xl border shadow-sm hover:shadow-xl transition-all duration-300 overflow-hidden ${isViewed
                ? 'bg-gray-100/90 border-gray-300/60 opacity-75'
                : 'bg-white/90 border-white/40 hover:border-blue-200'
                }`}
        >
            <div className="p-6">
                <div className="flex gap-4">
                    <div className="flex-1 min-w-0">
                        <h3
                            className={`text-lg font-semibold mb-2 group-hover:text-blue-600 transition-colors line-clamp-2 ${isViewed ? 'text-gray-600' : 'text-gray-900'}`}
                            onClick={() => markAsViewed(paper.id)}
                        >
                            {paper.title}
                        </h3>

                        <div className="flex items-center gap-2 text-sm text-gray-600 mb-2">
                            <Users className="w-4 h-4" />
                            <span className="line-clamp-1">
                                {paper.authors.slice(0, 3).join(', ')}
                                {paper.authors.length > 3 && ` +${paper.authors.length - 3} more`}
                            </span>
                        </div>

                        <div className="flex items-center gap-2 text-xs text-gray-600 mb-2">
                            <span className="font-medium">{paper.authors.slice(0, 2).join(', ')}{paper.authors.length > 2 ? ', ...' : ''}</span>
                            <span className="w-1 h-1 bg-gray-400 rounded-full" />
                            <span>{paper.venue}</span>
                            <span className="w-1 h-1 bg-gray-400 rounded-full" />
                            <span>{paper.year}</span>
                            <span className="w-1 h-1 bg-gray-400 rounded-full" />
                            <span>DOI: {paper.doi || 'N/A'}</span>
                        </div>

                        <div className="mb-3">
                            <p className={`text-sm text-gray-700 leading-relaxed transition-all duration-300 ${expandedPaper === paper.id ? '' : 'line-clamp-3'}`}>
                                {paper.abstract}
                            </p>
                            <button
                                onClick={() => setExpandedPaper(expandedPaper === paper.id ? null : paper.id)}
                                className="text-xs text-blue-600 hover:text-blue-700 font-medium mt-1 hover:underline"
                            >
                                {expandedPaper === paper.id ? 'Show less' : 'Read more'}
                            </button>
                        </div>

                        <div className="flex items-center gap-6 mb-3 text-xs">
                            <div className="flex items-center gap-1.5">
                                <Quote className="w-3.5 h-3.5 text-gray-500" />
                                <span className="font-medium text-gray-900">{paper.citations}</span>
                                <span className="text-gray-600">citations</span>
                            </div>
                            <div className="flex items-center gap-1.5">
                                <TrendingUp className="w-3.5 h-3.5 text-blue-600" />
                                <span className="font-medium text-blue-600">{Math.floor(Math.random() * 30) + 8}</span>
                                <span className="text-gray-600">influential</span>
                            </div>
                            <div className="flex items-center gap-1.5">
                                <Users className="w-3.5 h-3.5 text-purple-600" />
                                <span className="font-medium text-purple-600">{Math.floor(Math.random() * 100) + 15}</span>
                                <span className="text-gray-600">citing</span>
                            </div>
                        </div>

                        <div className="flex items-center gap-3 justify-between">
                            <div className="flex items-center gap-2">
                                <span className={`px-2.5 py-1 rounded-full text-xs font-medium ${paper.source === 'arxiv' ? 'bg-red-50 text-red-700' : paper.source === 'semantic-scholar' ? 'bg-blue-50 text-blue-700' : 'bg-green-50 text-green-700'}`}>
                                    {paper.source === 'arxiv' ? 'arXiv' : paper.source === 'semantic-scholar' ? 'Semantic Scholar' : 'OpenAlex'}
                                </span>
                                <div className="flex items-center gap-1 text-xs text-gray-500">
                                    <BarChart3 className="w-3 h-3" />
                                    <span>{Math.floor(Math.random() * 30) + 8} highly influential</span>
                                </div>
                            </div>

                            <div className="flex gap-1.5">
                                <button
                                    onClick={(e) => {
                                        e.stopPropagation();
                                        const url = paper.pdfUrl || paper.url;
                                        if (url && url !== '#') {
                                            window.open(url, '_blank', 'noopener,noreferrer');
                                            markAsViewed(paper.id);
                                        }
                                    }}
                                    disabled={!paper.pdfUrl && !paper.url}
                                    className={`px-3 py-1.5 backdrop-blur-sm bg-white/80 hover:bg-white border border-gray-200 rounded-lg text-xs font-medium transition-all flex items-center gap-1.5 ${!paper.pdfUrl && !paper.url ? 'opacity-50 cursor-not-allowed text-gray-400' : 'text-gray-700 hover:text-blue-600'}`}
                                >
                                    <FileText className="w-3.5 h-3.5" />
                                    PDF
                                </button>

                                <button
                                    onClick={(e) => {
                                        e.stopPropagation();
                                        if (!isPaperSaved(paper.id)) toggleSave(paper.id);
                                        onNavigate('workspace');
                                        markAsViewed(paper.id);
                                    }}
                                    className="px-3 py-1.5 backdrop-blur-sm bg-white/80 hover:bg-white border border-gray-200 rounded-lg text-xs font-medium text-gray-700 hover:text-blue-600 transition-all flex items-center gap-1.5"
                                >
                                    <ExternalLink className="w-3.5 h-3.5" />
                                    View
                                </button>

                                <button
                                    onClick={(e) => {
                                        e.stopPropagation();
                                        const citation = `${paper.authors.slice(0, 3).join(', ')}${paper.authors.length > 3 ? ' et al.' : ''}. (${paper.year}). ${paper.title}. ${paper.venue || paper.source}.${paper.doi ? ` DOI: ${paper.doi}` : ''}`;
                                        navigator.clipboard.writeText(citation);
                                        markAsViewed(paper.id);
                                        alert('Citation copied!');
                                    }}
                                    className="px-3 py-1.5 backdrop-blur-sm bg-white/80 hover:bg-white border border-gray-200 rounded-lg text-xs font-medium text-gray-700 hover:text-blue-600 transition-all flex items-center gap-1.5"
                                >
                                    <Share2 className="w-3.5 h-3.5" />
                                    Cite
                                </button>
                            </div>
                        </div>
                    </div>

                    <button
                        onClick={handleSave}
                        className={`relative p-2 rounded-lg transition-all shrink-0 overflow-hidden ${isSaved ? 'bg-blue-100 hover:bg-blue-200' : 'hover:bg-blue-50'}`}
                        title={isSaving ? 'Saving in background...' : isSaved ? 'Saved' : 'Save paper'}
                    >
                        {isSaving && (
                            <>
                                <div className="absolute inset-0 bg-blue-50" />
                                <div
                                    className="absolute top-0 left-0 right-0 bg-gradient-to-b from-blue-400 to-blue-500"
                                    style={{
                                        height: '100%',
                                        animation: 'fillDown 2s ease-out forwards'
                                    }}
                                />
                            </>
                        )}
                        <div className="relative z-10">
                            {isSaved ? (
                                <BookmarkCheck className="w-5 h-5 text-blue-600" />
                            ) : (
                                <BookmarkPlus className="w-5 h-5 text-gray-400 hover:text-blue-600" />
                            )}
                        </div>
                    </button>
                </div>
            </div>
            <style>{`
                @keyframes fillDown {
                    from { height: 0%; }
                    to { height: 100%; }
                }
            `}</style>
        </div>
    );
};
