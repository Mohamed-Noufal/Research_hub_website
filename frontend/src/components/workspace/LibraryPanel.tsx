import { useState, useEffect } from 'react';
import { FolderOpen, BookmarkCheck, LayoutGrid, Plus, FolderPlus, Star, MoreVertical, Eye, Download, Share2, Folder } from 'lucide-react';
import { Button } from '../ui/button';
import { Badge } from '../ui/badge';
import type { Paper } from '../../App';
import { toast } from 'sonner';
import CreateFolderDialog from './CreateFolderDialog';
import AddPaperDialog, { type ManualPaperData } from './AddPaperDialog';
import FolderSelectorDialog from './FolderSelectorDialog';
import apiService from '../../services/api';

interface LibraryPanelProps {
  onOpenPaper: (paper: Paper) => void;
}

interface FolderType {
  id: string;
  name: string;
  paperCount: number;
}

export default function LibraryPanel({ onOpenPaper }: LibraryPanelProps) {
  const [selectedFolder, setSelectedFolder] = useState('all');
  const [showCreateFolderDialog, setShowCreateFolderDialog] = useState(false);
  const [showAddPaperDialog, setShowAddPaperDialog] = useState(false);
  const [folderSelectorPaper, setFolderSelectorPaper] = useState<Paper | null>(null);
  const [folders, setFolders] = useState<FolderType[]>([]);
  const [folderPaperIds, setFolderPaperIds] = useState<Set<string>>(new Set());
  const [isLoadingFolders, setIsLoadingFolders] = useState(false);
  const [papers, setPapers] = useState<Paper[]>([]);
  // const [isLoadingPapers, setIsLoadingPapers] = useState(false);

  // Fetch folders and papers on mount
  useEffect(() => {
    fetchFolders();
    fetchPapers();
  }, []);

  // Fetch papers for selected folder when it changes
  useEffect(() => {
    if (selectedFolder === 'all') {
      setFolderPaperIds(new Set());
    } else {
      fetchFolderPapers(selectedFolder);
    }
  }, [selectedFolder]);

  const fetchFolders = async () => {
    try {
      setIsLoadingFolders(true);
      const data = await apiService.getPaperFolders();
      // Map API response to FolderType
      const mappedFolders = data.map((f: any) => ({
        id: f.id.toString(),
        name: f.name,
        paperCount: f.paper_count
      }));
      setFolders(mappedFolders);
    } catch (error) {
      console.error('Failed to fetch folders:', error);
      toast.error('Failed to load folders');
    } finally {
      setIsLoadingFolders(false);
    }
  };

  const fetchPapers = async () => {
    try {
      // setIsLoadingPapers(true);
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
      setPapers(transformedPapers);
    } catch (error) {
      console.error('Failed to fetch papers:', error);
      toast.error('Failed to load papers');
      // finally {
      //   setIsLoadingPapers(false);
      // }
    }
  };

  const fetchFolderPapers = async (folderId: string) => {
    try {
      const data = await apiService.getFolderPapers(folderId);
      // Backend returns integer IDs, convert to string for comparison if needed
      // Assuming Paper.id is string based on interface
      setFolderPaperIds(new Set(data.paper_ids.map((id: number) => id.toString())));
    } catch (error) {
      console.error('Failed to fetch folder papers:', error);
      toast.error('Failed to filter papers');
    }
  };

  // Filter papers
  const filteredPapers = selectedFolder === 'all'
    ? papers
    : papers.filter(p => folderPaperIds.has(p.id.toString()));

  const handleCreateFolder = async (name: string, description?: string) => {
    try {
      await apiService.createPaperFolder(name, description);
      toast.success(`Folder "${name}" created!`);
      fetchFolders(); // Refresh list
    } catch (error) {
      console.error('Failed to create folder:', error);
      toast.error('Failed to create folder');
    }
  };

  const handleAddPaper = async (paperData: ManualPaperData) => {
    try {
      const formData = new FormData();
      formData.append('title', paperData.title);
      formData.append('authors', paperData.authors.join(', '));
      if (paperData.abstract) formData.append('abstract', paperData.abstract);
      if (paperData.year) formData.append('year', paperData.year.toString());
      if (paperData.doi) formData.append('doi', paperData.doi);
      if (paperData.venue) formData.append('venue', paperData.venue);
      if (paperData.folderId) formData.append('folder_id', paperData.folderId);
      if (paperData.pdfFile) formData.append('pdf_file', paperData.pdfFile);

      await apiService.createManualPaper(formData);
      toast.success(`Paper "${paperData.title}" added!`);

      // Refresh papers and folders
      fetchPapers();
      fetchFolders();
    } catch (error) {
      console.error('Failed to add paper:', error);
      toast.error('Failed to add paper');
    }
  };

  const handleSaveFolders = async (_paperTitle: string, folderIds: string[]) => {
    if (!folderSelectorPaper) return;

    try {
      // Add paper to each selected folder
      // Note: This is a simplified implementation. Ideally we'd compare and remove unchecked ones.
      // For now, we just add to newly selected ones.
      const promises = folderIds.map(folderId =>
        apiService.addPaperToFolder(folderId, folderSelectorPaper.id)
      );

      await Promise.all(promises);
      toast.success('Added to folders!');
      fetchFolders(); // Update counts
      fetchPapers(); // Refresh papers list
    } catch (error) {
      console.error('Failed to update folders:', error);
      toast.error('Failed to update folders');
    }
  };

  const handleRemoveFromFolder = async (paperId: string) => {
    try {
      if (selectedFolder === 'all') {
        // Remove from saved papers entirely
        await apiService.unsavePaper(parseInt(paperId));
        toast.success('Removed from library!');
        fetchPapers(); // Refresh all papers
      } else {
        // Remove from specific folder only
        await apiService.removePaperFromFolder(selectedFolder, paperId);
        toast.success('Removed from folder!');
        fetchFolders(); // Update counts
        fetchFolderPapers(selectedFolder); // Refresh the current folder's papers
      }
    } catch (error) {
      console.error('Failed to remove paper:', error);
      toast.error('Failed to remove paper');
    }
  };

  return (
    <div className="flex flex-col h-full bg-gray-50">
      {/* Header */}
      <div className="p-4 border-b border-gray-200 space-y-3 bg-white">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-semibold flex items-center gap-2 text-gray-900">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-purple-500 to-blue-500 flex items-center justify-center">
              <BookmarkCheck className="w-4 h-4 text-white" />
            </div>
            Library
          </h2>

          {/* View Mode Toggle (Grid only for now) */}
          <div className="flex items-center gap-2">
            <button
              className="p-2 rounded-lg bg-purple-100 text-purple-600"
              title="Grid view"
            >
              <LayoutGrid className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* Action Buttons Row */}
        <div className="flex gap-2">
          <Button
            variant="outline"
            className="flex-1 text-sm"
            onClick={() => setShowCreateFolderDialog(true)}
          >
            <FolderPlus className="w-4 h-4 mr-2" />
            New Folder
          </Button>
          <Button
            variant="outline"
            className="flex-1 text-sm"
            onClick={() => setShowAddPaperDialog(true)}
          >
            <Plus className="w-4 h-4 mr-2" />
            Add Paper
          </Button>
        </div>

        {/* Folder Dropdown */}
        <div className="relative">
          <select
            value={selectedFolder}
            onChange={(e) => setSelectedFolder(e.target.value)}
            className="w-full px-3 py-2 rounded-lg bg-white border border-gray-300 hover:bg-gray-50 transition-colors cursor-pointer text-sm text-gray-900 font-medium"
            disabled={isLoadingFolders}
          >
            <option value="all">📁 All Papers ({papers.length})</option>
            {folders.map((folder) => (
              <option key={folder.id} value={folder.id}>
                📁 {folder.name} ({folder.paperCount})
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Papers Grid */}
      <div className="flex-1 overflow-y-auto p-4">
        {filteredPapers.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-gray-400">
            <div className="w-20 h-20 bg-gray-100 rounded-2xl flex items-center justify-center mb-4">
              <FolderOpen className="w-10 h-10 text-gray-300" />
            </div>
            <p className="text-sm font-medium text-gray-600">
              {papers.length === 0 ? 'No saved papers yet' : 'No papers in this folder'}
            </p>
            <p className="text-xs text-gray-400 mt-1">
              {papers.length === 0 ? 'Search and save papers to build your library' : 'Add papers to this folder to see them here'}
            </p>
          </div>
        ) : (
          <div className="grid grid-cols-1 gap-4">
            {filteredPapers.map((paper, index) => (
              <PaperCard
                key={paper.id}
                paper={paper}
                index={index}
                onOpen={() => onOpenPaper(paper)}
                onAddToFolder={() => setFolderSelectorPaper(paper)}
                onRemoveFromFolder={() => handleRemoveFromFolder(paper.id)}
                isInFolder={selectedFolder !== 'all'}
              />
            ))}
          </div>
        )}
      </div>

      {/* Bottom Stats */}
      {filteredPapers.length > 0 && (
        <div className="p-3 border-t border-gray-200 bg-white">
          <p className="text-xs text-gray-500 text-center">
            Showing {filteredPapers.length} of {papers.length} papers
          </p>
        </div>
      )}

      {/* Dialogs */}
      <CreateFolderDialog
        isOpen={showCreateFolderDialog}
        onClose={() => setShowCreateFolderDialog(false)}
        onCreateFolder={handleCreateFolder}
      />

      <AddPaperDialog
        isOpen={showAddPaperDialog}
        onClose={() => setShowAddPaperDialog(false)}
        onAddPaper={handleAddPaper}
        folders={folders}
      />

      <FolderSelectorDialog
        isOpen={folderSelectorPaper !== null}
        onClose={() => setFolderSelectorPaper(null)}
        folders={folders}
        selectedFolderIds={[]} // TODO: Fetch existing folders for paper
        onSave={(folderIds) => {
          if (folderSelectorPaper) {
            handleSaveFolders(folderSelectorPaper.title, folderIds);
            setFolderSelectorPaper(null);
          }
        }}
        paperTitle={folderSelectorPaper?.title || ''}
      />
    </div>
  );
}

