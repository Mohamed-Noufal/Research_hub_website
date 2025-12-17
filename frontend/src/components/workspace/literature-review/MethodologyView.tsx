import { useState } from 'react';
import { BookOpen, Star, ChevronDown, FlaskConical, Check, Loader2 } from 'lucide-react';
import { Badge } from '../../ui/badge';
import type { ResearchPaper } from './types';
import { useUpdateMethodology, useMethodologyData } from '../../../hooks/useMethodology';

interface EditableField {
    paperId: number;
    field: string;
}

export default function MethodologyView({ papers, projectId }: { papers: ResearchPaper[], projectId?: number }) {
    const [editingField, setEditingField] = useState<EditableField | null>(null);
    const [editValue, setEditValue] = useState('');
    const [savingField, setSavingField] = useState<EditableField | null>(null);
    const [savedField, setSavedField] = useState<EditableField | null>(null);

    const updateMethodology = useUpdateMethodology();
    const { data: methodologyData } = useMethodologyData(projectId ? String(projectId) : '');

    const handleFieldClick = (paperId: number, field: string, currentValue: string, e: React.MouseEvent) => {
        e.stopPropagation();
        setEditingField({ paperId, field });
        setEditValue(currentValue || '');
    };

    const handleSave = async (paperId: number, field: string) => {
        if (!projectId) return;

        setSavingField({ paperId, field });

        try {
            await updateMethodology.mutateAsync({
                projectId: String(projectId),
                paperId: String(paperId),
                data: {
                    [field]: editValue
                }
            });

            setSavedField({ paperId, field });
            setTimeout(() => setSavedField(null), 2000);
        } catch (error) {
            console.error('Failed to save:', error);
        } finally {
            setSavingField(null);
            setEditingField(null);
        }
    };

    const handleBlur = (paperId: number, field: string) => {
        handleSave(paperId, field);
    };

    const handleKeyDown = (e: React.KeyboardEvent, paperId: number, field: string) => {
        if (e.key === 'Enter' && e.ctrlKey) {
            handleSave(paperId, field);
        } else if (e.key === 'Escape') {
            setEditingField(null);
        }
    };

    const isEditing = (paperId: number, field: string) => {
        return editingField?.paperId === paperId && editingField?.field === field;
    };

    const isSaving = (paperId: number, field: string) => {
        return savingField?.paperId === paperId && savingField?.field === field;
    };

    const isSaved = (paperId: number, field: string) => {
        return savedField?.paperId === paperId && savedField?.field === field;
    };

    return (
        <div className="space-y-8 w-full">
            <div className="bg-gradient-to-r from-indigo-500 to-purple-600 rounded-2xl p-8 text-white shadow-lg">
                <h2 className="text-2xl font-bold mb-2">Methodology Explorer</h2>
                <p className="text-indigo-100 opacity-90">Deep dive into research approaches, their lineage, and what makes them unique.</p>
            </div>

            <div className="grid gap-6">
                {papers.map((paper) => {
                    // Find saved data for this paper
                    const savedData = methodologyData?.papers?.find(p => String(p.paper_id) === String(paper.id));

                    // Merge saved values with paper static checks (if needed) or just use saved || paper default
                    const displayValues = {
                        methodology_description: savedData?.methodology_description || paper.methodologyDescription,
                        methodology_context: savedData?.methodology_context || paper.methodologyContext,
                        approach_novelty: savedData?.approach_novelty || paper.approachNovelty,
                    };

                    return (
                        <div key={paper.id} className="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden hover:shadow-md transition-shadow">
                            <div className="border-b border-gray-100 bg-gray-50/50 p-4 flex justify-between items-start">
                                <div className="flex-1">
                                    <div className="flex items-center gap-2 mb-1">
                                        {/* Methodology Badge - Editable */}
                                        <div
                                            className="cursor-pointer"
                                            onClick={(e) => handleFieldClick(paper.id, 'methodology', paper.methodology, e)}
                                        >
                                            {isEditing(paper.id, 'methodology') ? (
                                                <input
                                                    type="text"
                                                    value={editValue}
                                                    onChange={(e) => setEditValue(e.target.value)}
                                                    onBlur={() => handleBlur(paper.id, 'methodology')}
                                                    onKeyDown={(e) => handleKeyDown(e, paper.id, 'methodology')}
                                                    className="px-2 py-1 border border-indigo-500 rounded focus:outline-none focus:ring-1 focus:ring-indigo-500 text-sm"
                                                    autoFocus
                                                />
                                            ) : (
                                                <div className="flex items-center gap-1">
                                                    <Badge variant="outline" className="bg-white text-indigo-600 border-indigo-200">
                                                        {paper.methodology}
                                                    </Badge>
                                                    {isSaving(paper.id, 'methodology') && <Loader2 className="w-3 h-3 animate-spin text-gray-400" />}
                                                    {isSaved(paper.id, 'methodology') && <Check className="w-3 h-3 text-green-500" />}
                                                </div>
                                            )}
                                        </div>

                                        <span className="text-gray-400 text-xs">•</span>

                                        {/* Methodology Type - Editable */}
                                        <div
                                            className="cursor-pointer"
                                            onClick={(e) => handleFieldClick(paper.id, 'methodology_type', paper.methodologyType, e)}
                                        >
                                            {isEditing(paper.id, 'methodology_type') ? (
                                                <input
                                                    type="text"
                                                    value={editValue}
                                                    onChange={(e) => setEditValue(e.target.value)}
                                                    onBlur={() => handleBlur(paper.id, 'methodology_type')}
                                                    onKeyDown={(e) => handleKeyDown(e, paper.id, 'methodology_type')}
                                                    className="px-2 py-1 border border-indigo-500 rounded focus:outline-none focus:ring-1 focus:ring-indigo-500 text-sm"
                                                    autoFocus
                                                />
                                            ) : (
                                                <div className="flex items-center gap-1">
                                                    <span className="text-sm font-medium text-gray-600">{paper.methodologyType}</span>
                                                    {isSaving(paper.id, 'methodology_type') && <Loader2 className="w-3 h-3 animate-spin text-gray-400" />}
                                                    {isSaved(paper.id, 'methodology_type') && <Check className="w-3 h-3 text-green-500" />}
                                                </div>
                                            )}
                                        </div>
                                    </div>
                                    <h3 className="text-lg font-bold text-gray-900">{paper.title}</h3>
                                </div>
                                <div className="text-right">
                                    <div className="text-xs font-medium text-gray-500 uppercase tracking-wider mb-1">Year</div>
                                    <div className="text-lg font-bold text-gray-900">{paper.year}</div>
                                </div>
                            </div>

                            <div className="grid md:grid-cols-3 divide-y md:divide-y-0 md:divide-x divide-gray-100">
                                {/* Column 1: The Approach - Editable */}
                                <div
                                    className="p-6 cursor-pointer"
                                    onClick={(e) => handleFieldClick(paper.id, 'methodology_description', displayValues.methodology_description, e)}
                                >
                                    <div className="flex items-center gap-2 mb-3 text-indigo-600">
                                        <div className="p-1.5 bg-indigo-50 rounded-lg">
                                            <FlaskConical className="w-4 h-4" />
                                        </div>
                                        <h4 className="font-semibold text-sm uppercase tracking-wide">The Approach</h4>
                                        {isSaving(paper.id, 'methodology_description') && <Loader2 className="w-3 h-3 animate-spin" />}
                                        {isSaved(paper.id, 'methodology_description') && <Check className="w-3 h-3 text-green-500" />}
                                    </div>
                                    {isEditing(paper.id, 'methodology_description') ? (
                                        <textarea
                                            value={editValue}
                                            onChange={(e) => setEditValue(e.target.value)}
                                            onBlur={() => handleBlur(paper.id, 'methodology_description')}
                                            onKeyDown={(e) => handleKeyDown(e, paper.id, 'methodology_description')}
                                            className="w-full px-2 py-1 border border-indigo-500 rounded focus:outline-none focus:ring-1 focus:ring-indigo-500 min-h-[100px] text-sm"
                                            autoFocus
                                            placeholder="Describe the research approach..."
                                        />
                                    ) : (
                                        <p className="text-sm text-gray-600 leading-relaxed">
                                            {displayValues.methodology_description}
                                        </p>
                                    )}
                                    <div className="mt-4 pt-4 border-t border-gray-100">
                                        <div className="text-xs font-medium text-gray-500 mb-1">Data Collection</div>
                                        <div className="text-sm text-gray-900">{paper.dataCollection}</div>
                                    </div>
                                </div>

                                {/* Column 2: Previous Context - Editable */}
                                <div
                                    className="p-6 bg-gray-50/30 cursor-pointer"
                                    onClick={(e) => handleFieldClick(paper.id, 'methodology_context', displayValues.methodology_context, e)}
                                >
                                    <div className="flex items-center gap-2 mb-3 text-gray-600">
                                        <div className="p-1.5 bg-gray-100 rounded-lg">
                                            <BookOpen className="w-4 h-4" />
                                        </div>
                                        <h4 className="font-semibold text-sm uppercase tracking-wide">Previous Context</h4>
                                        {isSaving(paper.id, 'methodology_context') && <Loader2 className="w-3 h-3 animate-spin" />}
                                        {isSaved(paper.id, 'methodology_context') && <Check className="w-3 h-3 text-green-500" />}
                                    </div>
                                    {isEditing(paper.id, 'methodology_context') ? (
                                        <textarea
                                            value={editValue}
                                            onChange={(e) => setEditValue(e.target.value)}
                                            onBlur={() => handleBlur(paper.id, 'methodology_context')}
                                            onKeyDown={(e) => handleKeyDown(e, paper.id, 'methodology_context')}
                                            className="w-full px-2 py-1 border border-indigo-500 rounded focus:outline-none focus:ring-1 focus:ring-indigo-500 min-h-[100px] text-sm"
                                            autoFocus
                                            placeholder="Describe the previous work and context..."
                                        />
                                    ) : (
                                        <p className="text-sm text-gray-600 leading-relaxed italic">
                                            "{displayValues.methodology_context}"
                                        </p>
                                    )}
                                    <div className="mt-4 flex items-center gap-2 text-xs text-gray-500">
                                        <ChevronDown className="w-3 h-3" />
                                        <span>Builds upon prior work</span>
                                    </div>
                                </div>

                                {/* Column 3: Novelty/Difference - Editable */}
                                <div
                                    className="p-6 bg-green-50/30 cursor-pointer"
                                    onClick={(e) => handleFieldClick(paper.id, 'approach_novelty', displayValues.approach_novelty, e)}
                                >
                                    <div className="flex items-center gap-2 mb-3 text-green-700">
                                        <div className="p-1.5 bg-green-100 rounded-lg">
                                            <Star className="w-4 h-4" />
                                        </div>
                                        <h4 className="font-semibold text-sm uppercase tracking-wide">Why It's Different</h4>
                                        {isSaving(paper.id, 'approach_novelty') && <Loader2 className="w-3 h-3 animate-spin" />}
                                        {isSaved(paper.id, 'approach_novelty') && <Check className="w-3 h-3 text-green-500" />}
                                    </div>
                                    {isEditing(paper.id, 'approach_novelty') ? (
                                        <textarea
                                            value={editValue}
                                            onChange={(e) => setEditValue(e.target.value)}
                                            onBlur={() => handleBlur(paper.id, 'approach_novelty')}
                                            onKeyDown={(e) => handleKeyDown(e, paper.id, 'approach_novelty')}
                                            className="w-full px-2 py-1 border border-indigo-500 rounded focus:outline-none focus:ring-1 focus:ring-indigo-500 min-h-[100px] text-sm"
                                            autoFocus
                                            placeholder="Describe what makes this approach novel..."
                                        />
                                    ) : (
                                        <p className="text-sm text-gray-700 leading-relaxed font-medium">
                                            {displayValues.approach_novelty}
                                        </p>
                                    )}
                                    <div className="mt-4">
                                        <Badge className="bg-green-100 text-green-800 hover:bg-green-200 border-0">
                                            Novel Contribution
                                        </Badge>
                                    </div>
                                </div>
                            </div>
                        </div>
                    );
                })}
            </div>
        </div>
    );
}
