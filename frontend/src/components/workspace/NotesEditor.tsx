import { useState, useRef, useEffect } from 'react';
import {
  Bold, Italic, Underline, Strikethrough,
  List, ListOrdered,
  Heading1, Heading2,
  Quote, Code,
  Link, Image,

  MoreHorizontal,
  Save,
  Clock,
  Eye
} from 'lucide-react';
import { Button } from '../ui/button';
import { Separator } from '../ui/separator';
import { Badge } from '../ui/badge';
// import { toast } from 'sonner';

interface NotesEditorProps {
  noteId?: string;
}

export default function NotesEditor({ noteId }: NotesEditorProps) {
  const [title, setTitle] = useState('Untitled Document');
  const [isTitleEditing, setIsTitleEditing] = useState(false);
  const [wordCount, setWordCount] = useState(0);
  const [lastSaved, setLastSaved] = useState<Date>(new Date());
  const [isFocusMode, setIsFocusMode] = useState(false);
  const contentRef = useRef<HTMLDivElement>(null);

  const execCommand = (command: string, value?: string) => {
    document.execCommand(command, false, value);
    contentRef.current?.focus();
    updateWordCount();
  };

  const updateWordCount = () => {
    if (contentRef.current) {
      const text = contentRef.current.innerText || '';
      const words = text.trim().split(/\s+/).filter(w => w.length > 0);
      setWordCount(words.length);
    }
  };

  // Auto-save simulation
  useEffect(() => {
    const timer = setInterval(() => {
      setLastSaved(new Date());
      // In real app, save to backend here
    }, 30000); // Every 30 seconds

    return () => clearInterval(timer);
  }, []);

  // Reset content when noteId changes
  useEffect(() => {
    if (contentRef.current && noteId) {
      setTitle(`Note: ${noteId}`);
      contentRef.current.innerHTML = `
        <h2>Welcome to your Note</h2>
        <p>Start writing your notes here...</p>
        <p><br /></p>
        <h2>Features</h2>
        <ul>
          <li>Rich text formatting</li>
          <li>Auto-save every 30 seconds</li>
          <li>Word count tracking</li>
          <li>Focus mode for distraction-free writing</li>
        </ul>
      `;
      updateWordCount();
    }
  }, [noteId]);

  const toolbarButtons = [
    { icon: Heading1, command: 'formatBlock', value: '<h1>', label: 'Heading 1', group: 1 },
    { icon: Heading2, command: 'formatBlock', value: '<h2>', label: 'Heading 2', group: 1 },
    { icon: Bold, command: 'bold', label: 'Bold', group: 2 },
    { icon: Italic, command: 'italic', label: 'Italic', group: 2 },
    { icon: Underline, command: 'underline', label: 'Underline', group: 2 },
    { icon: Strikethrough, command: 'strikeThrough', label: 'Strikethrough', group: 2 },
    { icon: List, command: 'insertUnorderedList', label: 'Bullet List', group: 3 },
    { icon: ListOrdered, command: 'insertOrderedList', label: 'Numbered List', group: 3 },
    { icon: Quote, command: 'formatBlock', value: '<blockquote>', label: 'Quote', group: 4 },
    { icon: Code, command: 'formatBlock', value: '<pre>', label: 'Code Block', group: 4 },
  ];

  // Group buttons for visual separation
  const groupedButtons: Record<number, typeof toolbarButtons> = {};
  toolbarButtons.forEach(btn => {
    if (!groupedButtons[btn.group]) groupedButtons[btn.group] = [];
    groupedButtons[btn.group].push(btn);
  });

  const formatTimeAgo = () => {
    const seconds = Math.floor((new Date().getTime() - lastSaved.getTime()) / 1000);
    if (seconds < 60) return 'just now';
    if (seconds < 3600) return `${Math.floor(seconds / 60)}m ago`;
    return lastSaved.toLocaleTimeString();
  };

  return (
    <div className={`h-full flex flex-col bg-white transition-all ${isFocusMode ? 'p-12' : ''}`}>
      {/* Header */}
      {!isFocusMode && (
        <div className="px-6 pt-6 pb-3 border-b border-gray-200">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-amber-500 to-orange-500 flex items-center justify-center">
                <Bold className="w-5 h-5 text-white" />
              </div>
              {isTitleEditing ? (
                <input
                  type="text"
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  onBlur={() => setIsTitleEditing(false)}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter') {
                      setIsTitleEditing(false);
                    }
                  }}
                  className="text-2xl font-bold border-none outline-none bg-transparent"
                  autoFocus
                />
              ) : (
                <h1
                  className="text-2xl font-bold cursor-text hover:text-gray-700 transition-colors"
                  onClick={() => setIsTitleEditing(true)}
                >
                  {title}
                </h1>
              )}
            </div>

            <div className="flex items-center gap-2">
              <Button size="sm" variant="outline" onClick={() => setIsFocusMode(!isFocusMode)}>
                <Eye className="w-4 h-4 mr-2" />
                {isFocusMode ? 'Exit' : 'Focus'}
              </Button>
              <Button size="sm" className="bg-gradient-to-r from-amber-600 to-orange-600 hover:from-amber-700 hover:to-orange-700">
                <Save className="w-4 h-4 mr-2" />
                Save
              </Button>
            </div>
          </div>

          {/* Metadata */}
          <div className="flex items-center gap-4 text-xs text-gray-500">
            <div className="flex items-center gap-1">
              <Clock className="w-3.5 h-3.5" />
              <span>Last saved {formatTimeAgo()}</span>
            </div>
            <div className="flex items-center gap-1">
              <span className="font-medium">{wordCount}</span>
              <span>words</span>
            </div>
            <Badge variant="secondary" className="text-xs">Draft</Badge>
          </div>
        </div>
      )}

      {/* Toolbar */}
      {!isFocusMode && (
        <div className="px-6 py-3 border-b border-gray-200 bg-gray-50">
          <div className="flex items-center gap-1 flex-wrap">
            {Object.keys(groupedButtons).map((groupKey, idx) => (
              <div key={groupKey} className="flex items-center gap-1">
                {groupedButtons[parseInt(groupKey)].map((btn, btnIdx) => (
                  <Button
                    key={btnIdx}
                    variant="ghost"
                    size="sm"
                    onClick={() => {
                      if (btn.command === 'createLink') {
                        const url = prompt('Enter URL:');
                        if (url) execCommand(btn.command, url);
                      } else {
                        execCommand(btn.command, btn.value);
                      }
                    }}
                    title={btn.label}
                    className="h-8 w-8 p-0"
                  >
                    <btn.icon className="w-4 h-4" />
                  </Button>
                ))}
                {idx < Object.keys(groupedButtons).length - 1 && (
                  <Separator orientation="vertical" className="h-6 mx-1" />
                )}
              </div>
            ))}

            <Separator orientation="vertical" className="h-6 mx-1" />

            <Button
              variant="ghost"
              size="sm"
              onClick={() => {
                const url = prompt('Enter image URL:');
                if (url) execCommand('insertImage', url);
              }}
              title="Insert Image"
              className="h-8 w-8 p-0"
            >
              <Image className="w-4 h-4" />
            </Button>

            <Button
              variant="ghost"
              size="sm"
              onClick={() => {
                const url = prompt('Enter link URL:');
                if (url) execCommand('createLink', url);
              }}
              title="Insert Link"
              className="h-8 w-8 p-0"
            >
              <Link className="w-4 h-4" />
            </Button>

            <Button
              variant="ghost"
              size="sm"
              title="More Options"
              className="h-8 w-8 p-0"
            >
              <MoreHorizontal className="w-4 h-4" />
            </Button>
          </div>
        </div>
      )}

      {/* Content Editor */}
      <div className={`flex-1 overflow-y-auto ${isFocusMode ? 'max-w-4xl mx-auto w-full' : 'px-6 py-6'}`}>
        <div
          ref={contentRef}
          contentEditable
          onInput={updateWordCount}
          className={`
            min-h-full outline-none prose prose-slate max-w-none
            ${isFocusMode ? 'prose-lg' : ''}
            focus:outline-none
          `}
          style={{
            caretColor: '#f59e0b'
          }}
          suppressContentEditableWarning
        >
          <p>Start writing your notes here...</p>
          <p><br /></p>
          <h2>Key Points</h2>
          <ul>
            <li>Rich text formatting with toolbar</li>
            <li>Auto-save functionality</li>
            <li>Word count tracking</li>
            <li>Focus mode for distraction-free writing</li>
          </ul>
          <p><br /></p>
          <h2>Research Questions</h2>
          <p>What are the key findings from the literature?</p>
        </div>
      </div>

      {/* Footer Info */}
      {!isFocusMode && (
        <div className="px-6 py-2 border-t border-gray-200 text-xs text-gray-500 flex items-center justify-between bg-gray-50">
          <div className="flex items-center gap-4">
            <span>Note ID: {noteId || 'New note'}</span>
            <span>•</span>
            <span>Created: {new Date().toLocaleDateString()}</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-amber-600 font-medium">⌘S to save</span>
          </div>
        </div>
      )}
    </div>
  );
}

