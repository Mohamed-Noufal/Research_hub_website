
import { useState, useRef, useEffect } from 'react';
import {
  Brain, CheckCircle2, Loader2,
  Plus, ArrowRight, Sparkles, ChevronDown
} from 'lucide-react';
import { Button } from '../ui/button';
import { Textarea } from '../ui/textarea';
import type { Paper } from '../../App';
import ReconnectingWebSocket from 'reconnecting-websocket';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "../ui/dropdown-menu";
import { Badge } from "../ui/badge";
import PaperPicker from './PaperPicker';

// Available LLM Models
const AVAILABLE_MODELS = [
  { id: 'groq/qwen3-32b', name: 'Qwen 32B', provider: 'Groq', tier: 'free', isDefault: true },
  { id: 'groq/llama-3.1-70b', name: 'Llama 3.1 70B', provider: 'Groq', tier: 'free' },
  { id: 'together/qwen3-235b', name: 'Qwen3 235B', provider: 'Together', tier: 'balanced', badge: 'Best Value' },
  { id: 'together/llama-3.1-70b', name: 'Llama 3.1 70B', provider: 'Together', tier: 'balanced' },
  { id: 'openai/gpt-5-nano', name: 'GPT-5 Nano', provider: 'OpenAI', tier: 'budget' },
  { id: 'openai/gpt-5-mini', name: 'GPT-5 Mini', provider: 'OpenAI', tier: 'balanced' },
  { id: 'openai/gpt-5.1', name: 'GPT-5.1', provider: 'OpenAI', tier: 'premium', badge: 'Best Quality' },
  { id: 'google/gemini-3-flash', name: 'Gemini 3 Flash', provider: 'Google', tier: 'budget', badge: '1M Context' },
];

interface AIAssistantProps {
  papers: Paper[];
  projectId?: string | number;
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
  isError?: boolean;
}

const API_BASE_URL = 'http://localhost:8000/api/v1';
const WS_BASE_URL = 'ws://localhost:8000/api/v1/agent/ws';

