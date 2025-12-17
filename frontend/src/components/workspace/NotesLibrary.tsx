import { useState } from 'react';
import {
  FolderPlus,
  FilePlus,
  Folder,
  FileText,
  MoreVertical,
  Edit2,
  Trash2,
  Search,
  LayoutGrid,
  List,
  Clock,
  Star
} from 'lucide-react';
import { Button } from '../ui/button';
import { Input } from '../ui/input';
import { Badge } from '../ui/badge';
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from '../ui/dropdown-menu';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter } from '../ui/dialog';
import { toast } from 'sonner';

interface NoteFile {
  id: string;
  name: string;
  type: 'file';
  content?: string;
  wordCount?: number;
  createdAt: Date;
  updatedAt: Date;
}

interface NoteFolder {
  id: string;
  name: string;
  type: 'folder';
  expanded: boolean;
  children: (NoteFile | NoteFolder)[];
  createdAt: Date;
}

type NoteItem = NoteFile | NoteFolder;
type ViewMode = 'list' | 'grid';

interface NotesLibraryProps {
  onOpenNote?: (noteId: string) => void;
}

export default function NotesLibrary({ onOpenNote }: NotesLibraryProps) {
  const [searchQuery, setSearchQuery] = useState('');
  const [viewMode, setViewMode] = useState<ViewMode>('grid');
  const [showNewDialog, setShowNewDialog] = useState(false);
  const [newItemType, setNewItemType] = useState<'file' | 'folder'>('file');
  const [newItemName, setNewItemName] = useState('');

  const [notes, setNotes] = useState<NoteItem[]>([
    {
      id: 'note-1',
      name: 'Research Plan',
      type: 'file',
      wordCount: 2450,
      createdAt: new Date(Date.now() - 3600000 * 2),
      updatedAt: new Date(Date.now() - 3600000 * 2),
    },
    {
      id: 'note-2',
      name: 'Literature Review',
      type: 'file',
      wordCount: 5200,
      createdAt: new Date(Date.now() - 3600000 * 24),
      updatedAt: new Date(Date.now() - 3600000 * 24),
    },
    {
      id: 'note-3',
      name: 'Ideas & Brainstorm',
      type: 'file',
      wordCount: 1200,
      createdAt: new Date(Date.now() - 3600000 * 48),
      updatedAt: new Date(Date.now() - 3600000 * 48),
    },
    {
      id: 'note-4',
      name: 'Meeting Notes',
      type: 'file',
      wordCount: 890,
      createdAt: new Date(Date.now() - 3600000 * 72),
      updatedAt: new Date(Date.now() - 3600000 * 72),
    },
  ]);

  const createNewItem = () => {
    if (!newItemName.trim()) return;

    const newItem: NoteItem = newItemType === 'folder'
      ? {
        id: `folder-${Date.now()}`,
        name: newItemName,
        type: 'folder',
        expanded: true,
        createdAt: new Date(),
        children: [],
      }
      : {
        id: `note-${Date.now()}`,
        name: newItemName,
        type: 'file',
        wordCount: 0,
        createdAt: new Date(),
        updatedAt: new Date(),
      };

    setNotes([...notes, newItem]);
    setNewItemName('');
    setShowNewDialog(false);
    toast.success(`${newItemType === 'folder' ? 'Folder' : 'Note'} created`);
  };

  const deleteItem = (id: string) => {
    setNotes(notes.filter(item => item.id !== id));
    toast.success('Deleted');
  };

  const filteredNotes = notes.filter(item =>
    item.name.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const formatTimeAgo = (date: Date) => {
    const seconds = Math.floor((new Date().getTime() - date.getTime()) / 1000);
    if (seconds < 3600) return `${Math.floor(seconds / 60)}m ago`;
    if (seconds < 86400) return `${Math.floor(seconds / 3600)}h ago`;
    return `${Math.floor(seconds / 86400)}d ago`;
  };

  return (
    <div className="flex flex-col h-full bg-gray-50">
      {/* Header */}
      <div className="p-4 border-b border-gray-200 space-y-3 bg-white">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-semibold flex items-center gap-2">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-amber-500 to-orange-500 flex items-center justify-center">
              <FileText className="w-4 h-4 text-white" />
            </div>
            Notes
          </h2>
          <div className="flex items-center gap-2">
            <button
              onClick={() => setViewMode('grid')}
              className={`p-2 rounded-lg transition-colors ${viewMode === 'grid' ? 'bg-amber-100 text-amber-600' : 'text-gray-400 hover:bg-gray-100'
                }`}
              title="Grid view"
            >
              <LayoutGrid className="w-4 h-4" />
            </button>
            <button
              onClick={() => setViewMode('list')}
              className={`p-2 rounded-lg transition-colors ${viewMode === 'list' ? 'bg-amber-100 text-amber-600' : 'text-gray-400 hover:bg-gray-100'
                }`}
              title="List view"
            >
              <List className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* Action Buttons */}
        <div className="flex gap-2">
          <Button
            size="sm"
            variant="outline"
            onClick={() => {
              setNewItemType('file');
              setShowNewDialog(true);
            }}
            className="flex-1"
          >
            <FilePlus className="w-4 h-4 mr-1" />
            New Note
          </Button>
          <Button
            size="sm"
            variant="outline"
            onClick={() => {
              setNewItemType('folder');
              setShowNewDialog(true);
            }}
            className="flex-1"
          >
            <FolderPlus className="w-4 h-4 mr-1" />
            New Folder
          </Button>
        </div>

        {/* Search */}
        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
          <Input
            placeholder="Search notes..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pl-9"
          />
        </div>
      </div>

      {/* Notes Grid/List */}
      <div className="flex-1 overflow-y-auto p-4">
        {filteredNotes.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-gray-400">
            <div className="w-20 h-20 bg-gray-100 rounded-2xl flex items-center justify-center mb-4">
              <FileText className="w-10 h-10 text-gray-300" />
            </div>
            <p className="text-sm font-medium text-gray-600">
              {searchQuery ? 'No notes found' : 'No notes yet'}
            </p>
            <p className="text-xs text-gray-400 mt-1">
              {searchQuery ? 'Try a different search' : 'Create your first note to get started'}
            </p>
          </div>
        ) : (
          <div className={
            viewMode === 'grid'
              ? 'grid grid-cols-1 gap-3'
              : 'flex flex-col gap-2'
          }>
            {filteredNotes.map((note) => (
              <NoteCard
                key={note.id}
                note={note}
                viewMode={viewMode}
                onOpen={() => note.type === 'file' && onOpenNote?.(note.id)}
                onDelete={() => deleteItem(note.id)}
                formatTimeAgo={formatTimeAgo}
              />
            ))}
          </div>
        )}
      </div>

      {/* New Item Dialog */}
      <Dialog open={showNewDialog} onOpenChange={setShowNewDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>
              Create New {newItemType === 'folder' ? 'Folder' : 'Note'}
            </DialogTitle>
            <DialogDescription>
              Enter a name for your new {newItemType === 'folder' ? 'folder' : 'note'}.
            </DialogDescription>
          </DialogHeader>
          <div className="py-4">
            <Input
              placeholder={`${newItemType === 'folder' ? 'Folder' : 'Note'} name`}
              value={newItemName}
              onChange={(e) => setNewItemName(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter') {
                  createNewItem();
                }
              }}
              autoFocus
            />
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowNewDialog(false)}>
              Cancel
            </Button>
            <Button onClick={createNewItem} disabled={!newItemName.trim()}>
              Create
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}

