import { useState } from 'react';
import { X, FolderOpen } from 'lucide-react';
import { Button } from '../ui/button';

interface Folder {
    id: string;
    name: string;
}

interface FolderSelectorDialogProps {
    isOpen: boolean;
    onClose: () => void;
    folders: Folder[];
    selectedFolderIds: string[];
    onSave: (folderIds: string[]) => void;
    paperTitle: string;
}

export default function FolderSelectorDialog({
    isOpen,
    onClose,
    folders,
    selectedFolderIds,
    onSave,
    paperTitle
}: FolderSelectorDialogProps) {
    const [selected, setSelected] = useState<string[]>(selectedFolderIds);

    if (!isOpen) return null;

    const toggleFolder = (folderId: string) => {
        setSelected(prev =>
            prev.includes(folderId)
                ? prev.filter(id => id !== folderId)
                : [...prev, folderId]
        );
    };

    const handleSave = () => {
        onSave(selected);
        onClose();
    };

    const handleClose = () => {
        setSelected(selectedFolderIds); // Reset to original
        onClose();
    };

    // Filter out "All Papers" folder
    const selectableFolders = folders.filter(f => f.id !== 'all');

    return (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
            <div className="bg-white rounded-xl shadow-2xl w-full max-w-md mx-4">
                {/* Header */}
                <div className="flex items-center justify-between p-6 border-b border-gray-200">
                    <div className="flex items-center gap-3">
                        <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-blue-500 to-indigo-500 flex items-center justify-center">
                            <FolderOpen className="w-5 h-5 text-white" />
                        </div>
                        <div>
                            <h2 className="text-lg font-semibold text-gray-900">Add to Folders</h2>
                            <p className="text-xs text-gray-500 line-clamp-1">{paperTitle}</p>
                        </div>
                    </div>
                    <button
                        onClick={handleClose}
                        className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
                    >
                        <X className="w-5 h-5 text-gray-500" />
                    </button>
                </div>

                {/* Folder List */}
                <div className="p-6">
                    {selectableFolders.length === 0 ? (
                        <div className="text-center py-8 text-gray-400">
                            <FolderOpen className="w-12 h-12 mx-auto mb-3 text-gray-300" />
                            <p className="text-sm font-medium">No folders yet</p>
                            <p className="text-xs mt-1">Create a folder first to organize your papers</p>
                        </div>
                    ) : (
                        <div className="space-y-2 max-h-96 overflow-y-auto">
                            {selectableFolders.map((folder) => (
                                <label
                                    key={folder.id}
                                    className="flex items-center gap-3 p-3 rounded-lg hover:bg-gray-50 cursor-pointer transition-colors border border-transparent hover:border-gray-200"
                                >
                                    <input
                                        type="checkbox"
                                        checked={selected.includes(folder.id)}
                                        onChange={() => toggleFolder(folder.id)}
                                        className="w-4 h-4 text-purple-600 border-gray-300 rounded focus:ring-purple-500"
                                    />
                                    <span className="flex-1 text-sm text-gray-900">
                                        📁 {folder.name}
                                    </span>
                                </label>
                            ))}
                        </div>
                    )}
                </div>

                {/* Actions */}
                <div className="flex gap-3 p-6 border-t border-gray-200">
                    <Button
                        type="button"
                        variant="outline"
                        onClick={handleClose}
                        className="flex-1"
                    >
                        Cancel
                    </Button>
                    <Button
                        type="button"
                        onClick={handleSave}
                        className="flex-1 bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700"
                        disabled={selectableFolders.length === 0}
                    >
                        Save
                    </Button>
                </div>
            </div>
        </div>
    );
}
