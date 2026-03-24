import React, { useState } from 'react';
import { AuthProvider, useAuth } from './contexts/AuthContext';
import { LoginPage } from './pages/LoginPage';
import { RegisterPage } from './pages/RegisterPage';
import { Sidebar } from './components/Sidebar';
import { TopBar } from './components/TopBar';
import { ChatInterface } from './components/ChatInterface';
import { ReasoningTrace } from './components/ReasoningTrace';
import { AnalyticsDashboard } from './components/AnalyticsDashboard';
import { ThreeDScene } from './components/ThreeDScene';
import { NodeGraphVisualization, GraphNode, GraphEdge } from './components/NodeGraphVisualization';
import { DataLineageVisualization, DataFlowNode, DataFlowEdge } from './components/DataLineageVisualization';
import {
  getOrCreateSessionId,
  Message,
  ReasoningStep,
  loadingReasoningSteps,
} from './services/ai';
import { wsService } from './services/websocket';

type ViewMode = 'chat' | 'dashboard' | 'data-map' | 'library' | 'admin';

const INITIAL_REASONING_STEPS: ReasoningStep[] = loadingReasoningSteps().map((s) => ({
  ...s,
  status: 'pending',
}));

function AppContent() {
  const { user, token, isLoading, logout } = useAuth();
  const [authView, setAuthView] = useState<'login' | 'register'>('login');
  const sessionId = getOrCreateSessionId();
  
  const getInitialView = (): ViewMode => {
    const path = window.location.pathname.replace(/^\//, '');
    if (['chat', 'dashboard', 'data-map', 'library', 'admin'].includes(path)) {
      return path as ViewMode;
    }
    return 'chat';
  };

  const [viewMode, setViewMode] = useState<ViewMode>(getInitialView());
  
  React.useEffect(() => {
    const handlePopState = () => {
      const path = window.location.pathname.replace(/^\//, '') || 'chat';
      setViewMode(path as ViewMode);
    };
    window.addEventListener('popstate', handlePopState);
    return () => window.removeEventListener('popstate', handlePopState);
  }, []);

  const handleLinkClick = (mode: ViewMode) => {
    window.history.pushState(null, '', `/${mode}`);
    setViewMode(mode);
  };

  const [messages, setMessages] = useState<Message[]>([]);
  const [isTyping, setIsTyping] = useState(false);
  const [reasoningSteps, setReasoningSteps] = useState<ReasoningStep[]>(INITIAL_REASONING_STEPS);
  
  // Fetch history on load
  React.useEffect(() => {
    if (token && user) {
      const loadHistory = async () => {
        try {
          const resp = await fetch(`/api/v1/chat/history/${sessionId}`, {
            headers: { 'Authorization': `Bearer ${token}` }
          });
          if (resp.ok) {
            const data = await resp.json();
            if (data.history && data.history.length > 0) {
              setMessages(data.history.map((h: any) => ({
                role: h.role,
                content: h.content,
                timestamp: new Date() // Fallback timestamp
              })));
            } else {
              setMessages([{
                role: 'model',
                content: `Welcome, ${user.username}. Ask a business intelligence question to begin.`,
                timestamp: new Date(),
              }]);
            }
          }
        } catch (error) {
          console.error('Failed to load history:', error);
        }
      };
      loadHistory();
    }
  }, [token, user, sessionId]);
  
  const [graphNodes, setGraphNodes] = useState<GraphNode[]>([]);
  const [graphEdges, setGraphEdges] = useState<GraphEdge[]>([]);
  const [lineageNodes, setLineageNodes] = useState<DataFlowNode[]>([]);
  const [lineageEdges, setLineageEdges] = useState<DataFlowEdge[]>([]);

  React.useEffect(() => {
    const unsubscribe = wsService.subscribe((event) => {
      if (event.type === 'node_start') {
        const nodeName = event.node_name || 'unknown';
        setGraphNodes(prev => {
          const existing = prev.find(n => n.id === nodeName);
          if (existing) return prev.map(n => n.id === nodeName ? { ...n, status: 'running' } : n);
          return [...prev, { id: nodeName, label: nodeName.toUpperCase(), status: 'running' }];
        });
        setReasoningSteps(prev => {
          const title = nodeName.replace(/_/g, ' ').toUpperCase();
          const existingIdx = prev.findIndex(s => s.title === title || s.title.includes(title));
          if (existingIdx !== -1) {
            const next = [...prev];
            next[existingIdx] = { ...next[existingIdx], status: 'active' };
            return next;
          }
          return [...prev, { id: prev.length + 1, title, description: 'Analyzing...', status: 'active' }];
        });
      }
      
      if (event.type === 'node_end') {
        const nodeName = event.node_name || 'unknown';
        const output = event.data?.output_data || {};
        setGraphNodes(prev => prev.map(n => n.id === nodeName ? { ...n, status: 'completed', executionTime: event.execution_time_ms } : n));
        setReasoningSteps(prev => prev.map(s => {
          const title = nodeName.replace(/_/g, ' ').toUpperCase();
          if (s.title === title || s.title.includes(title)) {
            return { ...s, status: 'completed', description: `Done in ${event.execution_time_ms?.toFixed(0) || '?'}ms`, code: JSON.stringify(output, null, 2).slice(0, 500) };
          }
          return s;
        }));

        if (nodeName === 'insight_writer' && output.answer) {
          setMessages((prev) => [...prev, { role: 'model', content: output.answer, timestamp: new Date(), payload: output as any }]);
          setIsTyping(false);
        }

        if (nodeName === 'clarifier' && output.needs_clarification && output.clarification_question) {
          setMessages((prev) => [...prev, { role: 'model', content: output.clarification_question, timestamp: new Date() }]);
          setIsTyping(false);
        }
      }

      if (event.type === 'execution_complete') {
        setIsTyping(false);
      }

      if (event.type === 'data_flow') {
        const node_id = `data_${Date.now()}`;
        setLineageNodes(prev => [...prev, { id: node_id, name: event.description || 'Data chunk', dataType: 'data_table', timestamp: event.timestamp }]);
        if (event.from && event.to) {
          setLineageEdges(prev => [...prev, { id: `edge_${Date.now()}`, from: event.from!, to: event.to!, dataCount: 1, transformationType: 'data_flow' }]);
        }
      }

      if (event.type === 'execution_error') {
        setMessages((prev) => [...prev, { role: 'model', content: `Execution failed: ${event.error}`, timestamp: new Date() }]);
        setIsTyping(false);
      }

      // @ts-ignore - type may be missing in WSEventType but sent by backend
      if (event.type === 'auth_error') {
        setMessages((prev) => [...prev, { role: 'model', content: `Authentication failed: ${event.message || 'Please log in again.'}`, timestamp: new Date() }]);
        setIsTyping(false);
        logout();
      }
    });

    return () => {
      unsubscribe();
      wsService.disconnect();
    };
  }, []);

  const handleMessageSent = async (prompt: string) => {
    if (!token) return;
    const userMsg: Message = { role: 'user', content: prompt, timestamp: new Date() };
    const nextMessages = [...messages, userMsg];
    setMessages(nextMessages);
    setIsTyping(true);
    setReasoningSteps(INITIAL_REASONING_STEPS);
    setGraphNodes([]);
    setGraphEdges([]);
    setLineageNodes([]);
    setLineageEdges([]);

    try {
      await wsService.connect(sessionId, token);
      const history = nextMessages.map((m) => ({
        role: m.role === 'model' ? 'assistant' : 'user',
        content: m.content,
      }));
      wsService.execute(prompt, history);
    } catch (error) {
      console.error('WS Connection Error:', error);
      setIsTyping(false);
      setMessages((prev) => [...prev, { role: 'model', content: `Failed to connect: ${error instanceof Error ? error.message : String(error)}`, timestamp: new Date() }]);
    }
  };

  if (isLoading) {
    return (
      <div className="min-h-screen bg-surface flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-primary"></div>
      </div>
    );
  }

  if (!user) {
    return authView === 'login' ? (
      <LoginPage onToggle={() => setAuthView('register')} />
    ) : (
      <RegisterPage onToggle={() => setAuthView('login')} />
    );
  }

  return (
    <div className="min-h-screen bg-surface selection:bg-primary-container/30">
      <ThreeDScene />
      <Sidebar 
        currentView={viewMode} 
        onViewChange={handleLinkClick} 
        onLogout={logout} 
        username={user?.username} 
      />
      <main className="ml-64 p-8 min-h-[calc(100vh-4rem)] relative z-10">
        <TopBar />
        {viewMode === 'chat' && (
          <div className="flex gap-8">
            <ChatInterface messages={messages} onMessageSent={handleMessageSent} isTyping={isTyping} />
            <ReasoningTrace steps={reasoningSteps} />
          </div>
        )}
        {viewMode === 'dashboard' && <div className="w-full"><AnalyticsDashboard /></div>}
        {viewMode === 'data-map' && (
          <div className="space-y-8">
            <NodeGraphVisualization nodes={graphNodes} edges={graphEdges} isExecuting={isTyping} />
            <DataLineageVisualization nodes={lineageNodes} edges={lineageEdges} title="Execution Data Lineage" />
          </div>
        )}
        {/* Placeholder for Library and Admin */}
        {(viewMode === 'library' || viewMode === 'admin') && (
          <div className="flex items-center justify-center h-96 text-outline">
            <h2 className="text-2xl font-bold text-white uppercase">{viewMode} Coming Soon</h2>
          </div>
        )}
      </main>
    </div>
  );
}

export default function App() {
  return (
    <AuthProvider>
      <AppContent />
    </AuthProvider>
  );
}
