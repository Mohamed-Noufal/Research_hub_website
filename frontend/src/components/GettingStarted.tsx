import { BookOpen, Search, BookmarkPlus, FileText, Bot, LibraryBig, Download, CheckCircle2 } from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Badge } from './ui/badge';
import { Button } from './ui/button';

interface GettingStartedProps {
  onClose: () => void;
  onNavigate?: (section: string) => void;
}

export default function GettingStarted({ onClose, onNavigate }: GettingStartedProps) {
  const steps = [
    {
      title: 'Search for Papers',
      description: 'Start by searching across arXiv, Semantic Scholar, and OpenAlex databases. Use categories to narrow your search.',
      icon: Search,
      color: 'blue',
      actions: [
        'Select a research category',
        'Enter your search query',
        'Review the results with smart filters',
      ],
      tip: 'Use quotes for exact phrases and - to exclude terms',
    },
    {
      title: 'Save to Your Library',
      description: 'Build your personal research library by saving papers you find interesting or relevant to your work.',
      icon: BookmarkPlus,
      color: 'purple',
      actions: [
        'Click the bookmark icon on any paper',
        'Access saved papers in your workspace',
        'Upload your own PDF files',
      ],
      tip: 'Papers are saved locally in your browser',
    },
    {
      title: 'Open Workspace',
      description: 'Your workspace is a flexible environment for reading, note-taking, and organizing your research.',
      icon: LibraryBig,
      color: 'green',
      actions: [
        'View your saved papers library',
        'Read papers in the viewer',
        'Create and organize notes',
      ],
      tip: 'Resize panels to customize your layout',
    },
    {
      title: 'Take Smart Notes',
      description: 'Create structured notes linked to papers. Use Notion-like editing to organize your thoughts.',
      icon: FileText,
      color: 'orange',
      actions: [
        'Create notes for each paper',
        'Use markdown formatting',
        'Link notes to specific papers',
      ],
      tip: 'Notes are auto-saved as you type',
    },
    {
      title: 'Use AI Assistant',
      description: 'Get help understanding papers, comparing research, and identifying key insights with AI.',
      icon: Bot,
      color: 'pink',
      actions: [
        'Ask questions about papers',
        'Request summaries',
        'Compare multiple papers',
      ],
      tip: 'Be specific in your questions for better answers',
    },
    {
      title: 'Manage Citations',
      description: 'Generate properly formatted citations in APA, MLA, Chicago, or IEEE style for your papers.',
      icon: Download,
      color: 'indigo',
      actions: [
        'Select papers to cite',
        'Choose your citation style',
        'Copy or export citations',
      ],
      tip: 'You can edit citations in the table view',
    },
  ];

  const colorClasses = {
    blue: 'bg-blue-100 text-blue-600',
    purple: 'bg-purple-100 text-purple-600',
    green: 'bg-green-100 text-green-600',
    orange: 'bg-orange-100 text-orange-600',
    pink: 'bg-pink-100 text-pink-600',
    indigo: 'bg-indigo-100 text-indigo-600',
  };

  return (
    <div className="max-w-6xl mx-auto px-6 py-8">
      {/* Header */}
      <div className="text-center mb-12">
        <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-gradient-to-br from-blue-500 to-purple-600 mb-4">
          <BookOpen className="w-8 h-8 text-white" />
        </div>
        <h1 className="text-4xl mb-4">Getting Started with ResearchHub</h1>
        <p className="text-xl text-gray-600 max-w-2xl mx-auto">
          Your complete guide to becoming productive with ResearchHub in minutes
        </p>
      </div>

      {/* Quick Start Steps */}
      <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6 mb-12">
        {steps.map((step, index) => {
          const Icon = step.icon;
          return (
            <Card key={index} className="hover:shadow-lg transition-shadow">
              <CardHeader>
                <div className="flex items-start justify-between mb-3">
                  <div className={`w-12 h-12 rounded-lg ${colorClasses[step.color as keyof typeof colorClasses]} flex items-center justify-center`}>
                    <Icon className="w-6 h-6" />
                  </div>
                  <Badge variant="secondary">{index + 1}</Badge>
                </div>
                <CardTitle className="text-xl">{step.title}</CardTitle>
                <CardDescription>{step.description}</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-2 mb-4">
                  {step.actions.map((action, actionIndex) => (
                    <div key={actionIndex} className="flex items-start gap-2">
                      <CheckCircle2 className="w-4 h-4 text-green-600 mt-0.5 flex-shrink-0" />
                      <span className="text-sm text-gray-700">{action}</span>
                    </div>
                  ))}
                </div>
                <div className="p-3 bg-gray-50 rounded-lg border border-gray-200">
                  <p className="text-xs text-gray-600">
                    <strong>💡 Tip:</strong> {step.tip}
                  </p>
                </div>
              </CardContent>
            </Card>
          );
        })}
      </div>

      {/* Features Overview */}
      <div className="mb-12">
        <h2 className="text-3xl mb-6 text-center">Key Features</h2>
        <div className="grid md:grid-cols-2 gap-6">
          <Card>
            <CardHeader>
              <CardTitle>🔍 Multi-Database Search</CardTitle>
              <CardDescription>
                Search across millions of papers from arXiv, Semantic Scholar, and OpenAlex simultaneously
              </CardDescription>
            </CardHeader>
            <CardContent>
              <ul className="space-y-2 text-sm text-gray-700">
                <li>• Category-based filtering for precise results</li>
                <li>• Advanced filters for citations, year, and source</li>
                <li>• Smart sorting by relevance, date, or citations</li>
              </ul>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>📚 Flexible Workspace</CardTitle>
              <CardDescription>
                Customize your research environment with resizable panels and multiple views
              </CardDescription>
            </CardHeader>
            <CardContent>
              <ul className="space-y-2 text-sm text-gray-700">
                <li>• Resize panels to fit your workflow</li>
                <li>• Collapsible sidebar for more space</li>
                <li>• Switch between library, viewer, notes, and AI</li>
              </ul>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>✍️ Smart Note-Taking</CardTitle>
              <CardDescription>
                Capture your thoughts with a powerful notes editor linked to your papers
              </CardDescription>
            </CardHeader>
            <CardContent>
              <ul className="space-y-2 text-sm text-gray-700">
                <li>• Create unlimited notes per paper</li>
                <li>• Auto-save prevents data loss</li>
                <li>• Rich text formatting support</li>
              </ul>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>🤖 AI Research Assistant</CardTitle>
              <CardDescription>
                Get intelligent help understanding papers and organizing your research
              </CardDescription>
            </CardHeader>
            <CardContent>
              <ul className="space-y-2 text-sm text-gray-700">
                <li>• Summarize complex papers quickly</li>
                <li>• Compare multiple papers side-by-side</li>
                <li>• Get explanations of methodologies</li>
              </ul>
            </CardContent>
          </Card>
        </div>
      </div>

      {/* Pro Tips */}
      <div className="mb-12">
        <h2 className="text-3xl mb-6 text-center">Pro Tips</h2>
        <div className="grid md:grid-cols-2 gap-4">
          <div className="p-6 bg-gradient-to-br from-blue-50 to-blue-100 rounded-xl border border-blue-200">
            <h3 className="font-semibold mb-2 text-lg">⌨️ Keyboard Shortcuts</h3>
            <p className="text-sm text-gray-700">
              Press <kbd className="px-2 py-1 bg-white rounded border text-xs">?</kbd> anywhere to see all keyboard shortcuts. 
              Use <kbd className="px-2 py-1 bg-white rounded border text-xs">⌘K</kbd> for quick search.
            </p>
          </div>

          <div className="p-6 bg-gradient-to-br from-purple-50 to-purple-100 rounded-xl border border-purple-200">
            <h3 className="font-semibold mb-2 text-lg">💾 Local Storage</h3>
            <p className="text-sm text-gray-700">
              All your data is stored locally in your browser. Nothing is sent to servers. 
              Export regularly to back up your work.
            </p>
          </div>

          <div className="p-6 bg-gradient-to-br from-green-50 to-green-100 rounded-xl border border-green-200">
            <h3 className="font-semibold mb-2 text-lg">📤 PDF Upload</h3>
            <p className="text-sm text-gray-700">
              Upload your own PDFs in the saved papers section. 
              Organize all your research in one place, even papers not in the databases.
            </p>
          </div>

          <div className="p-6 bg-gradient-to-br from-orange-50 to-orange-100 rounded-xl border border-orange-200">
            <h3 className="font-semibold mb-2 text-lg">📋 Citation Formats</h3>
            <p className="text-sm text-gray-700">
              Switch between APA, MLA, Chicago, and IEEE citation styles instantly. 
              The literature review table is fully editable.
            </p>
          </div>
        </div>
      </div>

      {/* Quick Actions */}
      <div className="text-center p-8 bg-gradient-to-br from-blue-600 to-purple-600 rounded-xl text-white">
        <h2 className="text-3xl mb-4">Ready to Start?</h2>
        <p className="text-xl mb-6 text-blue-100">
          Begin your research journey with these quick actions
        </p>
        <div className="flex gap-4 justify-center flex-wrap">
          <Button 
            size="lg" 
            className="bg-white text-blue-600 hover:bg-gray-100"
            onClick={onClose}
          >
            Start Searching Papers
          </Button>
          <Button 
            size="lg" 
            variant="outline" 
            className="border-white text-white hover:bg-white/20"
            onClick={() => onNavigate?.('blog')}
          >
            Read Our Blog
          </Button>
        </div>
      </div>

      {/* FAQ Section */}
      <div className="mt-12">
        <h2 className="text-3xl mb-6 text-center">Frequently Asked Questions</h2>
        <div className="space-y-4 max-w-3xl mx-auto">
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Is my data private?</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-gray-700">
                Yes! All your papers, notes, and workspace data are stored locally in your browser. 
                Nothing is sent to external servers. You have complete control over your data.
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Can I export my citations?</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-gray-700">
                Absolutely! You can copy citations in APA, MLA, Chicago, or IEEE format directly from the literature review section. 
                The citations are formatted according to the latest style guidelines.
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="text-lg">How do I customize my workspace?</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-gray-700">
                Click and drag the panel dividers to resize sections. Toggle the sidebar using the button in the header. 
                Your layout preferences are saved automatically.
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Can I use this offline?</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-gray-700">
                Once you've loaded papers and created notes, you can access them offline. 
                However, searching for new papers requires an internet connection.
              </p>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
