
import { useState, useEffect } from 'react';
import { X, Check, Search } from 'lucide-react';
import { Button } from "../ui/button";
import { Input } from "../ui/input";
import { Badge } from "../ui/badge";
import type { Paper } from '../../App';

interface PaperPickerProps {
    papers: Paper[];
    selectedIds: string[];
    onSelectionChange: (ids: string[]) => void;
    open: boolean;
    onOpenChange: (open: boolean) => void;
    limit?: number;
}

export default function PaperPicker({
    papers,
    selectedIds,
    onSelectionChange,
    open,
    onOpenChange,
    limit = 7
}: PaperPickerProps) {
    const [searchQuery, setSearchQuery] = useState('');

    // Local state for the modal selection - apply only on "Save"
    const [tempSelected, setTempSelected] = useState<string[]>(selectedIds);

    // Reset on open
    useEffect(() => {
        if (open) {
            setTempSelected(selectedIds);
            setSearchQuery('');
        }
    }, [open, selectedIds]);

    const filteredPapers = papers.filter(p =>
        p.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
        p.abstract?.toLowerCase().includes(searchQuery.toLowerCase())
    );

    const toggleSelection = (id: string) => {
        if (tempSelected.includes(id)) {
            setTempSelected(prev => prev.filter(i => i !== id));
        } else {
            if (tempSelected.length >= limit) return; // Enforce limit
            setTempSelected(prev => [...prev, id]);
        }
    };

    const handleSave = () => {
        onSelectionChange(tempSelected);
        onOpenChange(false);
    };

    if (!open) return null;

    return (
        <div className="absolute inset-0 z-50 flex flex-col bg-white">
            {/* Header */}
            <div className="flex items-center justify-between px-4 py-3 border-b border-gray-100">
                <div className="flex flex-col">
                    <span className="font-semibold text-gray-900">Select Papers</span>
                    <span className="text-xs text-gray-500">Pick up to {limit} papers for context</span>
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
                {filteredPapers.length === 0 ? (
                    <div className="h-full flex flex-col items-center justify-center text-gray-400 gap-2">
                        <FileSearchIcon className="w-8 h-8 opacity-20" />
                        <span className="text-sm">No papers found</span>
                    </div>
                ) : (
                    filteredPapers.map(paper => {
                        const isSelected = tempSelected.includes(paper.id);
                        const isDisabled = !isSelected && tempSelected.length >= limit;

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
                                    <h4 className={`text-sm font-medium truncate pr-4 ${isSelected ? 'text-blue-900' : 'text-gray-900'}`} title={paper.title}>
                                        {paper.title}
                                    </h4>
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

            {/* Footer */}
            <div className="p-4 border-t border-gray-100 bg-gray-50/50">
                <div className="flex gap-2">
                    <Button variant="outline" className="flex-1" onClick={() => onOpenChange(false)}>Cancel</Button>
                    <Button className="flex-1 bg-gray-900 text-white hover:bg-gray-800" onClick={handleSave} disabled={tempSelected.length === 0}>
                        Confirm
                    </Button>
                </div>
            </div>
        </div>
    );
}

function FileSearchIcon(props: any) {
    return (
        <svg {...props} xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M14.5 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7.5L14.5 2z" /><polyline points="14 2 14 8 20 8" /><circle cx="10" cy="13" r="2" /><path d="m20 17-5.4-5.4" /></svg>
    )
}