export default function AIAssistant({ papers, projectId }: AIAssistantProps) {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: 'welcome',
      role: 'assistant',
      content: '', // Empty content for welcome state logic
      timestamp: new Date()
    }
  ]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [conversationId, setConversationId] = useState<string | null>(null);
  // Check both localStorage keys for backwards compatibility
  const [userId, setUserId] = useState<string | null>(() =>
    localStorage.getItem('userId') || localStorage.getItem('paper-search-user-uuid-v1')
  );

  const [scope, setScope] = useState<'project' | 'library' | 'selection'>('project');
  const [selectedPaperIds, setSelectedPaperIds] = useState<string[]>([]);
  const [isPickerOpen, setIsPickerOpen] = useState(false);

  // Model selection state
  const [selectedModel, setSelectedModel] = useState(() =>
    localStorage.getItem('ai-selected-model') || 'groq/qwen3-32b'
  );

  // Auto-open picker when selection scope is chosen
  const handleScopeChange = (val: 'project' | 'library' | 'selection') => {
    setScope(val);
    if (val === 'selection' && selectedPaperIds.length === 0) {
      setIsPickerOpen(true);
    }
  };

  // Save model selection to localStorage
  const handleModelChange = (modelId: string) => {
    setSelectedModel(modelId);
    localStorage.setItem('ai-selected-model', modelId);
  };

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const wsRef = useRef<ReconnectingWebSocket | null>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // User Initialization
  useEffect(() => {
    const initUser = async () => {
      if (!userId) {
        try {
          const res = await fetch(`${API_BASE_URL}/users/init`, { method: 'POST' });
          const data = await res.json();
          setUserId(data.user_id);
          // Store in both keys for backwards compatibility
          localStorage.setItem('userId', data.user_id);
          localStorage.setItem('paper-search-user-uuid-v1', data.user_id);
        } catch (err) {
          console.error("Failed to init user", err);
        }
      }
    };
    initUser();
  }, [userId]);

  // Initial Conversation Setup
  useEffect(() => {
    const initConversation = async () => {
      if (!userId) return; // Wait for user ID

      try {
        if (!conversationId) {
          const res = await fetch(`${API_BASE_URL}/agent/conversations`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              user_id: userId,
              project_id: projectId ? Number(projectId) : null,
              title: 'New Chat'
            })
          });
          const data = await res.json();
          setConversationId(data.id);
        }
      } catch (err) {
        console.error("Failed to init conversation", err);
      }
    };
    initConversation();
  }, [userId, projectId]);

  // WebSocket Connection
  useEffect(() => {
    if (!conversationId || !userId) return;

    const wsUrl = `${WS_BASE_URL}/${conversationId}?user_id=${userId}`;
    const ws = new ReconnectingWebSocket(wsUrl);
    wsRef.current = ws;

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      handleWsMessage(data);
    };

    ws.onopen = () => {
      console.log("WebSocket connected");
    };

    return () => {
      ws.close();
    };
  }, [conversationId, userId]);

  const handleWsMessage = (data: any) => {
    setMessages(prev => {
      const lastMsg = prev[prev.length - 1];
      const isAssistant = lastMsg?.role === 'assistant';

      if (data.type === 'thinking') {
        if (isAssistant && lastMsg.content === '') {
          const newSteps = lastMsg.steps || [];
          newSteps.push({
            id: `think-${data.step}`,
            label: data.message || 'Analyzing your request...',
            status: 'running',
          });
          return prev.map(m => m.id === lastMsg.id ? { ...m, steps: newSteps } : m);
        }
        return prev;
      }

      if (data.type === 'tool_selected') {
        if (isAssistant) {
          let newSteps = [...(lastMsg.steps || [])];
          newSteps = newSteps.map(s => s.status === 'running' ? { ...s, status: 'completed' } : s);
          newSteps.push({
            id: `tool-${data.step}`,
            label: `Using: ${data.tool}`,
            status: 'running',
            tool: data.tool,
            detail: JSON.stringify(data.parameters, null, 2)
          });

          let newTools = lastMsg.toolsUsed || [];
          if (!newTools.includes(data.tool)) {
            newTools.push(data.tool);
          }

          return prev.map(m => m.id === lastMsg.id ? { ...m, steps: newSteps, toolsUsed: newTools } : m);
        }
        return prev;
      }

      // ... other message types ...
      if (data.type === 'tool_executing') {
        if (isAssistant) {
          const newSteps = (lastMsg.steps || []).map(s =>
            s.tool === data.tool && s.status === 'running'
              ? { ...s, label: `Executing: ${data.tool}...` }
              : s
          );
          return prev.map(m => m.id === lastMsg.id ? { ...m, steps: newSteps } : m);
        }
        return prev;
      }

      if (data.type === 'tool_result') {
        if (isAssistant) {
          const newSteps = (lastMsg.steps || []).map(s =>
            s.tool === data.tool && s.status === 'running'
              ? { ...s, status: 'completed' as const, label: `✓ ${data.tool}`, detail: typeof data.result === 'string' ? data.result : JSON.stringify(data.result).substring(0, 100) }
              : s
          );
          return prev.map(m => m.id === lastMsg.id ? { ...m, steps: newSteps } : m);
        }
        return prev;
      }

      if (data.type === 'tool_error') {
        if (isAssistant) {
          const newSteps = (lastMsg.steps || []).map(s =>
            s.tool === data.tool
              ? { ...s, status: 'completed' as const, label: `✗ ${data.tool} failed`, detail: data.error }
              : s
          );
          return prev.map(m => m.id === lastMsg.id ? { ...m, steps: newSteps } : m);
        }
        return prev;
      }

      if (data.type === 'synthesizing') {
        if (isAssistant) {
          let newSteps = [...(lastMsg.steps || [])];
          newSteps = newSteps.map(s => s.status === 'running' ? { ...s, status: 'completed' } : s);
          newSteps.push({
            id: 'synthesize',
            label: data.message || 'Generating final answer...',
            status: 'running',
          });
          return prev.map(m => m.id === lastMsg.id ? { ...m, steps: newSteps } : m);
        }
        return prev;
      }

      if (data.type === 'message') {
        if (isAssistant) {
          let newSteps = (lastMsg.steps || []).map(s => ({ ...s, status: 'completed' as const }));
          return prev.map(m => m.id === lastMsg.id ? { ...m, content: data.content || '', steps: newSteps } : m);
        }
        return prev;
      }

      if (data.type === 'message_end') {
        setIsLoading(false);
        return prev;
      }

      if (data.type === 'error') {
        setIsLoading(false);
        if (isAssistant) {
          return prev.map(m => m.id === lastMsg.id ? { ...m, content: data.message || data.content, isError: true } : m);
        }
        return [...prev, {
          id: Date.now().toString(),
          role: 'assistant',
          content: data.message || data.content || 'An error occurred',
          timestamp: new Date(),
          isError: true
        }];
      }

      return prev;
    });
  };

  const handleSend = async () => {
    if (!input.trim() || isLoading || !wsRef.current) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: input,
      timestamp: new Date()
    };

    setMessages(prev => [...prev, userMessage]);

    const assistantMsgId = (Date.now() + 1).toString();
    const assistantPlaceholder: Message = {
      id: assistantMsgId,
      role: 'assistant',
      content: '',
      timestamp: new Date(),
      steps: [],
    };
    setMessages(prev => [...prev, assistantPlaceholder]);

    setInput('');
    setIsLoading(true);

    wsRef.current.send(JSON.stringify({
      message: input,
      project_id: projectId ? Number(projectId) : null,
      user_id: userId,
      scope: scope,
      model_id: selectedModel,
      // Convert paper IDs to integers for backend compatibility
      selected_paper_ids: scope === 'selection' ? selectedPaperIds.map(id => parseInt(id, 10)) : []
    }));
  };

  const hasStartedConversation = messages.length > 1;

  return (
    <div className="h-full relative flex flex-col bg-white">
      {/* Paper Picker Modal */}
      <PaperPicker
        papers={papers}
        selectedIds={selectedPaperIds}
        onSelectionChange={setSelectedPaperIds}
        open={isPickerOpen}
        onOpenChange={setIsPickerOpen}
        limit={7}
      />

      {/* Messages / Welcome State */}
      <div className={`flex-1 overflow-y-auto px-4 py-6 space-y-6 pb-32 ${!hasStartedConversation ? 'flex flex-col justify-center items-center' : ''}`}>

        {!hasStartedConversation ? (
          <div className="text-center space-y-4 max-w-lg mx-auto mb-20">
            <div className="w-12 h-12 bg-gray-100 rounded-2xl flex items-center justify-center mx-auto mb-6">
              <Brain className="w-6 h-6 text-gray-900" />
            </div>
            <h2 className="text-2xl font-semibold text-gray-900">How can I help you?</h2>
          </div>
        ) : (
          messages.filter(m => m.content || m.steps?.length || m.role === 'user').map((message, index) => (
            <div key={message.id} className="w-full max-w-3xl mx-auto space-y-4">
              {/* User Message */}
              {message.role === 'user' && (
                <div className="flex justify-end">
                  <div className="bg-gray-100 text-gray-900 rounded-2xl px-5 py-3 max-w-[85%]">
                    <p className="whitespace-pre-wrap leading-relaxed">{message.content}</p>
                  </div>
                </div>
              )}

              {/* Assistant Message */}
              {message.role === 'assistant' && (
                <div className="flex gap-4">
                  <div className="w-8 h-8 rounded-full bg-white border border-gray-200 flex items-center justify-center shrink-0 mt-1 shadow-sm">
                    <Brain className="w-4 h-4 text-gray-700" />
                  </div>
                  <div className="flex-1 space-y-4 min-w-0">
                    {/* Steps / Thinking */}
                    {message.steps && message.steps.length > 0 && (
                      <div className="bg-gray-50 rounded-xl border border-gray-100 p-3 space-y-2">
                        <div className="flex items-center gap-2 text-xs font-medium text-gray-400 mb-2 uppercase tracking-wider">
                          <Loader2 className="w-3 h-3 animate-spin" /> Processing
                        </div>
                        {message.steps.map(step => (
                          <div key={step.id} className="flex items-start gap-3 text-sm">
                            <div className="mt-1">
                              {step.status === 'completed' ? (
                                <CheckCircle2 className="w-3.5 h-3.5 text-green-600" />
                              ) : (
                                <div className="w-3.5 h-3.5 rounded-full border-2 border-gray-300 border-t-blue-600 animate-spin" />
                              )}
                            </div>
                            <div className="flex-1">
                              <span className={`text-gray-700 ${step.status === 'running' ? 'font-medium' : ''}`}>
                                {step.label}
                              </span>
                              {step.detail && (
                                <div className="text-xs text-gray-500 mt-0.5 font-mono bg-white p-1 rounded border border-gray-100 truncate max-w-[300px]">
                                  {step.detail}
                                </div>
                              )}
                            </div>
                          </div>
                        ))}
                      </div>
                    )}

                    {/* Content */}
                    {message.content && (
                      <div className={`prose prose-sm max-w-none text-gray-800 leading-7 ${message.isError ? 'text-red-600' : ''}`}>
                        {message.content.split('\n').map((line, i) => (
                          <p key={i} className="mb-2 last:mb-0">{line}</p>
                        ))}
                      </div>
                    )}
                  </div>
                </div>
              )}
            </div>
          ))
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Floating Input Bar - Dynamic Positioning */}
      <div className={`
        absolute left-0 right-0 px-4 transition-all duration-500 ease-in-out z-20
        ${hasStartedConversation
          ? 'bottom-4'
          : 'top-[60%] -translate-y-1/2'}
      `}>
        <div className="w-full max-w-3xl mx-auto">
          <div className="bg-white rounded-2xl border border-gray-200 shadow-[0_8px_30px_rgb(0,0,0,0.04)] p-3 flex flex-col gap-2 transition-all duration-200 hover:shadow-[0_8px_30px_rgb(0,0,0,0.08)] focus-within:shadow-[0_8px_30px_rgb(0,0,0,0.12)] focus-within:ring-2 focus-within:ring-blue-500/20 focus-within:border-blue-500/50">

            {/* Text Area */}
            <Textarea
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                  e.preventDefault();
                  handleSend();
                }
              }}
              placeholder={hasStartedConversation ? "Message..." : "Ask anything (Ctrl+L)..."}
              className="min-h-[44px] max-h-[300px] border-0 focus-visible:ring-0 resize-none bg-transparent p-0 text-base placeholder:text-gray-400"
              style={{ height: input ? 'auto' : '44px' }}
            />

            {/* Bottom Controls Row */}
            <div className="flex items-center justify-between">

              {/* Left: Context Menu (+) */}
              <div className="flex items-center gap-2">
                <DropdownMenu>
                  <DropdownMenuTrigger asChild>
                    <Button variant="ghost" size="icon" className="h-8 w-8 text-gray-400 hover:text-gray-900 rounded-lg -ml-1">
                      <Plus className="w-5 h-5" />
                    </Button>
                  </DropdownMenuTrigger>
                  <DropdownMenuContent align="start" className="w-60 p-2 bg-white border border-gray-200 shadow-lg rounded-xl">
                    <DropdownMenuLabel className="text-xs font-semibold text-gray-400 mb-1 uppercase tracking-wider px-3 py-2">
                      Context Source
                    </DropdownMenuLabel>

                    <DropdownMenuItem
                      className="flex items-center justify-between cursor-pointer rounded-lg px-3 py-2.5 font-medium text-gray-700 data-[highlighted]:bg-gray-50 focus:text-gray-900 data-[state=checked]:bg-blue-50"
                      onClick={() => handleScopeChange('project')}
                    >
                      <span className={`text-sm ${scope === 'project' ? 'font-semibold text-gray-900' : 'font-medium text-gray-700'}`}>Current Project</span>
                      {scope === 'project' && <CheckCircle2 className="w-4 h-4 text-blue-600" />}
                    </DropdownMenuItem>

                    <DropdownMenuItem
                      className="flex items-center justify-between cursor-pointer rounded-lg px-3 py-2.5 font-medium text-gray-700 data-[highlighted]:bg-gray-50 focus:text-gray-900"
                      onClick={() => handleScopeChange('library')}
                    >
                      <span className={`text-sm ${scope === 'library' ? 'font-semibold text-gray-900' : 'font-medium text-gray-700'}`}>Entire Library</span>
                      {scope === 'library' && <CheckCircle2 className="w-4 h-4 text-blue-600" />}
                    </DropdownMenuItem>

                    <DropdownMenuSeparator className="my-1 bg-gray-100" />

                    <DropdownMenuItem
                      className="flex items-center justify-between cursor-pointer rounded-lg px-3 py-2.5 font-medium text-gray-700 data-[highlighted]:bg-gray-50 focus:text-gray-900"
                      onClick={() => handleScopeChange('selection')}
                    >
                      <div className="flex flex-col">
                        <span className={`text-sm ${scope === 'selection' ? 'font-semibold text-gray-900' : 'font-medium text-gray-700'}`}>Selected Papers</span>
                        {selectedPaperIds.length > 0 && (
                          <span className="text-xs text-gray-400 font-normal mt-0.5">{selectedPaperIds.length} papers active</span>
                        )}
                      </div>
                      {scope === 'selection' && <CheckCircle2 className="w-4 h-4 text-blue-600" />}
                    </DropdownMenuItem>

                    {scope === 'selection' && (
                      <div className="px-1 pt-1">
                        <Button
                          variant="outline"
                          size="sm"
                          className="w-full h-8 text-xs font-medium border-gray-200 hover:bg-gray-50 hover:text-gray-900"
                          onClick={() => setIsPickerOpen(true)}
                        >
                          Edit Selection
                        </Button>
                      </div>
                    )}
                  </DropdownMenuContent>
                </DropdownMenu>

                {/* Context Badge (visible when scope is custom) */}
                {scope === 'selection' && selectedPaperIds.length > 0 && (
                  <Badge variant="secondary" className="bg-gray-100 text-gray-500 font-normal border-0 hover:bg-gray-200 transition-colors cursor-pointer" onClick={() => setIsPickerOpen(true)}>
                    {selectedPaperIds.length} papers
                  </Badge>
                )}
              </div>

              {/* Center: Model Selector */}
              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <Button
                    variant="ghost"
                    className="h-7 px-2 text-xs font-medium text-gray-500 hover:text-gray-900 hover:bg-gray-100 rounded-lg gap-1"
                  >
                    <Sparkles className="w-3 h-3" />
                    <span className="max-w-[100px] truncate">
                      {AVAILABLE_MODELS.find(m => m.id === selectedModel)?.name || 'Select Model'}
                    </span>
                    <ChevronDown className="w-3 h-3 opacity-50" />
                  </Button>
                </DropdownMenuTrigger>
                <DropdownMenuContent align="center" className="w-64 p-2 bg-white border border-gray-200 shadow-lg rounded-xl">
                  <DropdownMenuLabel className="text-xs font-semibold text-gray-400 mb-1 uppercase tracking-wider px-3 py-2">
                    Model
                  </DropdownMenuLabel>

                  {/* Free Models */}
                  <div className="px-2 py-1">
                    <span className="text-[10px] font-medium text-green-600 uppercase tracking-wider">Free</span>
                  </div>
                  {AVAILABLE_MODELS.filter(m => m.tier === 'free').map(model => (
                    <DropdownMenuItem
                      key={model.id}
                      className="flex items-center justify-between cursor-pointer rounded-lg px-3 py-2 text-gray-700 data-[highlighted]:bg-gray-50"
                      onClick={() => handleModelChange(model.id)}
                    >
                      <div className="flex flex-col">
                        <span className={`text-sm ${selectedModel === model.id ? 'font-semibold text-gray-900' : 'font-medium'}`}>
                          {model.name}
                        </span>
                        <span className="text-[10px] text-gray-400">{model.provider}</span>
                      </div>
                      {selectedModel === model.id && <CheckCircle2 className="w-4 h-4 text-blue-600" />}
                    </DropdownMenuItem>
                  ))}

                  <DropdownMenuSeparator className="my-1 bg-gray-100" />

                  {/* Paid Models */}
                  <div className="px-2 py-1">
                    <span className="text-[10px] font-medium text-gray-400 uppercase tracking-wider">Paid</span>
                  </div>
                  {AVAILABLE_MODELS.filter(m => m.tier !== 'free').map(model => (
                    <DropdownMenuItem
                      key={model.id}
                      className="flex items-center justify-between cursor-pointer rounded-lg px-3 py-2 text-gray-700 data-[highlighted]:bg-gray-50"
                      onClick={() => handleModelChange(model.id)}
                    >
                      <div className="flex flex-col">
                        <div className="flex items-center gap-1.5">
                          <span className={`text-sm ${selectedModel === model.id ? 'font-semibold text-gray-900' : 'font-medium'}`}>
                            {model.name}
                          </span>
                          {model.badge && (
                            <span className="text-[9px] px-1.5 py-0.5 bg-blue-100 text-blue-700 rounded font-medium">
                              {model.badge}
                            </span>
                          )}
                        </div>
                        <span className="text-[10px] text-gray-400">{model.provider}</span>
                      </div>
                      {selectedModel === model.id && <CheckCircle2 className="w-4 h-4 text-blue-600" />}
                    </DropdownMenuItem>
                  ))}
                </DropdownMenuContent>
              </DropdownMenu>

              {/* Right: Send Button */}
              <Button
                onClick={handleSend}
                disabled={!input.trim() || isLoading}
                size="icon"
                className={`h-8 w-8 shrink-0 rounded-lg transition-all ${input.trim() ? 'bg-gray-900 text-white hover:bg-gray-800' : 'bg-gray-100 text-gray-300 hover:bg-gray-100'
                  }`}
              >
                <ArrowRight className="w-4 h-4" />
              </Button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