// Paper Card Component
interface PaperCardProps {
  paper: Paper;
  index: number;
  onOpen: () => void;
  onAddToFolder: () => void;
  onRemoveFromFolder?: () => void;
  isInFolder?: boolean;
}

function PaperCard({ paper, index, onOpen, onAddToFolder, onRemoveFromFolder, isInFolder }: PaperCardProps) {
  const [isHovered, setIsHovered] = useState(false);

  const formatAuthors = (authors: string[]) => {
    if (authors.length === 0) return 'Unknown';
    if (authors.length <= 2) return authors.join(', ');
    return `${authors[0]}, et al.`;
  };

  const getCategoryIcon = () => {
    const source = paper.source.toLowerCase();
    if (source.includes('pubmed') || source.includes('medical')) return '🏥';
    if (source.includes('arxiv') || source.includes('cs')) return '💻';
    if (source.includes('ieee')) return '⚡';
    return '📄';
  };

  return (
    <div
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
      className={`
        group bg-white border border-gray-200 rounded-xl p-4 transition-all duration-300 cursor-pointer
        ${isHovered ? 'shadow-lg -translate-y-1 border-purple-300' : 'hover:shadow-md'}
      `}
      style={{
        animationDelay: `${index * 50}ms`,
        animation: 'fadeIn 0.3s ease-out forwards',
      }}
      onClick={onOpen}
    >
      {/* Icon */}
      <div className="text-2xl mb-2">
        {getCategoryIcon()}
      </div>

      <div className="flex-1 min-w-0">
        {/* Title */}
        <h3 className="text-sm font-semibold text-gray-900 line-clamp-2 mb-2 leading-snug">
          {paper.title}
        </h3>

        {/* Authors & Year */}
        <div className="flex items-center gap-2 text-xs text-gray-600 mb-2">
          <span>👥 {formatAuthors(paper.authors)}</span>
          <span>•</span>
          <span>📅 {paper.year}</span>
        </div>

        {/* Metadata */}
        <div className="flex items-center gap-2 text-xs text-gray-500 mb-3 flex-wrap">
          <Badge variant="secondary" className="text-xs">
            {paper.source}
          </Badge>
          {paper.venue && (
            <span className="truncate">{paper.venue}</span>
          )}
          <span>📊 {paper.citations} citations</span>

          {/* PDF Status Badge */}
          {paper.pdfUrl ? (
            paper.pdfUrl.startsWith('http://localhost') ? (
              <Badge className="text-xs bg-green-100 text-green-700 border-green-200">
                📄 PDF Local
              </Badge>
            ) : (
              <Badge className="text-xs bg-blue-100 text-blue-700 border-blue-200">
                🔗 PDF Link
              </Badge>
            )
          ) : (
            <Badge variant="outline" className="text-xs text-gray-400 border-gray-300">
              ❌ No PDF
            </Badge>
          )}
        </div>

        {/* Abstract Preview */}
        {paper.abstract && (
          <p className="text-xs text-gray-600 line-clamp-2 leading-relaxed mb-3">
            {paper.abstract}
          </p>
        )}

        {/* Quick Actions (Show on hover) */}
        <div className={`
          flex items-center gap-2 transition-opacity duration-200
          ${isHovered ? 'opacity-100' : 'opacity-0'}
        `}>
          <button
            onClick={(e) => {
              e.stopPropagation();
              toast.success('Added to favorites');
            }}
            className="p-1.5 rounded-lg bg-purple-50 text-purple-600 hover:bg-purple-100 transition-colors"
            title="Add to favorites"
          >
            <Star className="w-3.5 h-3.5" />
          </button>
          <button
            onClick={(e) => {
              e.stopPropagation();
              onOpen();
            }}
            className="p-1.5 rounded-lg bg-blue-50 text-blue-600 hover:bg-blue-100 transition-colors"
            title="Quick view"
          >
            <Eye className="w-3.5 h-3.5" />
          </button>
          <button
            onClick={(e) => {
              e.stopPropagation();
              onAddToFolder();
            }}
            className="p-1.5 rounded-lg bg-indigo-50 text-indigo-600 hover:bg-indigo-100 transition-colors"
            title="Add to folder"
          >
            <Folder className="w-3.5 h-3.5" />
          </button>
          <button
            onClick={(e) => {
              e.stopPropagation();
              toast.success('Download started');
            }}
            className="p-1.5 rounded-lg bg-green-50 text-green-600 hover:bg-green-100 transition-colors"
            title="Download"
          >
            <Download className="w-3.5 h-3.5" />
          </button>
          <button
            onClick={(e) => {
              e.stopPropagation();
              toast.success('Share link copied');
            }}
            className="p-1.5 rounded-lg bg-gray-50 text-gray-600 hover:bg-gray-100 transition-colors"
            title="Share"
          >
            <Share2 className="w-3.5 h-3.5" />
          </button>
          {onRemoveFromFolder && (
            <button
              onClick={(e) => {
                e.stopPropagation();
                onRemoveFromFolder();
              }}
              className="p-1.5 rounded-lg bg-red-50 text-red-600 hover:bg-red-100 transition-colors"
              title={isInFolder ? "Remove from this folder" : "Remove from library"}
            >
              <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          )}
          <div className="flex-1" />
          <button
            onClick={(e) => e.stopPropagation()}
            className="p-1.5 rounded-lg bg-gray-50 text-gray-600 hover:bg-gray-100 transition-colors"
            title="More options"
          >
            <MoreVertical className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>
    </div>
  );
}

// Add keyframes animation
const style = document.createElement('style');
style.textContent = `
  @keyframes fadeIn {
    from {
      opacity: 0;
      transform: translateY(10px);
    }
    to {
      opacity: 1;
      transform: translateY(0);
    }
  }
`;
document.head.appendChild(style);
