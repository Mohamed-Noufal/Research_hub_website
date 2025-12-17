import { useState } from 'react';
import { X, Plus, Upload } from 'lucide-react';
import { Button } from '../ui/button';
import { Input } from '../ui/input';
import { Textarea } from '../ui/textarea';
import { toast } from 'sonner';

interface Folder {
    id: string;
    name: string;
}

interface AddPaperDialogProps {
    isOpen: boolean;
    onClose: () => void;
    onAddPaper: (paperData: ManualPaperData) => void;
    folders: Folder[];
}

export interface ManualPaperData {
    title: string;
    authors: string[];
    abstract?: string;
    year?: number;
    doi?: string;
    venue?: string;
    pdfFile?: File;
    folderId?: string;
}

export default function AddPaperDialog({ isOpen, onClose, onAddPaper, folders }: AddPaperDialogProps) {
    const [title, setTitle] = useState('');
    const [authors, setAuthors] = useState('');
    const [abstract, setAbstract] = useState('');
    const [year, setYear] = useState('');
    const [doi, setDoi] = useState('');
    const [venue, setVenue] = useState('');
    const [pdfFile, setPdfFile] = useState<File | null>(null);
    const [selectedFolder, setSelectedFolder] = useState('');
    const [isSubmitting, setIsSubmitting] = useState(false);

    if (!isOpen) return null;

    const handlePdfUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
        const file = e.target.files?.[0];
        if (file) {
            if (file.type !== 'application/pdf') {
                toast.error('Please upload a PDF file');
                return;
            }
            if (file.size > 50 * 1024 * 1024) { // 50MB limit
                toast.error('PDF file must be less than 50MB');
                return;
            }
            setPdfFile(file);
            toast.success(`Selected: ${file.name}`);
        }
    };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!title.trim() || !authors.trim()) {
            toast.error('Title and authors are required');
            return;
        }

        setIsSubmitting(true);

        const paperData: ManualPaperData = {
            title: title.trim(),
            authors: authors.split(',').map(a => a.trim()).filter(Boolean),
            abstract: abstract.trim() || undefined,
            year: year ? parseInt(year) : undefined,
            doi: doi.trim() || undefined,
            venue: venue.trim() || undefined,
            pdfFile: pdfFile || undefined,
            folderId: selectedFolder || undefined,
        };

        await onAddPaper(paperData);
        setIsSubmitting(false);

        // Reset form
        resetForm();
        onClose();
    };

    const resetForm = () => {
        setTitle('');
        setAuthors('');
        setAbstract('');
        setYear('');
        setDoi('');
        setVenue('');
        setPdfFile(null);
        setSelectedFolder('');
    };

    const handleClose = () => {
        resetForm();
        onClose();
    };

    return (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
            <div className="bg-white rounded-xl shadow-2xl w-full max-w-2xl max-h-[90vh] overflow-y-auto">
                {/* Header */}
                <div className="sticky top-0 bg-white flex items-center justify-between p-6 border-b border-gray-200 z-10">
                    <div className="flex items-center gap-3">
                        <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-green-500 to-emerald-500 flex items-center justify-center">
                            <Plus className="w-5 h-5 text-white" />
                        </div>
                        <h2 className="text-lg font-semibold text-gray-900">Add Paper Manually</h2>
                    </div>
                    <button
                        onClick={handleClose}
                        className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
                    >
                        <X className="w-5 h-5 text-gray-500" />
                    </button>
                </div>

                {/* Form */}
                <form onSubmit={handleSubmit} className="p-6 space-y-5">
                    {/* Title */}
                    <div>
                        <label htmlFor="title" className="block text-sm font-medium text-gray-700 mb-2">
                            Title <span className="text-red-500">*</span>
                        </label>
                        <Input
                            id="title"
                            type="text"
                            value={title}
                            onChange={(e) => setTitle(e.target.value)}
                            placeholder="Enter paper title"
                            className="w-full"
                            required
                            autoFocus
                        />
                    </div>

                    {/* Authors */}
                    <div>
                        <label htmlFor="authors" className="block text-sm font-medium text-gray-700 mb-2">
                            Authors <span className="text-red-500">*</span>
                        </label>
                        <Input
                            id="authors"
                            type="text"
                            value={authors}
                            onChange={(e) => setAuthors(e.target.value)}
                            placeholder="John Doe, Jane Smith, et al. (comma-separated)"
                            className="w-full"
                            required
                        />
                        <p className="text-xs text-gray-500 mt-1">Separate multiple authors with commas</p>
                    </div>

                    {/* Abstract */}
                    <div>
                        <label htmlFor="abstract" className="block text-sm font-medium text-gray-700 mb-2">
                            Abstract <span className="text-gray-400">(optional)</span>
                        </label>
                        <Textarea
                            id="abstract"
                            value={abstract}
                            onChange={(e) => setAbstract(e.target.value)}
                            placeholder="Paste the paper abstract here..."
                            className="w-full resize-none"
                            rows={4}
                        />
                    </div>

                    {/* Year and DOI */}
                    <div className="grid grid-cols-2 gap-4">
                        <div>
                            <label htmlFor="year" className="block text-sm font-medium text-gray-700 mb-2">
                                Year <span className="text-gray-400">(optional)</span>
                            </label>
                            <Input
                                id="year"
                                type="number"
                                value={year}
                                onChange={(e) => setYear(e.target.value)}
                                placeholder="2024"
                                min="1900"
                                max={new Date().getFullYear() + 1}
                                className="w-full"
                            />
                        </div>
                        <div>
                            <label htmlFor="doi" className="block text-sm font-medium text-gray-700 mb-2">
                                DOI <span className="text-gray-400">(optional)</span>
                            </label>
                            <Input
                                id="doi"
                                type="text"
                                value={doi}
                                onChange={(e) => setDoi(e.target.value)}
                                placeholder="10.1234/example"
                                className="w-full"
                            />
                        </div>
                    </div>

                    {/* Venue */}
                    <div>
                        <label htmlFor="venue" className="block text-sm font-medium text-gray-700 mb-2">
                            Venue/Journal <span className="text-gray-400">(optional)</span>
                        </label>
                        <Input
                            id="venue"
                            type="text"
                            value={venue}
                            onChange={(e) => setVenue(e.target.value)}
                            placeholder="e.g., Nature, CVPR 2024"
                            className="w-full"
                        />
                    </div>

                    {/* PDF Upload */}
                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-2">
                            PDF File <span className="text-gray-400">(optional)</span>
                        </label>
                        <div className="flex items-center gap-3">
                            <label className="flex-1 cursor-pointer">
                                <div className="flex items-center justify-center gap-2 px-4 py-3 border-2 border-dashed border-gray-300 rounded-lg hover:border-purple-400 hover:bg-purple-50 transition-colors">
                                    <Upload className="w-5 h-5 text-gray-400" />
                                    <span className="text-sm text-gray-600">
                                        {pdfFile ? pdfFile.name : 'Click to upload PDF'}
                                    </span>
                                </div>
                                <input
                                    type="file"
                                    accept=".pdf"
                                    onChange={handlePdfUpload}
                                    className="hidden"
                                />
                            </label>
                            {pdfFile && (
                                <button
                                    type="button"
                                    onClick={() => setPdfFile(null)}
                                    className="px-3 py-2 text-sm text-red-600 hover:bg-red-50 rounded-lg transition-colors"
                                >
                                    Remove
                                </button>
                            )}
                        </div>
                        {pdfFile && (
                            <p className="text-xs text-gray-500 mt-1">
                                Size: {(pdfFile.size / 1024 / 1024).toFixed(2)} MB
                            </p>
                        )}
                    </div>

                    {/* Folder Selection */}
                    <div>
                        <label htmlFor="folder" className="block text-sm font-medium text-gray-700 mb-2">
                            Add to Folder <span className="text-gray-400">(optional)</span>
                        </label>
                        <select
                            id="folder"
                            value={selectedFolder}
                            onChange={(e) => setSelectedFolder(e.target.value)}
                            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                        >
                            <option value="">None (All Papers only)</option>
                            {folders.filter(f => f.id !== 'all').map((folder) => (
                                <option key={folder.id} value={folder.id}>
                                    📁 {folder.name}
                                </option>
                            ))}
                        </select>
                    </div>

                    {/* Actions */}
                    <div className="flex gap-3 pt-4 border-t border-gray-200">
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
                            className="flex-1 bg-gradient-to-r from-green-600 to-emerald-600 hover:from-green-700 hover:to-emerald-700"
                            disabled={!title.trim() || !authors.trim() || isSubmitting}
                        >
                            {isSubmitting ? 'Adding...' : 'Add Paper'}
                        </Button>
                    </div>
                </form>
            </div>
        </div>
    );
}
