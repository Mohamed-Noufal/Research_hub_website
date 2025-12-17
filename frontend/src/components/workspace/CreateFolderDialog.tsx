import { useState } from 'react';
import { X, FolderPlus } from 'lucide-react';
import { Button } from '../ui/button';
import { Input } from '../ui/input';
import { Textarea } from '../ui/textarea';

interface CreateFolderDialogProps {
    isOpen: boolean;
    onClose: () => void;
    onCreateFolder: (name: string, description?: string) => void;
}

export default function CreateFolderDialog({ isOpen, onClose, onCreateFolder }: CreateFolderDialogProps) {
    const [folderName, setFolderName] = useState('');
    const [description, setDescription] = useState('');
    const [isSubmitting, setIsSubmitting] = useState(false);

    if (!isOpen) return null;

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!folderName.trim()) return;

        setIsSubmitting(true);
        await onCreateFolder(folderName.trim(), description.trim() || undefined);
        setIsSubmitting(false);

        // Reset form
        setFolderName('');
        setDescription('');
        onClose();
    };

    const handleClose = () => {
        setFolderName('');
        setDescription('');
        onClose();
    };

    return (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
            <div className="bg-white rounded-xl shadow-2xl w-full max-w-md mx-4">
                {/* Header */}
                <div className="flex items-center justify-between p-6 border-b border-gray-200">
                    <div className="flex items-center gap-3">
                        <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-purple-500 to-blue-500 flex items-center justify-center">
                            <FolderPlus className="w-5 h-5 text-white" />
                        </div>
                        <h2 className="text-lg font-semibold text-gray-900">Create New Folder</h2>
                    </div>
                    <button
                        onClick={handleClose}
                        className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
                    >
                        <X className="w-5 h-5 text-gray-500" />
                    </button>
                </div>

                {/* Form */}
                <form onSubmit={handleSubmit} className="p-6 space-y-4">
                    {/* Folder Name */}
                    <div>
                        <label htmlFor="folderName" className="block text-sm font-medium text-gray-700 mb-2">
                            Folder Name <span className="text-red-500">*</span>
                        </label>
                        <Input
                            id="folderName"
                            type="text"
                            value={folderName}
                            onChange={(e) => setFolderName(e.target.value)}
                            placeholder="e.g., Thesis Chapter 1, Machine Learning Papers"
                            className="w-full"
                            maxLength={100}
                            required
                            autoFocus
                        />
                        <p className="text-xs text-gray-500 mt-1">{folderName.length}/100 characters</p>
                    </div>

                    {/* Description */}
                    <div>
                        <label htmlFor="description" className="block text-sm font-medium text-gray-700 mb-2">
                            Description <span className="text-gray-400">(optional)</span>
                        </label>
                        <Textarea
                            id="description"
                            value={description}
                            onChange={(e) => setDescription(e.target.value)}
                            placeholder="Add notes about what papers belong in this folder..."
                            className="w-full resize-none"
                            rows={3}
                            maxLength={500}
                        />
                        <p className="text-xs text-gray-500 mt-1">{description.length}/500 characters</p>
                    </div>

                    {/* Actions */}
                    <div className="flex gap-3 pt-4">
                        <Button
                            type="button"
                            variant="outline"
                            onClick={handleClose}
                            className="flex-1"
                            disabled={isSubmitting}
                        >
                            Cancel
                        </Button>
                        <Button
                            type="submit"
                            className="flex-1 bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-700 hover:to-blue-700"
                            disabled={!folderName.trim() || isSubmitting}
                        >
                            {isSubmitting ? 'Creating...' : 'Create Folder'}
                        </Button>
                    </div>
                </form>
            </div>
        </div>
    );
}