// Note Card Component
interface NoteCardProps {
  note: NoteItem;
  viewMode: ViewMode;
  onOpen: () => void;
  onDelete: () => void;
  formatTimeAgo: (date: Date) => string;
}

function NoteCard({ note, viewMode, onOpen, onDelete, formatTimeAgo }: NoteCardProps) {
  const [isHovered, setIsHovered] = useState(false);

  if (note.type === 'folder') {
    return (
      <div className="p-4 bg-amber-50 rounded-xl border border-amber-200 hover:border-amber-300 transition-all cursor-pointer">
        <div className="flex items-center gap-3">
          <Folder className="w-8 h-8 text-amber-600" />
          <div className="flex-1">
            <h3 className="text-sm font-semibold text-gray-900">{note.name}</h3>
            <p className="text-xs text-gray-500">Folder</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
      onClick={onOpen}
      className={`
        group bg-white rounded-xl border border-gray-200 transition-all duration-300 cursor-pointer
        ${isHovered ? 'shadow-lg -translate-y-1 border-amber-300' : 'hover:shadow-md'}
        ${viewMode === 'list' ? 'p-3' : 'p-4'}
      `}
    >
      <div className="flex items-start gap-3">
        {/* Icon */}
        <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-amber-100 to-orange-100 flex items-center justify-center shrink-0">
          <FileText className="w-5 h-5 text-amber-600" />
        </div>

        <div className="flex-1 min-w-0">
          {/* Title */}
          <h3 className="text-sm font-semibold text-gray-900 line-clamp-1 mb-1">
            {note.name}
          </h3>

          {/* Metadata */}
          <div className="flex items-center gap-3 text-xs text-gray-500 mb-2">
            <span className="flex items-center gap-1">
              <Clock className="w-3 h-3" />
              {formatTimeAgo(note.updatedAt)}
            </span>
            {note.wordCount && (
              <span>{note.wordCount} words</span>
            )}
          </div>

          {/* Tags (mock) */}
          {viewMode === 'grid' && (
            <div className="flex gap-1 flex-wrap">
              <Badge variant="secondary" className="text-xs">research</Badge>
              <Badge variant="secondary" className="text-xs">draft</Badge>
            </div>
          )}
        </div>

        {/* Actions */}
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button
              variant="ghost"
              size="icon"
              className={`h-8 w-8 shrink-0 transition-opacity ${isHovered ? 'opacity-100' : 'opacity-0'
                }`}
              onClick={(e) => e.stopPropagation()}
            >
              <MoreVertical className="w-4 h-4" />
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end">
            <DropdownMenuItem onClick={(e) => {
              e.stopPropagation();
              toast.success('Added to favorites');
            }}>
              <Star className="w-3 h-3 mr-2" />
              Favorite
            </DropdownMenuItem>
            <DropdownMenuItem onClick={(e) => {
              e.stopPropagation();
              // Edit functionality
            }}>
              <Edit2 className="w-3 h-3 mr-2" />
              Rename
            </DropdownMenuItem>
            <DropdownMenuItem
              onClick={(e) => {
                e.stopPropagation();
                onDelete();
              }}
              className="text-red-600"
            >
              <Trash2 className="w-3 h-3 mr-2" />
              Delete
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>
    </div>
  );
}

