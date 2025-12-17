import { useState, useMemo } from 'react';
import { Search, Check, Calendar, Plus } from 'lucide-react';
import { Button } from '../../ui/button';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '../../ui/dialog';
import { useSavedPapers } from '../../../hooks/useLiteratureReviews';

interface PaperSelectorProps {
    isOpen: boolean;
    onClose: () => void;
    onSelect: (paperIds: number[]) => void;
    selectedIds?: number[];
    title?: string;
}

export default function PaperSelector({
    isOpen,
    onClose,
    onSelect,
    selectedIds = [],
    title = "Select Papers"
}: PaperSelectorProps) {
    const { data: papers = [], isLoading } = useSavedPapers();
    const [searchTerm, setSearchTerm] = useState('');
    const [currentSelection, setCurrentSelection] = useState<number[]>([]);

    // Reset selection when opened
    // Note: We might want to pre-select items if needed, but usually we add *new* items.
    // If we pass in selectedIds, we might want to disable them or show them as already selected.

    const filteredPapers = useMemo(() => {
        if (!searchTerm) return papers;
        const lower = searchTerm.toLowerCase();
        return papers.filter((p: any) =>
            p.title.toLowerCase().includes(lower) ||
            (p.authors && p.authors.join(', ').toLowerCase().includes(lower))
        );
    }, [papers, searchTerm]);

    const handleToggle = (id: number) => {
        setCurrentSelection(prev =>
            prev.includes(id)
                ? prev.filter(pid => pid !== id)
                : [...prev, id]
        );
    };

    const handleConfirm = () => {
        onSelect(currentSelection);
        setCurrentSelection([]);
        onClose();
    };

    const isSelected = (id: number) => currentSelection.includes(id);
    const isAlreadyInProject = (id: number) => selectedIds.includes(id);

    return (
        <Dialog open={isOpen} onOpenChange={onClose}>
            <DialogContent className="max-w-3xl max-h-[80vh] flex flex-col p-0 gap-0">
                <DialogHeader className="p-6 pb-4 border-b border-gray-100">
                    <DialogTitle className="text-xl font-bold flex items-center justify-between">
                        {title}
                        <span className="text-sm font-normal text-gray-500">
                            {currentSelection.length} selected
                        </span>
                    </DialogTitle>

                    <div className="relative mt-4">
                        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
                        <input
                            type="text"
                            placeholder="Search your library..."
                            value={searchTerm}
                            onChange={(e) => setSearchTerm(e.target.value)}
                            className="w-full pl-9 pr-4 py-2 bg-gray-50 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 transition-all"
                        />
                    </div>
                </DialogHeader>

                <div className="flex-1 overflow-y-auto p-2">
                    {isLoading ? (
                        <div className="flex items-center justify-center py-12">
                            <div className="w-6 h-6 border-2 border-indigo-600 border-t-transparent rounded-full animate-spin" />
                        </div>
                    ) : filteredPapers.length === 0 ? (
                        <div className="text-center py-12 text-gray-500">
                            <p>No papers found matching "{searchTerm}"</p>
                        </div>
                    ) : (
                        <div className="space-y-1">
                            {filteredPapers.map((paper: any) => {
                                const alreadyAdded = isAlreadyInProject(paper.id);
                                const selected = isSelected(paper.id);

                                return (
                                    <div
                                        key={paper.id}
                                        onClick={() => !alreadyAdded && handleToggle(paper.id)}
                                        className={`
                      relative flex items-start gap-4 p-4 rounded-xl cursor-pointer transition-all border
                      ${alreadyAdded
                                                ? 'opacity-60 bg-gray-50 border-transparent cursor-not-allowed'
                                                : selected
                                                    ? 'bg-indigo-50 border-indigo-200 shadow-sm'
                                                    : 'bg-white border-transparent hover:bg-gray-50'
                                            }
                    `}
                                    >
                                        {/* Checkbox */}
                                        <div className={`
                      mt-1 w-5 h-5 rounded border flex items-center justify-center transition-colors
                      ${alreadyAdded
                                                ? 'bg-gray-200 border-gray-300 text-gray-500'
                                                : selected
                                                    ? 'bg-indigo-600 border-indigo-600 text-white'
                                                    : 'border-gray-300 bg-white text-transparent hover:border-indigo-400'
                                            }
                    `}>
                                            <Check className="w-3.5 h-3.5" />
                                        </div>

                                        <div className="flex-1 min-w-0">
                                            <h4 className={`text-sm font-semibold mb-1 ${alreadyAdded ? 'text-gray-500' : 'text-gray-900'}`}>
                                                {paper.title}
                                            </h4>
                                            <div className="flex items-center gap-3 text-xs text-gray-500">
                                                <span className="truncate max-w-[200px]">
                                                    {paper.authors ? paper.authors.join(', ') : 'Unknown Authors'}
                                                </span>
                                                <span className="flex items-center gap-1">
                                                    <Calendar className="w-3 h-3" />
                                                    {paper.year}
                                                </span>
                                                {alreadyAdded && (
                                                    <span className="text-emerald-600 font-medium bg-emerald-50 px-2 py-0.5 rounded">
                                                        Already in project
                                                    </span>
                                                )}
                                            </div>
                                        </div>
                                    </div>
                                );
                            })}
                        </div>
                    )}
                </div>

                <div className="p-4 border-t border-gray-100 flex items-center justify-end gap-3 bg-gray-50/50">
                    <Button variant="ghost" onClick={onClose}>
                        Cancel
                    </Button>
                    <Button
                        onClick={handleConfirm}
                        disabled={currentSelection.length === 0}
                        className="bg-indigo-600 hover:bg-indigo-700"
                    >
                        <Plus className="w-4 h-4 mr-2" />
                        Add {currentSelection.length > 0 ? `${currentSelection.length} Papers` : 'Papers'}
                    </Button>
                </div>
            </DialogContent>
        </Dialog>
    );
}
