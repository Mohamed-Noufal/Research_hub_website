import { useState, useEffect } from 'react';
import { Plus, X, Trash2, Loader2, Check } from 'lucide-react';
import type { ResearchPaper } from './types';
import { useSynthesisData, useUpdateSynthesisStructure, useUpdateSynthesisCell } from '../../../hooks/useSynthesis';

export default function SynthesisView({ papers, projectId }: { papers: ResearchPaper[], projectId?: number }) {
    const [columns, setColumns] = useState<{ id: string, title: string }[]>([]);
    const [rows, setRows] = useState<{ id: string, label: string, cells: Record<string, string> }[]>([]);
    const [isSaving, setIsSaving] = useState(false);
    const [saved, setSaved] = useState(false);

    const { data: synthesisData, isLoading } = useSynthesisData(projectId ? String(projectId) : '');
    const updateStructure = useUpdateSynthesisStructure();
    const updateCell = useUpdateSynthesisCell();

    // Load saved data
    useEffect(() => {
        if (synthesisData) {
            if (synthesisData.columns && synthesisData.columns.length > 0) {
                setColumns(synthesisData.columns);
            } else {
                // Default columns
                setColumns([
                    { id: 'col1', title: 'Theme 1: Effectiveness' },
                    { id: 'col2', title: 'Theme 2: Implementation' },
                    { id: 'col3', title: 'Theme 3: Limitations' }
                ]);
            }

            if (synthesisData.rows && synthesisData.rows.length > 0) {
                // Load rows with cells
                const loadedRows = synthesisData.rows.map(row => ({
                    ...row,
                    cells: {}
                }));

                // Populate cells
                Object.entries(synthesisData.cells || {}).forEach(([key, value]) => {
                    const [rowId, colId] = key.split('_');
                    const row = loadedRows.find(r => r.id === rowId);
                    if (row) {
                        (row.cells as Record<string, string>)[colId] = value;
                    }
                });

                setRows(loadedRows);
            } else {
                // Initialize from papers
                setRows(papers.map(p => ({
                    id: `paper-${p.id}`,
                    label: p.title,
                    cells: {}
                })));
            }
        }
    }, [synthesisData, papers]);

    const saveStructure = async () => {
        if (!projectId) return;

        setIsSaving(true);
        try {
            await updateStructure.mutateAsync({
                projectId: String(projectId),
                structure: {
                    columns: columns.map(c => ({ id: c.id, title: c.title })),
                    rows: rows.map(r => ({ id: r.id, label: r.label }))
                }
            });
            setSaved(true);
            setTimeout(() => setSaved(false), 2000);
        } catch (error) {
            console.error('Failed to save structure:', error);
        } finally {
            setIsSaving(false);
        }
    };

    const addColumn = () => {
        const newId = `col-${Date.now()}`;
        setColumns([...columns, { id: newId, title: 'New Theme' }]);
    };

    const removeColumn = (colId: string) => {
        if (columns.length > 1) {
            setColumns(columns.filter(c => c.id !== colId));
        }
    };

    const updateColumnTitle = (colId: string, newTitle: string) => {
        setColumns(columns.map(c => c.id === colId ? { ...c, title: newTitle } : c));
    };

    const addRow = () => {
        const newId = `row-${Date.now()}`;
        setRows([...rows, { id: newId, label: 'New Item', cells: {} }]);
    };

    const removeRow = (rowId: string) => {
        if (rows.length > 1) {
            setRows(rows.filter(r => r.id !== rowId));
        }
    };

    const updateRowLabel = (rowId: string, newLabel: string) => {
        setRows(rows.map(r => r.id === rowId ? { ...r, label: newLabel } : r));
    };

    const updateCellValue = async (rowId: string, colId: string, value: string) => {
        // Update local state
        setRows(rows.map(r => {
            if (r.id === rowId) {
                return { ...r, cells: { ...r.cells, [colId]: value } };
            }
            return r;
        }));

        // Save to backend
        if (projectId) {
            try {
                await updateCell.mutateAsync({
                    projectId: String(projectId),
                    cell: {
                        row_id: rowId,
                        column_id: colId,
                        value
                    }
                });
            } catch (error) {
                console.error('Failed to save cell:', error);
            }
        }
    };

    if (isLoading) {
        return (
            <div className="flex items-center justify-center h-64">
                <Loader2 className="w-8 h-8 animate-spin text-gray-400" />
            </div>
        );
    }

    return (
        <div className="bg-white rounded-xl border border-gray-200 shadow-sm flex flex-col h-[600px]">
            {/* Header with action buttons */}
            <div className="p-4 border-b border-gray-200 flex justify-between items-center">
                <div>
                    <h3 className="font-semibold text-gray-900">Synthesis Matrix</h3>
                    <p className="text-xs text-gray-500">Flexible grid - click headers to edit, hover rows/columns to delete</p>
                </div>
                <div className="flex gap-1.5">
                    <button
                        onClick={addColumn}
                        className="flex items-center gap-1 px-2 py-1.5 text-xs text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded-md transition-colors"
                        title="Add Column"
                    >
                        <Plus className="w-3.5 h-3.5" />
                        <span className="hidden sm:inline">Column</span>
                    </button>
                    <button
                        onClick={addRow}
                        className="flex items-center gap-1 px-2 py-1.5 text-xs text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded-md transition-colors"
                        title="Add Row"
                    >
                        <Plus className="w-3.5 h-3.5" />
                        <span className="hidden sm:inline">Row</span>
                    </button>
                    <button
                        onClick={saveStructure}
                        disabled={isSaving}
                        className="flex items-center gap-1 px-3 py-1.5 text-xs text-white bg-gray-700 hover:bg-gray-800 rounded-md transition-colors disabled:opacity-50"
                    >
                        {isSaving ? (
                            <Loader2 className="w-3.5 h-3.5 animate-spin" />
                        ) : saved ? (
                            <Check className="w-3.5 h-3.5" />
                        ) : null}
                        {saved ? 'Saved' : 'Save'}
                    </button>
                </div>
            </div>

            {/* Scrollable table */}
            <div className="flex-1 overflow-auto">
                <table className="w-full border-collapse min-w-[800px]">
                    <thead>
                        <tr>
                            {/* Row labels header */}
                            <th className="border border-gray-200 bg-gray-100 p-3 w-56 sticky left-0 z-10">
                                <span className="text-xs font-semibold text-gray-500 uppercase">Items / Papers</span>
                            </th>
                            {/* Dynamic column headers */}
                            {columns.map(col => (
                                <th key={col.id} className="border border-gray-200 bg-gray-50 p-0 min-w-[180px] group relative">
                                    <input
                                        type="text"
                                        value={col.title}
                                        onChange={(e) => updateColumnTitle(col.id, e.target.value)}
                                        className="w-full p-3 bg-transparent font-semibold text-xs text-gray-700 focus:outline-none focus:bg-indigo-50 focus:ring-1 focus:ring-indigo-300"
                                        placeholder="Theme name..."
                                    />
                                    {columns.length > 1 && (
                                        <button
                                            onClick={() => removeColumn(col.id)}
                                            className="absolute right-2 top-1/2 -translate-y-1/2 opacity-0 group-hover:opacity-100 p-1 bg-red-100 hover:bg-red-200 rounded text-red-500 transition-all"
                                            title="Remove column"
                                        >
                                            <X className="w-3 h-3" />
                                        </button>
                                    )}
                                </th>
                            ))}
                        </tr>
                    </thead>
                    <tbody>
                        {rows.map((row) => (
                            <tr key={row.id} className="group">
                                {/* Row label (editable) */}
                                <td className="border border-gray-200 bg-gray-50 p-0 sticky left-0 z-10 group-hover:bg-gray-100 transition-colors relative">
                                    <input
                                        type="text"
                                        value={row.label}
                                        onChange={(e) => updateRowLabel(row.id, e.target.value)}
                                        className="w-full p-3 bg-transparent text-sm font-medium text-gray-900 focus:outline-none focus:bg-indigo-50"
                                        placeholder="Item name..."
                                    />
                                    {rows.length > 1 && (
                                        <button
                                            onClick={() => removeRow(row.id)}
                                            className="absolute right-2 top-1/2 -translate-y-1/2 opacity-0 group-hover:opacity-100 p-1 bg-red-100 hover:bg-red-200 rounded text-red-500 transition-all"
                                            title="Remove row"
                                        >
                                            <Trash2 className="w-3 h-3" />
                                        </button>
                                    )}
                                </td>
                                {/* Dynamic cells */}
                                {columns.map(col => (
                                    <td key={col.id} className="border border-gray-200 p-0">
                                        <textarea
                                            value={row.cells[col.id] || ''}
                                            onChange={(e) => updateCellValue(row.id, col.id, e.target.value)}
                                            className="w-full h-full p-3 min-h-[80px] text-sm resize-none focus:outline-none focus:bg-indigo-50 block"
                                            placeholder="Enter notes..."
                                        />
                                    </td>
                                ))}
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>
        </div>
    );
}
