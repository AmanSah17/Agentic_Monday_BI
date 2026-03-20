import React, { useState } from 'react';
import { Sidebar } from './components/Sidebar';
import { TopBar } from './components/TopBar';
import { ChatInterface } from './components/ChatInterface';
import { ReasoningTrace } from './components/ReasoningTrace';
import { ThreeDScene } from './components/ThreeDScene';
import {
  getOrCreateSessionId,
  Message,
  ReasoningStep,
  loadingReasoningSteps,
  queryFounderBI,
  tracesToReasoningSteps,
} from './services/ai';

const INITIAL_REASONING_STEPS: ReasoningStep[] = loadingReasoningSteps().map((s) => ({
  ...s,
  status: 'pending',
}));

export default function App() {
  const sessionId = getOrCreateSessionId();
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

  const handleMessageSent = async (prompt: string) => {
    const userMsg: Message = { role: 'user', content: prompt, timestamp: new Date() };
    const nextMessages = [...messages, userMsg];
    setMessages(nextMessages);
    setIsTyping(true);
    setReasoningSteps(loadingReasoningSteps());

    try {
      const history = nextMessages.map((m) => ({
        role: m.role === 'model' ? 'assistant' : 'user',
        content: m.content,
      }));

      const response = await queryFounderBI(prompt, history, sessionId);
      const traceSteps = tracesToReasoningSteps(response.traces || []);
      setReasoningSteps(traceSteps.length ? traceSteps : INITIAL_REASONING_STEPS);

      const modelText = response.needs_clarification
        ? response.clarification_question || 'I need one clarification before proceeding.'
        : response.answer || 'Analysis complete.';

      const modelMsg: Message = {
        role: 'model',
        content: modelText,
        timestamp: new Date(),
        payload: response,
      };
      setMessages((prev) => [...prev, modelMsg]);
    } catch (error) {
      console.error('Backend Error:', error);
      setMessages((prev) => [
        ...prev,
        {
          role: 'model',
          content: `I encountered a backend processing error while running live tools. Please retry.\n\nError: ${error instanceof Error ? error.message : String(error)}`,
          timestamp: new Date(),
        },
      ]);
    } finally {
      setIsTyping(false);
    }
  };

  return (
    <div className="min-h-screen bg-surface selection:bg-primary-container/30">
      <ThreeDScene />
      <Sidebar />
      <TopBar />
      
      <main className="ml-64 p-8 min-h-[calc(100vh-4rem)] flex gap-8 relative z-10">
        <ChatInterface 
          messages={messages} 
          onMessageSent={handleMessageSent} 
          isTyping={isTyping} 
        />
        <ReasoningTrace steps={reasoningSteps} />
      </main>
    </div>
  );
}
