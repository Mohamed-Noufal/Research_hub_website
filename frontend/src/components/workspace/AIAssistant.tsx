import { useState, useRef, useEffect } from 'react';
import {
  Send, Search, Database, RotateCcw,
  Brain, CheckCircle2, Loader2, ChevronRight,
  FileSearch, Network, BarChart, FileText, GitCompare,
  BookOpen, Lightbulb
} from 'lucide-react';
import { Button } from '../ui/button';
import { Textarea } from '../ui/textarea';
import type { Paper } from '../../App';
// import { toast } from 'sonner';

interface AIAssistantProps {
  papers: Paper[];
}

interface ProcessStep {
  id: string;
  label: string;
  status: 'pending' | 'running' | 'completed';
  tool?: string;
  detail?: string;
}

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  steps?: ProcessStep[];
  agent?: string;
  toolsUsed?: string[];
}

export default function AIAssistant({ papers }: AIAssistantProps) {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: '1',
      role: 'assistant',
      content: `Hello! I'm your AI research assistant. I can help you with:

• Summarizing papers in your library
• Comparing multiple papers
• Finding connections between research
• Literature review assistance
• Analyzing trends and identifying gaps

How can I assist you today?`,
      timestamp: new Date()
    }
  ]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const generateProcessingSteps = (query: string): ProcessStep[] => {
    const lowerQuery = query.toLowerCase();

    if (lowerQuery.includes('summarize') || lowerQuery.includes('summary')) {
      return [
        { id: '1', label: 'Analyzing query context', status: 'pending', tool: 'Query Parser', detail: 'Understanding user intent' },
        { id: '2', label: 'Retrieving papers from library', status: 'pending', tool: 'Database', detail: `Accessing ${papers.length} papers` },
        { id: '3', label: 'Extracting key themes', status: 'pending', tool: 'Text Analysis', detail: 'Identifying topics and patterns' },
        { id: '4', label: 'Generating summary', status: 'pending', tool: 'Language Model', detail: 'Synthesizing insights' }
      ];
    }

    if (lowerQuery.includes('compare')) {
      return [
        { id: '1', label: 'Parsing comparison request', status: 'pending', tool: 'Query Parser', detail: 'Identifying papers to compare' },
        { id: '2', label: 'Loading paper metadata', status: 'pending', tool: 'Database', detail: 'Fetching relevant papers' },
        { id: '3', label: 'Analyzing methodologies', status: 'pending', tool: 'Comparative Analysis', detail: 'Comparing approaches' },
        { id: '4', label: 'Building comparison table', status: 'pending', tool: 'Language Model', detail: 'Structuring results' }
      ];
    }

    if (lowerQuery.includes('literature review') || lowerQuery.includes('review')) {
      return [
        { id: '1', label: 'Understanding scope', status: 'pending', tool: 'Query Parser', detail: 'Defining review parameters' },
        { id: '2', label: 'Categorizing papers', status: 'pending', tool: 'Classification', detail: 'Grouping by methodology' },
        { id: '3', label: 'Chronological analysis', status: 'pending', tool: 'Timeline Analysis', detail: 'Tracking evolution' },
        { id: '4', label: 'Generating framework', status: 'pending', tool: 'Language Model', detail: 'Creating structure' }
      ];
    }

    if (lowerQuery.includes('trend') || lowerQuery.includes('gap')) {
      return [
        { id: '1', label: 'Scanning library', status: 'pending', tool: 'Database', detail: 'Loading all papers' },
        { id: '2', label: 'Topic modeling', status: 'pending', tool: 'ML Analysis', detail: 'Identifying research areas' },
        { id: '3', label: 'Pattern recognition', status: 'pending', tool: 'Statistical Analysis', detail: 'Finding trends' },
        { id: '4', label: 'Synthesizing findings', status: 'pending', tool: 'Language Model', detail: 'Compiling insights' }
      ];
    }

    return [
      { id: '1', label: 'Processing query', status: 'pending', tool: 'Query Parser', detail: 'Understanding request' },
      { id: '2', label: 'Searching library', status: 'pending', tool: 'Database', detail: `Analyzing ${papers.length} papers` },
      { id: '3', label: 'Generating response', status: 'pending', tool: 'Language Model', detail: 'Formulating answer' }
    ];
  };

  const determineAgent = (query: string): string => {
    const lowerQuery = query.toLowerCase();
    if (lowerQuery.includes('summarize') || lowerQuery.includes('summary')) return 'Research Summarizer';
    if (lowerQuery.includes('compare')) return 'Comparative Analyzer';
    if (lowerQuery.includes('literature review')) return 'Review Builder';
    if (lowerQuery.includes('trend') || lowerQuery.includes('gap')) return 'Trend Detector';
    return 'Research Assistant';
  };

  const handleSend = async () => {
    if (!input.trim() || isLoading) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: input,
      timestamp: new Date()
    };

    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setIsLoading(true);

    // Generate processing steps based on query
    const steps = generateProcessingSteps(input);
    const toolsUsed = steps.map(s => s.tool).filter(Boolean) as string[];
    const agent = determineAgent(input);

    // Add assistant message with pending steps
    const assistantMessageId = (Date.now() + 1).toString();
    const assistantMessage: Message = {
      id: assistantMessageId,
      role: 'assistant',
      content: '',
      timestamp: new Date(),
      steps: steps.map(s => ({ ...s, status: 'pending' as const })),
      agent,
      toolsUsed
    };

    setMessages(prev => [...prev, assistantMessage]);

    // Simulate step-by-step processing
    for (let i = 0; i < steps.length; i++) {
      await new Promise(resolve => setTimeout(resolve, 800));

      setMessages(prev => prev.map(msg => {
        if (msg.id === assistantMessageId && msg.steps) {
          const updatedSteps = [...msg.steps];
          updatedSteps[i] = { ...updatedSteps[i], status: 'running' };
          return { ...msg, steps: updatedSteps };
        }
        return msg;
      }));

      await new Promise(resolve => setTimeout(resolve, 1200));

      setMessages(prev => prev.map(msg => {
        if (msg.id === assistantMessageId && msg.steps) {
          const updatedSteps = [...msg.steps];
          updatedSteps[i] = { ...updatedSteps[i], status: 'completed' };
          return { ...msg, steps: updatedSteps };
        }
        return msg;
      }));
    }

    // Add final response
    await new Promise(resolve => setTimeout(resolve, 500));
    setMessages(prev => prev.map(msg => {
      if (msg.id === assistantMessageId) {
        return { ...msg, content: generateMockResponse(input, papers) };
      }
      return msg;
    }));

    setIsLoading(false);
  };

  const generateMockResponse = (query: string, papers: Paper[]): string => {
    const lowerQuery = query.toLowerCase();

    if (lowerQuery.includes('summarize') || lowerQuery.includes('summary')) {
      return `Based on your library of ${papers.length} papers, here are the key themes:

**Main Topics:**
• Machine Learning - Dominant focus area
• Neural Networks - Recent architectures
• Optimization - Efficiency improvements

**Key Insights:**
1. Recent work focuses on model compression
2. Several papers explore novel attention mechanisms
3. Cross-domain applications are emerging

Would you like me to provide a detailed summary of a specific paper?`;
    }

    if (lowerQuery.includes('compare')) {
      return `I can help you compare papers. Key differences I notice:

**Architecture:** Novel vs. traditional approaches
**Performance:** Speed vs. accuracy tradeoffs
**Use Cases:** Theoretical vs. applied focus

Which specific papers would you like me to compare in detail?`;
    }

    if (lowerQuery.includes('literature review')) {
      return `Here's a recommended structure for your literature review:

**1. Methodology Grouping**
Supervised vs. unsupervised approaches
Traditional vs. deep learning methods

**2. Chronological Analysis**
Evolution of key ideas (2020 → 2024)
Emerging trends

**3. Gap Analysis**
Under-explored areas
Future research directions

Shall I help you create a detailed outline?`;
    }

    if (lowerQuery.includes('trend') || lowerQuery.includes('gap')) {
      return `Based on analysis of your library:

**Emerging Trends:**
• Focus on efficiency and model compression
• Integration of multimodal approaches
• Increased attention to interpretability

**Research Gaps:**
• Limited work on edge deployment
• Under-explored domain adaptation techniques
• Need for more robust evaluation metrics`;
    }

    return `Based on your ${papers.length} saved papers, I can provide insights into:

• Methodologies used
• Key findings
• Research connections

Could you be more specific about what aspect you'd like to explore?`;
  };

  const getToolIcon = (tool: string) => {
    if (tool?.includes('Parser')) return Search;
    if (tool?.includes('Database')) return Database;
    if (tool?.includes('Analysis')) return BarChart;
    if (tool?.includes('Language Model')) return Brain;
    if (tool?.includes('Classification')) return Network;
    return FileSearch;
  };

  const quickActions = [
    { icon: FileText, label: 'Summarize library', action: 'Summarize all papers in my library' },
    { icon: GitCompare, label: 'Compare papers', action: 'Compare the methodologies in my saved papers' },
    { icon: BookOpen, label: 'Literature review', action: 'Help me structure a literature review' },
    { icon: Lightbulb, label: 'Research gaps', action: 'What research gaps can you identify?' },
  ];

  return (
    <div className="h-full flex flex-col bg-white">
      {/* Messages - Full Width */}
      <div className="flex-1 overflow-y-auto px-4 py-6 space-y-6">
        {messages.map((message, index) => (
          <div key={message.id} className="space-y-4">
            {/* User Message */}
            {message.role === 'user' && (
              <div className="flex items-start gap-3">
                <div className="flex-1">
                  <div className="bg-gray-100 rounded-lg px-4 py-3 max-w-2xl">
                    <p className="text-gray-900 whitespace-pre-wrap">{message.content}</p>
                  </div>
                </div>
                <button className="p-1.5 text-gray-400 hover:text-gray-600" title="Undo">
                  <RotateCcw className="w-4 h-4" />
                </button>
              </div>
            )}

            {/* Assistant Message */}
            {message.role === 'assistant' && (
              <div className="space-y-3">
                {/* Agent Badge */}
                {message.agent && index > 0 && (
                  <div className="flex items-center gap-2">
                    <div className="inline-flex items-center gap-1.5 px-2 py-0.5 bg-gray-100 rounded text-xs text-gray-600">
                      <CheckCircle2 className="w-3 h-3" />
                      <span>{message.agent}</span>
                    </div>
                  </div>
                )}

                {/* Processing Steps */}
                {message.steps && message.steps.length > 0 && (
                  <div className="space-y-2">
                    {message.steps.map((step) => {
                      const IconComponent = getToolIcon(step.tool || '');
                      return (
                        <div
                          key={step.id}
                          className="flex items-start gap-2.5"
                        >
                          {/* Step Status Icon */}
                          <div className="mt-0.5">
                            {step.status === 'completed' && (
                              <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                            )}
                            {step.status === 'running' && (
                              <Loader2 className="w-4 h-4 text-blue-600 animate-spin" />
                            )}
                            {step.status === 'pending' && (
                              <div className="w-4 h-4 rounded-full border-2 border-gray-300" />
                            )}
                          </div>

                          {/* Step Content */}
                          <div className="flex-1">
                            <div className={`text-sm ${step.status === 'completed' ? 'text-gray-900' :
                              step.status === 'running' ? 'text-gray-900' :
                                'text-gray-400'
                              }`}>
                              {step.label}
                            </div>

                            {/* Tool Badge */}
                            {step.tool && step.status !== 'pending' && (
                              <div className="flex items-center gap-2 mt-1">
                                <div className="inline-flex items-center gap-1 text-xs text-gray-500">
                                  <IconComponent className="w-3 h-3" />
                                  <span>{step.tool}</span>
                                </div>
                                {step.detail && (
                                  <>
                                    <ChevronRight className="w-3 h-3 text-gray-400" />
                                    <span className="text-xs text-gray-400">{step.detail}</span>
                                  </>
                                )}
                              </div>
                            )}
                          </div>
                        </div>
                      );
                    })}
                  </div>
                )}

                {/* Tools Used Summary */}
                {message.toolsUsed && message.toolsUsed.length > 0 && message.content && (
                  <div className="flex items-center gap-2 flex-wrap">
                    {message.toolsUsed.map((tool, i) => {
                      const IconComponent = getToolIcon(tool);
                      return (
                        <div
                          key={i}
                          className="inline-flex items-center gap-1 px-2 py-0.5 bg-gray-100 rounded text-xs text-gray-600"
                        >
                          <IconComponent className="w-3 h-3" />
                          <span>{tool}</span>
                        </div>
                      );
                    })}
                  </div>
                )}

                {/* Message Content - No Background */}
                {message.content && (
                  <div className="text-gray-900 space-y-3 leading-relaxed">
                    {message.content.split('\n').map((line, i) => {
                      // Bold headers
                      if (line.startsWith('**') && line.endsWith('**')) {
                        return (
                          <div key={i} className="text-gray-900 font-semibold mt-4 first:mt-0">
                            {line.replace(/\*\*/g, '')}
                          </div>
                        );
                      }
                      // Bullet points
                      if (line.startsWith('• ')) {
                        return (
                          <div key={i} className="flex items-start gap-2">
                            <span className="text-gray-400 mt-0.5">•</span>
                            <span className="flex-1 text-gray-700">{line.replace('• ', '')}</span>
                          </div>
                        );
                      }
                      // Numbered lists
                      if (line.match(/^\d+\./)) {
                        return <div key={i} className="ml-4 text-gray-700">{line}</div>;
                      }
                      // Regular paragraphs
                      return line.trim() ? (
                        <p key={i} className="text-gray-700 first:mt-0">
                          {line}
                        </p>
                      ) : (
                        <br key={i} />
                      );
                    })}
                  </div>
                )}
              </div>
            )}
          </div>
        ))}

        {/* Loading indicator */}
        {isLoading && (
          <div className="flex items-center gap-2">
            <div className="flex gap-1">
              <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" />
              <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }} />
              <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.4s' }} />
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Quick Actions - Only show when empty */}
      {messages.length <= 1 && (
        <div className="px-4 pb-4">
          <div className="grid grid-cols-2 gap-2">
            {quickActions.map((action, index) => (
              <button
                key={index}
                onClick={() => setInput(action.action)}
                className="flex items-center gap-2 px-3 py-2.5 bg-gray-50 hover:bg-gray-100 text-gray-700 rounded-lg text-sm transition-colors text-left border border-gray-200"
              >
                <action.icon className="w-4 h-4 text-gray-500 flex-shrink-0" />
                <span className="flex-1">{action.label}</span>
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Input */}
      <div className="px-4 pb-4">
        <div className="flex items-end gap-2">
          <div className="flex-1 bg-gray-50 rounded-lg border border-gray-200 focus-within:border-gray-300 focus-within:bg-white transition-colors">
            <Textarea
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                  e.preventDefault();
                  handleSend();
                }
              }}
              placeholder="Ask anything (Ctrl+L), @ to mention, / for workflows"
              className="resize-none min-h-[52px] bg-transparent border-0 text-gray-900 placeholder:text-gray-400 focus-visible:ring-0 focus-visible:ring-offset-0"
            />
          </div>
          <Button
            onClick={handleSend}
            disabled={!input.trim() || isLoading}
            className="h-[52px] w-[52px] p-0 bg-gray-900 hover:bg-gray-800 text-white rounded-lg disabled:opacity-50 disabled:hover:bg-gray-900"
          >
            <Send className="w-4 h-4" />
          </Button>
        </div>
        <div className="flex items-center gap-3 mt-2 text-xs text-gray-500">
          <div className="flex items-center gap-1">
            <div className="w-2 h-2 rounded-full bg-emerald-500" />
            <span>Planning</span>
          </div>
          <div className="flex items-center gap-1">
            <ChevronRight className="w-3 h-3" />
            <span>Research Assistant v4.5</span>
          </div>
        </div>
      </div>
    </div>
  );
}
