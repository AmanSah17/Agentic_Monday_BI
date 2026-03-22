import React, { useState } from 'react';
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
  queryFounderBI,
  tracesToReasoningSteps,
} from './services/ai';
import { wsService } from './services/websocket';

type ViewMode = 'chat' | 'dashboard' | 'data-map' | 'library' | 'admin';

const INITIAL_REASONING_STEPS: ReasoningStep[] = loadingReasoningSteps().map((s) => ({
  ...s,
  status: 'pending',
}));

export default function App() {
  const sessionId = getOrCreateSessionId();
  
  // Resolve initial view from path
  const getInitialView = (): ViewMode => {
    const path = window.location.pathname.replace(/^\//, '');
    if (['chat', 'dashboard', 'data-map', 'library', 'admin'].includes(path)) {
      return path as ViewMode;
    }
    return 'chat';
  };

  const [viewMode, setViewMode] = useState<ViewMode>(getInitialView());
  
  // Handle popstate for back/forward navigation
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
  const [messages, setMessages] = useState<Message[]>([
    {
      role: 'model',
      content:
        `Welcome. Session: ${sessionId.slice(0, 8)}... Connected to live monday.com data (Deal funnel Data + Work_Order_Tracker Data). Ask a business intelligence question.`,
      timestamp: new Date(),
    },
  ]);
  const [isTyping, setIsTyping] = useState(false);
  const [reasoningSteps, setReasoningSteps] = useState<ReasoningStep[]>(INITIAL_REASONING_STEPS);
  
  // Graph & Lineage State
  const [graphNodes, setGraphNodes] = useState<GraphNode[]>([]);
  const [graphEdges, setGraphEdges] = useState<GraphEdge[]>([]);
  const [lineageNodes, setLineageNodes] = useState<DataFlowNode[]>([]);
  const [lineageEdges, setLineageEdges] = useState<DataFlowEdge[]>([]);

  // WebSocket event handling for real-time trace
  React.useEffect(() => {
    const unsubscribe = wsService.subscribe((event) => {
      if (event.type === 'node_start') {
        const nodeName = event.node_name || 'unknown';
        
        // Update Graph Nodes
        setGraphNodes(prev => {
          const existing = prev.find(n => n.id === nodeName);
          if (existing) {
            return prev.map(n => n.id === nodeName ? { ...n, status: 'running' } : n);
          }
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
          
          return [...prev, {
            id: prev.length + 1,
            title,
            description: 'Analyzing data...',
            status: 'active'
          }];
        });
      }
      
      if (event.type === 'node_end') {
        const nodeName = event.node_name || 'unknown';
        const output = event.data?.output_data || {};
        
        // Update Graph Nodes
        setGraphNodes(prev => prev.map(n => n.id === nodeName ? { 
          ...n, 
          status: 'completed',
          executionTime: event.execution_time_ms 
        } : n));

        setReasoningSteps(prev => prev.map(s => {
          const title = nodeName.replace(/_/g, ' ').toUpperCase();
          if (s.title === title || s.title.includes(title)) {
            return { 
              ...s, 
              status: 'completed',
              description: `Completed in ${event.execution_time_ms?.toFixed(0) || '?'}ms`,
              code: JSON.stringify(output, null, 2).slice(0, 500)
            };
          }
          return s;
        }));

        // If it's the final insight, add message
        if (nodeName === 'insight_writer' && output.answer) {
          const modelMsg: Message = {
            role: 'model',
            content: output.answer,
            timestamp: new Date(),
            payload: output as any,
          };
          setMessages((prev) => [...prev, modelMsg]);
          setIsTyping(false);
        }
      }

      if (event.type === 'data_flow') {
        // Update Lineage
        const node_id = `data_${Date.now()}`;
        setLineageNodes(prev => [...prev, {
          id: node_id,
          name: event.description || 'Data chunk',
          dataType: 'data_table',
          timestamp: event.timestamp
        }]);
        
        if (event.from && event.to) {
          setLineageEdges(prev => [...prev, {
            id: `edge_${Date.now()}`,
            from: event.from!,
            to: event.to!,
            dataCount: 1,
            transformationType: 'data_flow'
          }]);
        }
      }

      if (event.type === 'execution_error') {
        setMessages((prev) => [
          ...prev,
          {
            role: 'model',
            content: `Execution failed: ${event.error}`,
            timestamp: new Date(),
          },
        ]);
        setIsTyping(false);
      }
    });

    return () => {
      unsubscribe();
      wsService.disconnect();
    };
  }, []);

  const handleMessageSent = async (prompt: string) => {
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
      await wsService.connect(sessionId);
      const history = nextMessages.map((m) => ({
        role: m.role === 'model' ? 'assistant' : 'user',
        content: m.content,
      }));

      wsService.execute(prompt, history);
    } catch (error) {
      console.error('WS Connection Error:', error);
      setIsTyping(false);
      setMessages((prev) => [
        ...prev,
        {
          role: 'model',
          content: `Failed to connect to real-time engine: ${error instanceof Error ? error.message : String(error)}`,
          timestamp: new Date(),
        },
      ]);
    }
  };

  return (
    <div className="min-h-screen bg-surface selection:bg-primary-container/30">
      <ThreeDScene />
      <main className="ml-64 p-8 min-h-[calc(100vh-4rem)] relative z-10">
        <Sidebar currentView={viewMode} onViewChange={handleLinkClick} />
        <TopBar />
        {viewMode === 'chat' && (
          <div className="flex gap-8">
            <ChatInterface 
              messages={messages} 
              onMessageSent={handleMessageSent} 
              isTyping={isTyping} 
            />
            <ReasoningTrace steps={reasoningSteps} />
          </div>
        )}
        
        {viewMode === 'dashboard' && (
          <div className="w-full">
            <AnalyticsDashboard />
          </div>
        )}
        
        {viewMode === 'data-map' && (
          <div className="space-y-8">
            <NodeGraphVisualization 
              nodes={graphNodes} 
              edges={graphEdges} 
              isExecuting={isTyping}
            />
            <DataLineageVisualization 
              nodes={lineageNodes} 
              edges={lineageEdges} 
              title="Execution Data Lineage"
            />
          </div>
        )}
        
        {viewMode === 'library' && (
          <div className="flex items-center justify-center h-96">
            <div className="text-center text-outline">
              <h2 className="text-2xl font-bold text-white mb-2">Query Library</h2>
              <p>Pre-built queries and saved analyses coming soon</p>
            </div>
          </div>
        )}
        
        {viewMode === 'admin' && (
          <div className="flex items-center justify-center h-96">
            <div className="text-center text-outline">
              <h2 className="text-2xl font-bold text-white mb-2">Admin Settings</h2>
              <p>Configuration and system settings coming soon</p>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
