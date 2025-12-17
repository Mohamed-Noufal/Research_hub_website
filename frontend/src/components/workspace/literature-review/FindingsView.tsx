import { useState } from 'react';
import { Plus, AlertCircle, Check, Loader2, Trash2, X } from 'lucide-react';
import { Button } from '../../ui/button';
import { Badge } from '../../ui/badge';
import type { ResearchPaper } from './types';
import { useGaps, useCreateGap, useUpdateGap, useDeleteGap, useUpdateFinding, useFindings } from '../../../hooks/useFindings';

interface EditableField {
    id: string;
    field: string;
}

export default function FindingsView({ papers, projectId }: { papers: ResearchPaper[], projectId?: number }) {
    const [editingField, setEditingField] = useState<EditableField | null>(null);
    const [editValue, setEditValue] = useState('');
    const [savingField, setSavingField] = useState<EditableField | null>(null);
    const [savedField, setSavedField] = useState<EditableField | null>(null);
    const [showAddGap, setShowAddGap] = useState(false);
    const [newGapDesc, setNewGapDesc] = useState('');
    const [newGapPriority, setNewGapPriority] = useState<'High' | 'Medium' | 'Low'>('Medium');

    const { data: gapsData } = useGaps(projectId ? String(projectId) : '');
    const { data: findingsData } = useFindings(projectId ? String(projectId) : '');
    const createGap = useCreateGap();
    const updateGap = useUpdateGap();
    const deleteGap = useDeleteGap();
    const updateFinding = useUpdateFinding();

    const gaps = gapsData?.gaps || [];

    const handleFieldClick = (id: string, field: string, currentValue: string, e: React.MouseEvent) => {
        e.stopPropagation();
        setEditingField({ id, field });
        setEditValue(currentValue || '');
    };

    const handleSave = async (id: string, field: string) => {
        if (!projectId) return;

        setSavingField({ id, field });

        try {
            if (field === 'gap_description' || field === 'gap_priority') {
                // Update gap
                const updateData = field === 'gap_description'
                    ? { description: editValue }
                    : { priority: editValue };

                await updateGap.mutateAsync({
                    projectId: String(projectId),
                    gapId: id,
                    gap: updateData
                });
            } else {
                // Update finding
                await updateFinding.mutateAsync({
                    projectId: String(projectId),
                    paperId: id,
                    finding: {
                        [field]: editValue
                    }
                });
            }

            setSavedField({ id, field });
            setTimeout(() => setSavedField(null), 2000);
        } catch (error) {
            console.error('Failed to save:', error);
        } finally {
            setSavingField(null);
            setEditingField(null);
        }
    };

    const handleBlur = (id: string, field: string) => {
        handleSave(id, field);
    };

    const handleKeyDown = (e: React.KeyboardEvent, id: string, field: string) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            handleSave(id, field);
        } else if (e.key === 'Escape') {
            setEditingField(null);
        }
    };

    const handleAddGap = async () => {
        if (!projectId || !newGapDesc.trim()) return;

        try {
            await createGap.mutateAsync({
                projectId: String(projectId),
                gap: {
                    description: newGapDesc,
                    priority: newGapPriority
                }
            });
            setNewGapDesc('');
            setNewGapPriority('Medium');
            setShowAddGap(false);
        } catch (error) {
            console.error('Failed to create gap:', error);
        }
    };

    const handleDeleteGap = async (gapId: string) => {
        if (!projectId) return;
        try {
            await deleteGap.mutateAsync({ projectId: String(projectId), gapId });
        } catch (error) {
            console.error('Failed to delete gap:', error);
        }
    };

    const isEditing = (id: string, field: string) => {
        return editingField?.id === id && editingField?.field === field;
    };

    const isSaving = (id: string, field: string) => {
        return savingField?.id === id && savingField?.field === field;
    };

    const isSaved = (id: string, field: string) => {
        return savedField?.id === id && savedField?.field === field;
    };

    const getPriorityColor = (priority: string) => {
        switch (priority) {
            case 'High': return 'text-red-500 bg-red-50 border-red-200';
            case 'Medium': return 'text-yellow-500 bg-yellow-50 border-yellow-200';
            case 'Low': return 'text-blue-500 bg-blue-50 border-blue-200';
            default: return 'text-gray-500 bg-gray-50 border-gray-200';
        }
    };

    return (
        <div className="space-y-6">
            {/* Research Gaps Section */}
            <div className="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden">
                <div className="p-6 border-b border-gray-200 flex justify-between items-center">
                    <div>
                        <h3 className="text-lg font-semibold text-gray-900">Identified Research Gaps</h3>
                        <p className="text-sm text-gray-500">Areas requiring further investigation based on current literature</p>
                    </div>
                    <Button size="sm" variant="outline" onClick={() => setShowAddGap(true)}>
                        <Plus className="w-4 h-4 mr-2" />
                        Add Gap
                    </Button>
                </div>

                {/* Add Gap Form */}
                {showAddGap && (
                    <div className="p-6 border-b border-gray-200 bg-gray-50">
                        <div className="space-y-3">
                            <textarea
                                value={newGapDesc}
                                onChange={(e) => setNewGapDesc(e.target.value)}
                                placeholder="Describe the research gap..."
                                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500 min-h-[80px]"
                                autoFocus
                            />
                            <div className="flex items-center gap-3">
                                <select
                                    value={newGapPriority}
                                    onChange={(e) => setNewGapPriority(e.target.value as 'High' | 'Medium' | 'Low')}
                                    className="px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
                                >
                                    <option value="High">High Priority</option>
                                    <option value="Medium">Medium Priority</option>
                                    <option value="Low">Low Priority</option>
                                </select>
                                <Button size="sm" onClick={handleAddGap} disabled={!newGapDesc.trim()}>
                                    Add
                                </Button>
                                <Button size="sm" variant="ghost" onClick={() => { setShowAddGap(false); setNewGapDesc(''); }}>
                                    <X className="w-4 h-4" />
                                </Button>
                            </div>
                        </div>
                    </div>
                )}

                <div className="divide-y divide-gray-100">
                    {gaps.map((gap) => (
                        <div key={gap.id} className="p-6 hover:bg-gray-50 transition-colors group">
                            <div className="flex items-start justify-between">
                                <div className="flex items-start gap-3 flex-1">
                                    <AlertCircle className={`w-5 h-5 mt-0.5 ${gap.priority === 'High' ? 'text-red-500' :
                                        gap.priority === 'Medium' ? 'text-yellow-500' : 'text-blue-500'
                                        }`} />
                                    <div className="flex-1">
                                        {/* Gap Description - Editable */}
                                        <div
                                            className="cursor-pointer"
                                            onClick={(e) => handleFieldClick(gap.id, 'gap_description', gap.description, e)}
                                        >
                                            {isEditing(gap.id, 'gap_description') ? (
                                                <textarea
                                                    value={editValue}
                                                    onChange={(e) => setEditValue(e.target.value)}
                                                    onBlur={() => handleBlur(gap.id, 'gap_description')}
                                                    onKeyDown={(e) => handleKeyDown(e, gap.id, 'gap_description')}
                                                    className="w-full px-2 py-1 border border-indigo-500 rounded focus:outline-none focus:ring-1 focus:ring-indigo-500 min-h-[60px]"
                                                    autoFocus
                                                />
                                            ) : (
                                                <div className="flex items-start gap-2">
                                                    <p className="text-gray-900 font-medium flex-1">{gap.description}</p>
                                                    {isSaving(gap.id, 'gap_description') && <Loader2 className="w-4 h-4 animate-spin text-gray-400 mt-1" />}
                                                    {isSaved(gap.id, 'gap_description') && <Check className="w-4 h-4 text-green-500 mt-1" />}
                                                </div>
                                            )}
                                        </div>

                                        {/* Priority Badge - Editable */}
                                        <div className="flex items-center gap-2 mt-2">
                                            <div
                                                className="cursor-pointer"
                                                onClick={(e) => handleFieldClick(gap.id, 'gap_priority', gap.priority, e)}
                                            >
                                                {isEditing(gap.id, 'gap_priority') ? (
                                                    <select
                                                        value={editValue}
                                                        onChange={(e) => setEditValue(e.target.value)}
                                                        onBlur={() => handleBlur(gap.id, 'gap_priority')}
                                                        className="px-2 py-1 border border-indigo-500 rounded focus:outline-none focus:ring-1 focus:ring-indigo-500 text-sm"
                                                        autoFocus
                                                    >
                                                        <option value="High">High Priority</option>
                                                        <option value="Medium">Medium Priority</option>
                                                        <option value="Low">Low Priority</option>
                                                    </select>
                                                ) : (
                                                    <div className="flex items-center gap-1">
                                                        <Badge variant="outline" className={getPriorityColor(gap.priority)}>
                                                            {gap.priority} Priority
                                                        </Badge>
                                                        {isSaving(gap.id, 'gap_priority') && <Loader2 className="w-3 h-3 animate-spin text-gray-400" />}
                                                        {isSaved(gap.id, 'gap_priority') && <Check className="w-3 h-3 text-green-500" />}
                                                    </div>
                                                )}
                                            </div>
                                            <span className="text-xs text-gray-500">Supported by {gap.related_paper_ids.length} papers</span>
                                        </div>
                                    </div>
                                </div>
                                <Button
                                    variant="ghost"
                                    size="sm"
                                    className="opacity-0 group-hover:opacity-100 transition-opacity"
                                    onClick={() => handleDeleteGap(gap.id)}
                                >
                                    <Trash2 className="w-4 h-4 text-red-500" />
                                </Button>
                            </div>
                        </div>
                    ))}
                </div>
            </div>

            {/* Key Findings Matrix */}
            <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">Evidence Matrix</h3>
                <div className="space-y-4">
                    {papers.map(paper => {
                        // Find saved finding data
                        const savedFinding = findingsData?.findings?.find(f => String(f.paper_id) === String(paper.id));

                        const displayValues = {
                            key_finding: savedFinding?.key_finding || paper.keyFindings,
                            limitations: savedFinding?.limitations || paper.limitations
                        };

                        return (
                            <div key={paper.id} className="p-4 border border-gray-200 rounded-lg">
                                <div className="flex items-center justify-between mb-2">
                                    <h4 className="font-medium text-gray-900">{paper.title}</h4>
                                    <Badge variant="secondary">{paper.methodology}</Badge>
                                </div>
                                <div className="flex gap-4">
                                    {/* Key Finding - Editable */}
                                    <div
                                        className="flex-1 cursor-pointer"
                                        onClick={(e) => handleFieldClick(String(paper.id), 'key_finding', displayValues.key_finding, e)}
                                    >

                                        <div className="text-xs font-semibold text-gray-500 uppercase mb-1">Key Finding</div>
                                        {isEditing(String(paper.id), 'key_finding') ? (
                                            <textarea
                                                value={editValue}
                                                onChange={(e) => setEditValue(e.target.value)}
                                                onBlur={() => handleBlur(String(paper.id), 'key_finding')}
                                                onKeyDown={(e) => handleKeyDown(e, String(paper.id), 'key_finding')}
                                                className="w-full px-2 py-1 border border-indigo-500 rounded focus:outline-none focus:ring-1 focus:ring-indigo-500 min-h-[60px] text-sm"
                                                autoFocus
                                            />
                                        ) : (
                                            <div className="flex items-start gap-2">
                                                <p className="text-sm text-gray-700 flex-1">{displayValues.key_finding}</p>
                                                {isSaving(String(paper.id), 'key_finding') && <Loader2 className="w-3 h-3 animate-spin text-gray-400 mt-1" />}
                                                {isSaved(String(paper.id), 'key_finding') && <Check className="w-3 h-3 text-green-500 mt-1" />}
                                            </div>
                                        )}
                                    </div>

                                    {/* Limitations - Editable */}
                                    <div
                                        className="flex-1 border-l border-gray-100 pl-4 cursor-pointer"
                                        onClick={(e) => handleFieldClick(String(paper.id), 'limitations', displayValues.limitations, e)}
                                    >

                                        <div className="text-xs font-semibold text-gray-500 uppercase mb-1">Limitations</div>
                                        {isEditing(String(paper.id), 'limitations') ? (
                                            <textarea
                                                value={editValue}
                                                onChange={(e) => setEditValue(e.target.value)}
                                                onBlur={() => handleBlur(String(paper.id), 'limitations')}
                                                onKeyDown={(e) => handleKeyDown(e, String(paper.id), 'limitations')}
                                                className="w-full px-2 py-1 border border-indigo-500 rounded focus:outline-none focus:ring-1 focus:ring-indigo-500 min-h-[60px] text-sm"
                                                autoFocus
                                            />
                                        ) : (
                                            <div className="flex items-start gap-2">
                                                <p className="text-sm text-gray-600 flex-1">{displayValues.limitations}</p>
                                                {isSaving(String(paper.id), 'limitations') && <Loader2 className="w-3 h-3 animate-spin text-gray-400 mt-1" />}
                                                {isSaved(String(paper.id), 'limitations') && <Check className="w-3 h-3 text-green-500 mt-1" />}
                                            </div>
                                        )}
                                    </div>
                                </div>
                            </div>
                        );
                    })}
                </div>
            </div>
        </div>
    );
}
