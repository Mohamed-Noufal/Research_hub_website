import { useState, useRef, useEffect } from 'react';
import {
  Send, Search, Database, RotateCcw,
  Brain, CheckCircle2, Loader2, ChevronRight,
  FileSearch, Network, BarChart, FileText, GitCompare,
  BookOpen, Lightbulb, AlertCircle
} from 'lucide-react';
import { Button } from '../ui/button';
import { Textarea } from '../ui/textarea';
import type { Paper } from '../../App';
import ReconnectingWebSocket from 'reconnecting-websocket';

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
      content: `Hello! I'm your AI research assistant. I can helping you with:

• Summarizing papers in your library
• Finding connections between research
• Literature review assistance
• Analyzing trends and identifying gaps

${projectId ? 'I am currently focused on your selected project.' : 'How can I assist you today?'}`,
      timestamp: new Date()
    }
  ]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [conversationId, setConversationId] = useState<string | null>(null);
  const [userId, setUserId] = useState<string | null>(() => localStorage.getItem('paper-search-user-uuid-v1'));


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
        // Here we could fetch existing history if we had a persistent conversation ID
        // For now, we create a new one or use local storage to persist for session
        // Only if we don't have one
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

      // Handle new streaming event types
      if (data.type === 'thinking') {
        // Agent is analyzing the request
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
        // Agent selected a tool
        if (isAssistant) {
          let newSteps = [...(lastMsg.steps || [])];
          // Mark thinking as complete
          newSteps = newSteps.map(s => s.status === 'running' ? { ...s, status: 'completed' } : s);
          // Add tool selection step
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

      if (data.type === 'tool_executing') {
        // Tool is executing
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
        // Tool completed with result
        if (isAssistant) {
          const newSteps = (lastMsg.steps || []).map(s =>
            s.tool === data.tool && s.status === 'running'
              ? { ...s, status: 'completed', label: `✓ ${data.tool}`, detail: typeof data.result === 'string' ? data.result : JSON.stringify(data.result).substring(0, 100) }
              : s
          );
          return prev.map(m => m.id === lastMsg.id ? { ...m, steps: newSteps } : m);
        }
        return prev;
      }

      if (data.type === 'tool_error') {
        // Tool failed
        if (isAssistant) {
          const newSteps = (lastMsg.steps || []).map(s =>
            s.tool === data.tool
              ? { ...s, status: 'completed', label: `✗ ${data.tool} failed`, detail: data.error }
              : s
          );
          return prev.map(m => m.id === lastMsg.id ? { ...m, steps: newSteps } : m);
        }
        return prev;
      }

      if (data.type === 'synthesizing') {
        // Agent is generating final answer
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
        // Final answer content
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

    // Create placeholder for assistant response
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

    // Send payload
    wsRef.current.send(JSON.stringify({
      message: input,
      project_id: projectId ? Number(projectId) : null,
      user_id: userId
      // parent_message_id could be added for internal tracking
    }));
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
                {(message.agent || (message.steps && message.steps.length > 0)) && index > 0 && (
                  <div className="flex items-center gap-2">
                    <div className="inline-flex items-center gap-1.5 px-2 py-0.5 bg-gray-100 rounded text-xs text-gray-600">
                      <CheckCircle2 className="w-3 h-3" />
                      <span>{message.agent || 'AI Agent'}</span>
                    </div>
                  </div>
                )}

                {/* Processing Steps */}
                {message.steps && message.steps.length > 0 && (
                  <div className="space-y-2 border-l-2 border-gray-100 pl-3">
                    {message.steps.map((step) => (
                      <div
                        key={step.id}
                        className="flex items-start gap-2.5"
                      >
                        <div className="mt-0.5">
                          {step.status === 'completed' && <CheckCircle2 className="w-4 h-4 text-emerald-600" />}
                          {step.status === 'running' && <Loader2 className="w-4 h-4 text-blue-600 animate-spin" />}
                          {step.status === 'pending' && <div className="w-4 h-4 rounded-full border-2 border-gray-300" />}
                        </div>

                        <div className="flex-1">
                          <div className={`text-sm ${step.status === 'completed' ? 'text-gray-900' : step.status === 'running' ? 'text-gray-900' : 'text-gray-400'}`}>
                            {step.label}
                          </div>
                          {step.tool && step.status !== 'pending' && (
                            <div className="flex items-center gap-2 mt-1">
                              <div className="inline-flex items-center gap-1 text-xs text-gray-500">
                                {/* Icon logic simplified */}
                                <Database className="w-3 h-3" />
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
                    ))}
                  </div>
                )}

                {/* Message Content */}
                {message.content && (
                  <div className={`text-gray-900 space-y-3 leading-relaxed ${message.isError ? 'text-red-600' : ''}`}>
                    {message.content.split('\n').map((line, i) => {
                      if (line.startsWith('**') && line.endsWith('**')) {
                        return <div key={i} className="font-semibold mt-4 first:mt-0">{line.replace(/\*\*/g, '')}</div>;
                      }
                      if (line.startsWith('• ')) {
                        return <div key={i} className="flex gap-2"><span className="text-gray-400">•</span><span className="flex-1">{line.replace('• ', '')}</span></div>;
                      }
                      return line.trim() ? <p key={i}>{line}</p> : <br key={i} />;
                    })}
                  </div>
                )}
              </div>
            )}
          </div>
        ))}

        {isLoading && messages[messages.length - 1]?.role !== 'assistant' && (
          <div className="flex items-center gap-2"><Loader2 className="w-4 h-4 animate-spin text-gray-400" /></div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Quick Actions (only if empty history) */}
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
              placeholder="Ask anything (Ctrl+L)..."
              className="resize-none min-h-[52px] bg-transparent border-0 text-gray-900 placeholder:text-gray-400 focus-visible:ring-0 focus-visible:ring-offset-0"
            />
          </div>
          <Button
            onClick={handleSend}
            disabled={!input.trim() || isLoading}
            className="h-[52px] w-[52px] p-0 bg-gray-900 hover:bg-gray-800 text-white rounded-lg disabled:opacity-50"
          >
            <Send className="w-4 h-4" />
          </Button>
        </div>
      </div>
    </div>
  );
}
