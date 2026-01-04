
import { useState, useEffect } from 'react';
import { X, Check, Search, FileCheck2, FileWarning } from 'lucide-react';
import { Button } from "../ui/button";
import { Input } from "../ui/input";
import { Badge } from "../ui/badge";
import type { Paper } from '../../App';
import apiService from '../../services/api';

// Icon component for empty state
const FileSearchIcon = ({ className }: { className?: string }) => (
    <svg className={className} fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
    </svg>
);

interface PaperPickerProps {
    papers: Paper[];  // Deprecated - component fetches directly
    selectedIds: string[];
    onSelectionChange: (ids: string[]) => void;
    open: boolean;
    onOpenChange: (open: boolean) => void;
    limit?: number;
}

export default function PaperPicker({
    selectedIds,
    onSelectionChange,
    open,
    onOpenChange,
    limit = 7
}: PaperPickerProps) {
    const [searchQuery, setSearchQuery] = useState('');
    const [savedPapers, setSavedPapers] = useState<Paper[]>([]);
    const [isLoading, setIsLoading] = useState(false);
    const [tempSelected, setTempSelected] = useState<string[]>(selectedIds);

    // Fetch saved papers when picker opens
    useEffect(() => {
        if (open) {
            setTempSelected(selectedIds);
            setSearchQuery('');
            fetchSavedPapers();
        }
    }, [open, selectedIds]);

    const fetchSavedPapers = async () => {
        try {
            setIsLoading(true);
            const data = await apiService.getSavedPapers();

            // Transform API papers to match App Paper interface
            const transformedPapers: Paper[] = (data.papers || []).map((p: any) => ({
                id: p.id?.toString() || '',
                title: p.title || '',
                authors: p.authors || [],
                abstract: p.abstract || '',
                year: p.publication_date ? new Date(p.publication_date).getFullYear() : 0,
                citations: p.citation_count || 0,
                source: (p.source?.toLowerCase().replace(/[_\s]/g, '-') || 'arxiv') as 'arxiv' | 'semantic-scholar' | 'openalex',
                url: p.pdf_url || '',
                pdfUrl: p.pdf_url,
                doi: p.doi,
                venue: p.venue,
                saved: true,
                openAccess: !!p.pdf_url
            }));

            setSavedPapers(transformedPapers);
        } catch (error) {
            console.error('Failed to fetch saved papers:', error);
        } finally {
            setIsLoading(false);
        }
    };

    const filteredPapers = savedPapers.filter(p =>
        p.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
        p.abstract?.toLowerCase().includes(searchQuery.toLowerCase())
    );

    const toggleSelection = (id: string) => {
        if (tempSelected.includes(id)) {
            setTempSelected(prev => prev.filter(i => i !== id));
        } else {
            if (tempSelected.length >= limit) return;
            setTempSelected(prev => [...prev, id]);
        }
    };

    const handleSave = () => {
        onSelectionChange(tempSelected);
        onOpenChange(false);
    };

    const papersWithPdf = filteredPapers.filter(p => p.pdfUrl && p.pdfUrl.trim() !== '').length;
    const papersWithoutPdf = filteredPapers.length - papersWithPdf;

    if (!open) return null;

    return (
        <div className="absolute inset-0 z-50 flex flex-col bg-white">
            {/* Header */}
            <div className="flex items-center justify-between px-4 py-3 border-b border-gray-100">
                <div className="flex flex-col">
                    <span className="font-semibold text-gray-900">📚 Knowledge Base</span>
                    <span className="text-xs text-gray-500">Select up to {limit} saved papers with PDFs</span>
                </div>
                <div className="flex items-center gap-2">
                    <Badge variant={tempSelected.length >= limit ? "destructive" : "secondary"}>
                        {tempSelected.length} / {limit}
                    </Badge>
                    <Button variant="ghost" size="icon" className="h-8 w-8 text-gray-400 hover:text-gray-900" onClick={() => onOpenChange(false)}>
                        <X className="w-4 h-4" />
                    </Button>
                </div>
            </div>

            {/* PDF Status Info */}
            {filteredPapers.length > 0 && (
                <div className="px-4 py-2 bg-blue-50 border-b border-blue-100">
                    <div className="flex items-center gap-4 text-xs">
                        <div className="flex items-center gap-1.5 text-green-700">
                            <FileCheck2 className="w-3.5 h-3.5" />
                            <span className="font-medium">{papersWithPdf} with PDF</span>
                        </div>
                        {papersWithoutPdf > 0 && (
                            <div className="flex items-center gap-1.5 text-amber-700">
                                <FileWarning className="w-3.5 h-3.5" />
                                <span className="font-medium">{papersWithoutPdf} need PDF download</span>
                            </div>
                        )}
                    </div>
                </div>
            )}

            {/* Search */}
            <div className="px-4 py-3">
                <div className="relative">
                    <Search className="absolute left-2.5 top-2.5 w-4 h-4 text-gray-400" />
                    <Input
                        placeholder="Search papers..."
                        value={searchQuery}
                        onChange={(e) => setSearchQuery(e.target.value)}
                        className="pl-9 bg-gray-50 border-gray-200"
                    />
                </div>
            </div>

            {/* List */}
            <div className="flex-1 overflow-y-auto px-4 pb-4 space-y-1">
                {isLoading ? (
                    <div className="h-full flex items-center justify-center">
                        <span className="text-sm text-gray-400">Loading your saved papers...</span>
                    </div>
                ) : filteredPapers.length === 0 ? (
                    <div className="h-full flex flex-col items-center justify-center text-gray-400 gap-2">
                        <FileSearchIcon className="w-8 h-8 opacity-20" />
                        <span className="text-sm">No saved papers found</span>
                        <span className="text-xs text-gray-400">Save papers from search to use them here</span>
                    </div>
                ) : (
                    filteredPapers.map(paper => {
                        const isSelected = tempSelected.includes(paper.id);
                        const isDisabled = !isSelected && tempSelected.length >= limit;
                        const hasPdf = paper.pdfUrl && paper.pdfUrl.trim() !== '';

                        return (
                            <div
                                key={paper.id}
                                onClick={() => !isDisabled && toggleSelection(paper.id)}
                                className={`p-3 rounded-lg flex items-start gap-3 cursor-pointer transition-colors border ${isSelected ? 'bg-blue-50/50 border-blue-100' : 'bg-white border-transparent hover:bg-gray-50'} ${isDisabled ? 'opacity-50 cursor-not-allowed' : ''}`}
                            >
                                <div className={`mt-0.5 w-4 h-4 rounded border flex items-center justify-center shrink-0 transition-colors ${isSelected ? 'bg-blue-600 border-blue-600 text-white' : 'border-gray-300 bg-white'}`}>
                                    {isSelected && <Check className="w-3 h-3" />}
                                </div>

                                <div className="flex-1 min-w-0">
                                    <div className="flex items-start gap-2">
                                        <h4 className={`text-sm font-medium flex-1 pr-2 ${isSelected ? 'text-blue-900' : 'text-gray-900'}`} title={paper.title}>
                                            {paper.title}
                                        </h4>
                                        {hasPdf ? (
                                            <FileCheck2 className="w-4 h-4 text-green-600 shrink-0 mt-0.5" title="PDF available" />
                                        ) : (
                                            <FileWarning className="w-4 h-4 text-amber-600 shrink-0 mt-0.5" title="No PDF - download in Paper Viewer" />
                                        )}
                                    </div>
                                    <div className="flex items-center gap-2 mt-0.5 text-xs text-gray-500">
                                        <span className="truncate max-w-[200px]">{paper.authors[0] || 'Unknown Author'}</span>
                                        {paper.year && <span>• {paper.year}</span>}
                                    </div>
                                </div>
                            </div>
                        );
                    })
                )}
            </div>

            {/* Tip + Actions */}
            <div className="p-4 border-t border-gray-100 space-y-3">
                <div className="text-xs text-gray-600flex items-start gap-1.5">
                    <span className="text-amber-600">💡</span>
                    <span><strong>Tip:</strong> Papers with PDFs provide better AI context</span>
                </div>
                <div className="flex gap-2">
                    <Button variant="outline" className="flex-1" onClick={() => onOpenChange(false)}>
                        Cancel
                    </Button>
                    <Button
                        className="flex-1 bg-blue-600 hover:bg-blue-700"
                        onClick={handleSave}
                        disabled={tempSelected.length === 0}
                    >
                        Save Selection
                    </Button>
                </div>
            </div>
        </div>
    );
}
