import { useState, useEffect } from 'react';
import { Scale, Plus, Download, Check, AlertCircle, Edit2, Loader2 } from 'lucide-react';
import { Button } from '../../ui/button';
// import { Badge } from '../../ui/badge';
import type { ResearchPaper } from './types';
import { useComparisonConfig, useUpdateComparisonConfig, useUpdateComparisonAttribute, useComparisonAttributes } from '../../../hooks/useComparison';

interface EditingCell {
    paperId: number;
    attributeName: string;
}

export default function ComparisonView({ papers, projectId }: { papers: ResearchPaper[], projectId?: number }) {
    const [selectedIds, setSelectedIds] = useState<number[]>([]);
    const [showSelector, setShowSelector] = useState(false);
    const [editingSimilarities, setEditingSimilarities] = useState(false);
    const [editingDifferences, setEditingDifferences] = useState(false);
    const [similaritiesText, setSimilaritiesText] = useState('');
    const [differencesText, setDifferencesText] = useState('');
    const [editingCell, setEditingCell] = useState<EditingCell | null>(null);
    const [editCellValue, setEditCellValue] = useState('');
    const [savingCell, setSavingCell] = useState<EditingCell | null>(null);
    const [savedCell, setSavedCell] = useState<EditingCell | null>(null);

    const { data: configData } = useComparisonConfig(projectId ? String(projectId) : '');
    const { data: attributesData } = useComparisonAttributes(projectId ? String(projectId) : '');
    const updateConfig = useUpdateComparisonConfig();
    const updateAttribute = useUpdateComparisonAttribute();

    // Load saved configuration
    useEffect(() => {
        if (configData) {
            if (configData.selected_paper_ids && configData.selected_paper_ids.length > 0) {
                setSelectedIds(configData.selected_paper_ids.map(id => parseInt(id)));
            } else if (selectedIds.length === 0 && papers.length > 0) {
                setSelectedIds(papers.slice(0, 3).map(p => p.id));
            }

            setSimilaritiesText(configData.insights_similarities ||
                `Research Focus:
• Clinical Implementation: All selected papers prioritize the practical application of AI tools within existing hospital workflows rather than purely theoretical model development.
• Outcome Metrics: Consistent focus on efficiency gains (time saved) and diagnostic accuracy as primary success indicators.

Findings:
• Positive Impact: Unanimous reporting of statistical significance in performance improvements when AI assistance is utilized.`
            );

            setDifferencesText(configData.insights_differences ||
                `Methodological Approach:
• Study Design: Significant variation in rigor, ranging from high-quality Randomized Controlled Trials to observational Case Studies.
• Data Sources: Divergence in data origin; some utilize structured EHR data while others rely on self-reported survey responses.

Scope & Scale:
• Sample Size: Wide disparity in participant numbers, from small-scale pilots (N=50) to large multi-center datasets (N=500+).`
            );
        }
    }, [configData, papers]);

    const selectedPapers = papers.filter(p => selectedIds.includes(p.id));

    const toggleSelection = async (id: number) => {
        const newIds = selectedIds.includes(id)
            ? selectedIds.filter(p => p !== id)
            : [...selectedIds, id];

        setSelectedIds(newIds);

        if (projectId) {
            try {
                await updateConfig.mutateAsync({
                    projectId: String(projectId),
                    config: { selected_paper_ids: newIds.map(String) }
                });
            } catch (error) {
                console.error('Failed to save selection:', error);
            }
        }
    };

    const handleSaveSimilarities = async () => {
        if (!projectId) return;
        try {
            await updateConfig.mutateAsync({
                projectId: String(projectId),
                config: { insights_similarities: similaritiesText }
            });
            setEditingSimilarities(false);
        } catch (error) {
            console.error('Failed to save similarities:', error);
        }
    };

    const handleSaveDifferences = async () => {
        if (!projectId) return;
        try {
            await updateConfig.mutateAsync({
                projectId: String(projectId),
                config: { insights_differences: differencesText }
            });
            setEditingDifferences(false);
        } catch (error) {
            console.error('Failed to save differences:', error);
        }
    };

    const handleCellClick = (paperId: number, attributeName: string, currentValue: string) => {
        setEditingCell({ paperId, attributeName });
        setEditCellValue(currentValue);
    };

    const handleCellSave = async (paperId: number, attributeName: string) => {
        if (!projectId) return;

        setSavingCell({ paperId, attributeName });

        try {
            await updateAttribute.mutateAsync({
                projectId: String(projectId),
                paperId: String(paperId),
                attribute: {
                    attribute_name: attributeName,
                    attribute_value: editCellValue
                }
            });

            setSavedCell({ paperId, attributeName });
            setTimeout(() => setSavedCell(null), 2000);
        } catch (error) {
            console.error('Failed to save cell:', error);
        } finally {
            setSavingCell(null);
            setEditingCell(null);
        }
    };

    const handleCellBlur = (paperId: number, attributeName: string) => {
        handleCellSave(paperId, attributeName);
    };

    const handleCellKeyDown = (e: React.KeyboardEvent, paperId: number, attributeName: string) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            handleCellSave(paperId, attributeName);
        } else if (e.key === 'Escape') {
            setEditingCell(null);
        }
    };

    const isEditingCell = (paperId: number, attributeName: string) => {
        return editingCell?.paperId === paperId && editingCell?.attributeName === attributeName;
    };

    const isSavingCell = (paperId: number, attributeName: string) => {
        return savingCell?.paperId === paperId && savingCell?.attributeName === attributeName;
    };

    const isSavedCell = (paperId: number, attributeName: string) => {
        return savedCell?.paperId === paperId && savedCell?.attributeName === attributeName;
    };

    const EditableCell = ({ paper, attributeName, value }: { paper: ResearchPaper, attributeName: string, value: string | React.ReactNode }) => {
        const stringValue = typeof value === 'string' ? value : String(value);

        return (
            <div
                className="cursor-pointer min-h-[40px] flex items-center"
                onClick={() => handleCellClick(paper.id, attributeName, stringValue)}
            >
                {isEditingCell(paper.id, attributeName) ? (
                    <textarea
                        value={editCellValue}
                        onChange={(e) => setEditCellValue(e.target.value)}
                        onBlur={() => handleCellBlur(paper.id, attributeName)}
                        onKeyDown={(e) => handleCellKeyDown(e, paper.id, attributeName)}
                        className="w-full px-2 py-1 border border-indigo-500 rounded focus:outline-none focus:ring-1 focus:ring-indigo-500 min-h-[60px] text-sm"
                        autoFocus
                    />
                ) : (
                    <div className="flex items-start gap-2 w-full">
                        <div className="flex-1">{value}</div>
                        {isSavingCell(paper.id, attributeName) && <Loader2 className="w-3 h-3 animate-spin text-gray-400 mt-1 flex-shrink-0" />}
                        {isSavedCell(paper.id, attributeName) && <Check className="w-3 h-3 text-green-500 mt-1 flex-shrink-0" />}
                    </div>
                )}
            </div>
        );
    };

    return (
        <div className="space-y-6">
            {/* Header & Controls */}
            <div className="flex items-center justify-between bg-white p-4 rounded-xl border border-gray-200 shadow-sm">
                <div className="flex items-center gap-4">
                    <div className="flex items-center gap-2">
                        <Scale className="w-5 h-5 text-indigo-600" />
                        <h3 className="font-semibold text-gray-900">Compare Papers</h3>
                    </div>
                    <div className="h-6 w-px bg-gray-200"></div>
                    <div className="flex -space-x-2">
                        {selectedPapers.map((p) => (
                            <div key={p.id} className="w-8 h-8 rounded-full bg-indigo-100 border-2 border-white flex items-center justify-center text-xs font-medium text-indigo-700" title={p.title}>
                                {p.authors[0].charAt(0)}
                            </div>
                        ))}
                        <button
                            onClick={() => setShowSelector(!showSelector)}
                            className="w-8 h-8 rounded-full bg-gray-100 border-2 border-white flex items-center justify-center text-gray-500 hover:bg-gray-200 transition-colors"
                        >
                            <Plus className="w-4 h-4" />
                        </button>
                    </div>
                    <span className="text-sm text-gray-500">{selectedPapers.length} papers selected</span>
                </div>
                <div className="flex gap-2">
                    <Button variant="outline" size="sm">
                        <Download className="w-4 h-4 mr-2" />
                        Export Matrix
                    </Button>
                </div>
            </div>

            {/* Paper Selector */}
            {showSelector && (
                <div className="bg-white p-4 rounded-xl border border-gray-200 shadow-sm animate-in slide-in-from-top-2">
                    <h4 className="text-sm font-medium text-gray-900 mb-3">Select papers to compare:</h4>
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
                        {papers.map(paper => (
                            <div
                                key={paper.id}
                                onClick={() => toggleSelection(paper.id)}
                                className={`p-3 rounded-lg border cursor-pointer transition-all ${selectedIds.includes(paper.id)
                                    ? 'border-indigo-600 bg-indigo-50 ring-1 ring-indigo-600'
                                    : 'border-gray-200 hover:border-gray-300 hover:bg-gray-50'
                                    }`}
                            >
                                <div className="flex items-start gap-3">
                                    <div className={`mt-0.5 w-4 h-4 rounded border flex items-center justify-center ${selectedIds.includes(paper.id) ? 'bg-indigo-600 border-indigo-600' : 'border-gray-300'}`}>
                                        {selectedIds.includes(paper.id) && <Check className="w-3 h-3 text-white" />}
                                    </div>
                                    <div>
                                        <div className="text-sm font-medium text-gray-900 line-clamp-1">{paper.title}</div>
                                        <div className="text-xs text-gray-500">{paper.authors[0]} ({paper.year})</div>
                                    </div>
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            )}

            {selectedPapers.length === 0 ? (
                <div className="text-center py-12 bg-white rounded-xl border border-dashed border-gray-300">
                    <Scale className="w-12 h-12 text-gray-300 mx-auto mb-3" />
                    <h3 className="text-lg font-medium text-gray-900">No papers selected</h3>
                    <p className="text-gray-500 mb-4">Select papers from the list above to compare them side-by-side.</p>
                    <Button onClick={() => setShowSelector(true)}>Select Papers</Button>
                </div>
            ) : (
                <>
                    {/* Insights Panel */}
                    <div className="grid grid-cols-2 gap-6">
                        <div className="bg-green-50 rounded-xl p-5 border border-green-100">
                            <div className="flex items-center justify-between mb-4">
                                <h4 className="flex items-center gap-2 text-green-800 font-semibold">
                                    <Check className="w-4 h-4" />
                                    Key Similarities
                                </h4>
                                {!editingSimilarities && (
                                    <button onClick={() => setEditingSimilarities(true)} className="p-1 hover:bg-green-100 rounded transition-colors">
                                        <Edit2 className="w-4 h-4 text-green-600" />
                                    </button>
                                )}
                            </div>
                            {editingSimilarities ? (
                                <div className="space-y-2">
                                    <textarea
                                        value={similaritiesText}
                                        onChange={(e) => setSimilaritiesText(e.target.value)}
                                        className="w-full px-3 py-2 border border-green-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500 min-h-[200px] text-sm"
                                        placeholder="Enter key similarities..."
                                        autoFocus
                                    />
                                    <div className="flex gap-2">
                                        <Button size="sm" onClick={handleSaveSimilarities}>Save</Button>
                                        <Button size="sm" variant="ghost" onClick={() => setEditingSimilarities(false)}>Cancel</Button>
                                    </div>
                                </div>
                            ) : (
                                <div className="text-sm text-green-900 leading-relaxed whitespace-pre-wrap">{similaritiesText}</div>
                            )}
                        </div>

                        <div className="bg-orange-50 rounded-xl p-5 border border-orange-100">
                            <div className="flex items-center justify-between mb-4">
                                <h4 className="flex items-center gap-2 text-orange-800 font-semibold">
                                    <AlertCircle className="w-4 h-4" />
                                    Notable Differences
                                </h4>
                                {!editingDifferences && (
                                    <button onClick={() => setEditingDifferences(true)} className="p-1 hover:bg-orange-100 rounded transition-colors">
                                        <Edit2 className="w-4 h-4 text-orange-600" />
                                    </button>
                                )}
                            </div>
                            {editingDifferences ? (
                                <div className="space-y-2">
                                    <textarea
                                        value={differencesText}
                                        onChange={(e) => setDifferencesText(e.target.value)}
                                        className="w-full px-3 py-2 border border-orange-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-orange-500 min-h-[200px] text-sm"
                                        placeholder="Enter notable differences..."
                                        autoFocus
                                    />
                                    <div className="flex gap-2">
                                        <Button size="sm" onClick={handleSaveDifferences}>Save</Button>
                                        <Button size="sm" variant="ghost" onClick={() => setEditingDifferences(false)}>Cancel</Button>
                                    </div>
                                </div>
                            ) : (
                                <div className="text-sm text-orange-900 leading-relaxed whitespace-pre-wrap">{differencesText}</div>
                            )}
                        </div>
                    </div>

                    {/* Comparison Matrix */}
                    <div className="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden">
                        <div className="overflow-x-auto">
                            <table className="w-full text-sm">
                                <thead>
                                    <tr className="bg-gray-50 border-b border-gray-200">
                                        <th className="p-4 text-left text-xs font-semibold text-gray-500 uppercase w-48 sticky left-0 bg-gray-50 border-r border-gray-200">
                                            Attribute
                                        </th>
                                        {selectedPapers.map(paper => (
                                            <th key={paper.id} className="p-4 text-left w-80 min-w-[250px] border-r border-gray-100 last:border-0">
                                                {/* Editable Title */}
                                                <div className="cursor-pointer mb-1" onClick={() => handleCellClick(paper.id, 'title', paper.title)}>
                                                    {isEditingCell(paper.id, 'title') ? (
                                                        <input
                                                            type="text"
                                                            value={editCellValue}
                                                            onChange={(e) => setEditCellValue(e.target.value)}
                                                            onBlur={() => handleCellBlur(paper.id, 'title')}
                                                            onKeyDown={(e) => handleCellKeyDown(e, paper.id, 'title')}
                                                            className="w-full px-2 py-1 border border-indigo-500 rounded focus:outline-none focus:ring-1 focus:ring-indigo-500 text-sm font-semibold"
                                                            autoFocus
                                                        />
                                                    ) : (
                                                        <div className="flex items-start gap-1">
                                                            <div className="font-semibold text-gray-900 line-clamp-2 flex-1" title={paper.title}>{paper.title}</div>
                                                            {isSavingCell(paper.id, 'title') && <Loader2 className="w-3 h-3 animate-spin text-gray-400 flex-shrink-0" />}
                                                            {isSavedCell(paper.id, 'title') && <Check className="w-3 h-3 text-green-500 flex-shrink-0" />}
                                                        </div>
                                                    )}
                                                </div>
                                                {/* Editable Author/Year */}
                                                <div className="cursor-pointer" onClick={() => handleCellClick(paper.id, 'authors_year', `${paper.authors[0]} (${paper.year})`)}>
                                                    {isEditingCell(paper.id, 'authors_year') ? (
                                                        <input
                                                            type="text"
                                                            value={editCellValue}
                                                            onChange={(e) => setEditCellValue(e.target.value)}
                                                            onBlur={() => handleCellBlur(paper.id, 'authors_year')}
                                                            onKeyDown={(e) => handleCellKeyDown(e, paper.id, 'authors_year')}
                                                            className="w-full px-2 py-1 border border-indigo-500 rounded focus:outline-none focus:ring-1 focus:ring-indigo-500 text-xs"
                                                            autoFocus
                                                        />
                                                    ) : (
                                                        <div className="flex items-center gap-1">
                                                            <div className="text-xs text-gray-500 font-normal flex-1">{paper.authors[0]} ({paper.year})</div>
                                                            {isSavingCell(paper.id, 'authors_year') && <Loader2 className="w-2 h-2 animate-spin text-gray-400 flex-shrink-0" />}
                                                            {isSavedCell(paper.id, 'authors_year') && <Check className="w-2 h-2 text-green-500 flex-shrink-0" />}
                                                        </div>
                                                    )}
                                                </div>
                                            </th>
                                        ))}
                                    </tr>
                                </thead>
                                <tbody className="divide-y divide-gray-200">
                                    {/* General Info */}
                                    <tr className="bg-gray-100/50">
                                        <td colSpan={selectedPapers.length + 1} className="px-4 py-2 text-xs font-bold text-gray-500 uppercase tracking-wider sticky left-0">
                                            General Information
                                        </td>
                                    </tr>
                                    {[
                                        { label: 'Venue', key: 'venue' },
                                        { label: 'Sample Size', key: 'sampleSize' },
                                        { label: 'Quality Score', key: 'qualityScore' },
                                    ].map((row) => (
                                        <tr key={row.key} className="hover:bg-gray-50 transition-colors">
                                            <td className="p-4 font-medium text-gray-900 bg-gray-50/50 sticky left-0 border-r border-gray-200">
                                                {row.label}
                                            </td>
                                            {selectedPapers.map(paper => (
                                                <td key={paper.id} className="p-4 align-top border-r border-gray-100 last:border-0 text-gray-700 leading-relaxed">
                                                    <EditableCell
                                                        paper={paper}
                                                        attributeName={row.key}
                                                        value={attributesData?.attributes?.[`${paper.id}_${row.key}`] ?? (paper as any)[row.key] ?? ''}
                                                    />
                                                </td>
                                            ))}
                                        </tr>
                                    ))}

                                    {/* Methodology */}
                                    <tr className="bg-indigo-50/50">
                                        <td colSpan={selectedPapers.length + 1} className="px-4 py-2 text-xs font-bold text-indigo-600 uppercase tracking-wider sticky left-0">
                                            Methodology Breakdown
                                        </td>
                                    </tr>
                                    {[
                                        { label: 'Methodology Summary', key: 'methodologySummary' },
                                        { label: 'Study Design', key: 'methodologyType' },
                                        { label: 'Data Collection', key: 'dataCollection' },
                                        { label: 'Analysis Method', key: 'analysisMethod' },
                                    ].map((row) => (
                                        <tr key={row.key} className="hover:bg-gray-50 transition-colors">
                                            <td className="p-4 font-medium text-gray-900 bg-gray-50/50 sticky left-0 border-r border-gray-200">
                                                {row.label}
                                            </td>
                                            {selectedPapers.map(paper => (
                                                <td key={paper.id} className="p-4 align-top border-r border-gray-100 last:border-0 text-gray-700 leading-relaxed">
                                                    <EditableCell
                                                        paper={paper}
                                                        attributeName={row.key}
                                                        value={attributesData?.attributes?.[`${paper.id}_${row.key}`] ?? (paper as any)[row.key] ?? ''}
                                                    />
                                                </td>
                                            ))}
                                        </tr>
                                    ))}

                                    {/* Findings */}
                                    <tr className="bg-green-50/50">
                                        <td colSpan={selectedPapers.length + 1} className="px-4 py-2 text-xs font-bold text-green-600 uppercase tracking-wider sticky left-0">
                                            Findings & Implications
                                        </td>
                                    </tr>
                                    {[
                                        { label: 'Key Findings', key: 'keyFindings' },
                                        { label: 'Limitations', key: 'limitations' },
                                    ].map((row) => (
                                        <tr key={row.key} className="hover:bg-gray-50 transition-colors">
                                            <td className="p-4 font-medium text-gray-900 bg-gray-50/50 sticky left-0 border-r border-gray-200">
                                                {row.label}
                                            </td>
                                            {selectedPapers.map(paper => (
                                                <td key={paper.id} className="p-4 align-top border-r border-gray-100 last:border-0 text-gray-700 leading-relaxed">
                                                    <EditableCell
                                                        paper={paper}
                                                        attributeName={row.key}
                                                        value={attributesData?.attributes?.[`${paper.id}_${row.key}`] ?? (paper as any)[row.key] ?? ''}
                                                    />
                                                </td>
                                            ))}
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    </div>
                </>
            )}
        </div>
    );
}
