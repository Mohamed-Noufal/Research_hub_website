import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from './ui/dialog';
import { Badge } from './ui/badge';
import { Keyboard, Search, FileText, Layout, Zap } from 'lucide-react';

interface KeyboardShortcutsModalProps {
  isOpen: boolean;
  onClose: () => void;
}

const shortcuts = [
  {
    category: 'Global',
    icon: Zap,
    items: [
      { keys: ['⌘', 'K'], description: 'Quick search' },
      { keys: ['⌘', 'B'], description: 'Toggle sidebar' },
      { keys: ['⌘', '/'], description: 'Show keyboard shortcuts' },
      { keys: ['ESC'], description: 'Close modals/panels' },
    ],
  },
  {
    category: 'Search',
    icon: Search,
    items: [
      { keys: ['⌘', 'Enter'], description: 'Execute search' },
      { keys: ['↑', '↓'], description: 'Navigate results' },
      { keys: ['Enter'], description: 'Open selected paper' },
      { keys: ['S'], description: 'Save/unsave paper' },
    ],
  },
  {
    category: 'Workspace',
    icon: Layout,
    items: [
      { keys: ['⌘', 'N'], description: 'New note' },
      { keys: ['⌘', 'S'], description: 'Save current work' },
      { keys: ['⌘', 'F'], description: 'Find in document' },
      { keys: ['⌘', '1-4'], description: 'Switch panels' },
    ],
  },
  {
    category: 'Editor',
    icon: FileText,
    items: [
      { keys: ['⌘', 'B'], description: 'Bold text' },
      { keys: ['⌘', 'I'], description: 'Italic text' },
      { keys: ['⌘', 'K'], description: 'Insert link' },
      { keys: ['⌘', 'Z'], description: 'Undo' },
      { keys: ['⌘', '⇧', 'Z'], description: 'Redo' },
    ],
  },
];

export default function KeyboardShortcutsModal({ isOpen, onClose }: KeyboardShortcutsModalProps) {
  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="max-w-3xl max-h-[80vh] overflow-y-auto">
        <DialogHeader>
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-blue-100 flex items-center justify-center">
              <Keyboard className="w-5 h-5 text-blue-600" />
            </div>
            <div>
              <DialogTitle className="text-2xl">Keyboard Shortcuts</DialogTitle>
              <DialogDescription>
                Boost your productivity with these keyboard shortcuts
              </DialogDescription>
            </div>
          </div>
        </DialogHeader>

        <div className="grid gap-8 mt-6">
          {shortcuts.map((section) => {
            const Icon = section.icon;
            return (
              <div key={section.category}>
                <div className="flex items-center gap-2 mb-4">
                  <Icon className="w-5 h-5 text-gray-600" />
                  <h3 className="text-lg font-semibold">{section.category}</h3>
                </div>
                <div className="space-y-3">
                  {section.items.map((item, index) => (
                    <div
                      key={index}
                      className="flex items-center justify-between p-3 rounded-lg hover:bg-gray-50 transition-colors"
                    >
                      <span className="text-gray-700">{item.description}</span>
                      <div className="flex items-center gap-1">
                        {item.keys.map((key, keyIndex) => (
                          <span key={keyIndex} className="flex items-center gap-1">
                            <Badge
                              variant="secondary"
                              className="px-2 py-1 font-mono text-xs bg-white border border-gray-300 shadow-sm"
                            >
                              {key}
                            </Badge>
                            {keyIndex < item.keys.length - 1 && (
                              <span className="text-gray-400 text-xs">+</span>
                            )}
                          </span>
                        ))}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            );
          })}
        </div>

        <div className="mt-6 p-4 bg-blue-50 rounded-lg border border-blue-200">
          <p className="text-sm text-blue-900">
            <strong>Tip:</strong> Press <Badge variant="secondary" className="mx-1 px-2 py-0.5 text-xs">?</Badge> 
            anywhere in the app to open this shortcuts guide.
          </p>
        </div>
      </DialogContent>
    </Dialog>
  );
}
