import React, { useState, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'motion/react';
import { Paperclip, Zap, Cpu, BarChart3 } from 'lucide-react';
import { Message } from '../services/ai';
import { cn } from '../lib/utils';
import confetti from 'canvas-confetti';

interface ChatInterfaceProps {
  onMessageSent: (prompt: string) => void;
  messages: Message[];
  isTyping: boolean;
}

export const ChatInterface = ({ onMessageSent, messages, isTyping }: ChatInterfaceProps) => {
  const [input, setInput] = useState('');
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages, isTyping]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isTyping) return;

    onMessageSent(input);
    setInput('');

    if (input.toLowerCase().includes('success') || input.toLowerCase().includes('win')) {
      confetti({
        particleCount: 100,
        spread: 70,
        origin: { y: 0.6 },
        colors: ['#6161ff', '#ffcb05', '#ffffff'],
      });
    }
  };

  return (
    <section className="flex-1 flex flex-col gap-6 max-w-4xl mx-auto w-full">
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="bg-surface-container-low rounded-xl p-6 flex items-center justify-between border border-outline-variant/10"
      >
        <div className="flex items-center gap-4">
          <div className="bg-primary-container/20 p-3 rounded-lg">
            <BarChart3 className="w-6 h-6 text-primary-container" />
          </div>
          <div>
            <h2 className="text-lg font-bold text-white tracking-tight">Business Intelligence Hub</h2>
            <p className="text-xs text-outline">Live monday tool-calling + traceable reasoning.</p>
          </div>
        </div>
        <div className="flex items-center gap-3 bg-surface-container-lowest p-1 rounded-lg">
          <button className="px-4 py-1.5 text-xs font-bold text-outline hover:text-white transition-all">
            Fast
          </button>
          <button className="px-4 py-1.5 text-xs font-bold text-primary-container bg-surface-container-high rounded-md">
            Deep Reasoning
          </button>
        </div>
      </motion.div>

      <div ref={scrollRef} className="flex-1 flex flex-col gap-6 overflow-y-auto no-scrollbar pb-32 px-2">
        <AnimatePresence initial={false}>
          {messages.map((msg, i) => (
            <motion.div
              key={i}
              initial={{ opacity: 0, y: 10, scale: 0.95 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              className={cn('flex gap-4', msg.role === 'user' ? 'justify-end' : 'justify-start')}
            >
              {msg.role === 'model' && (
                <div className="w-8 h-8 rounded-lg bg-primary-container flex items-center justify-center shrink-0">
                  <Cpu className="w-4 h-4 text-white" />
                </div>
              )}

              <div
                className={cn(
                  'max-w-[85%] p-5 rounded-2xl text-sm leading-relaxed shadow-lg',
                  msg.role === 'user'
                    ? 'bg-surface-container-high rounded-tr-none text-on-surface'
                    : 'bg-surface-container-low border border-outline-variant/10 text-on-surface'
                )}
              >
                {msg.content}

                {msg.role === 'model' && msg.payload?.sql_query && (
                  <div className="mt-4 rounded-xl border border-outline-variant/20 bg-surface-container-lowest p-3">
                    <p className="text-[10px] uppercase tracking-widest text-outline mb-2">Generated SQL</p>
                    <pre className="text-[11px] whitespace-pre-wrap break-words font-mono text-primary-container">
                      {msg.payload.sql_query}
                    </pre>
                  </div>
                )}

                {msg.role === 'model' && msg.payload?.result_records?.length ? (
                  <div className="mt-4 rounded-xl border border-outline-variant/20 bg-surface-container-lowest p-3">
                    <p className="text-[10px] uppercase tracking-widest text-outline mb-2">
                      Result Rows ({msg.payload.result_records.length})
                    </p>
                    <ResultPreview records={msg.payload.result_records} />
                  </div>
                ) : null}

                {msg.role === 'model' && msg.payload?.traces?.length ? (
                  <div className="mt-3 text-[10px] uppercase tracking-widest text-outline">
                    Trace Steps: {msg.payload.traces.length}
                  </div>
                ) : null}
              </div>
            </motion.div>
          ))}
        </AnimatePresence>

        {isTyping && (
          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="flex justify-start gap-4">
            <div className="w-8 h-8 rounded-lg bg-primary-container flex items-center justify-center shrink-0 animate-pulse">
              <Cpu className="w-4 h-4 text-white" />
            </div>
            <div className="bg-surface-container-low border border-outline-variant/10 p-4 rounded-2xl flex gap-1">
              <span
                className="w-1.5 h-1.5 bg-primary-container rounded-full animate-bounce"
                style={{ animationDelay: '0ms' }}
              />
              <span
                className="w-1.5 h-1.5 bg-primary-container rounded-full animate-bounce"
                style={{ animationDelay: '150ms' }}
              />
              <span
                className="w-1.5 h-1.5 bg-primary-container rounded-full animate-bounce"
                style={{ animationDelay: '300ms' }}
              />
            </div>
          </motion.div>
        )}
      </div>

      <div className="fixed bottom-8 left-[calc(16rem+2rem)] right-[calc(24rem+2rem+2rem)] z-30">
        <form onSubmit={handleSubmit} className="glass-panel rounded-2xl p-2 shadow-2xl flex items-center gap-2">
          <button type="button" className="p-3 text-outline hover:text-white transition-colors">
            <Paperclip className="w-5 h-5" />
          </button>
          <input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            className="flex-1 bg-transparent border-none focus:ring-0 text-on-surface placeholder:text-outline/50 text-sm"
            placeholder="Ask pipeline, revenue, sector, or execution questions..."
            type="text"
            disabled={isTyping}
          />
          <div className="flex items-center gap-2 pr-2">
            <button
              type="submit"
              disabled={!input.trim() || isTyping}
              className="bg-primary-container text-white px-5 py-2 rounded-xl text-xs font-bold hover:brightness-110 disabled:opacity-50 disabled:cursor-not-allowed transition-all flex items-center gap-2"
            >
              <span>Execute</span>
              <Zap className="w-4 h-4 fill-current" />
            </button>
          </div>
        </form>
      </div>
    </section>
  );
};

interface ResultPreviewProps {
  records: Array<Record<string, unknown>>;
}

const ResultPreview = ({ records }: ResultPreviewProps) => {
  const limited = records.slice(0, 8);
  const columns = Array.from(
    limited.reduce((set, row) => {
      Object.keys(row).forEach((k) => set.add(k));
      return set;
    }, new Set<string>())
  ).slice(0, 6);

  if (!columns.length) {
    return <p className="text-xs text-outline">No tabular rows to display.</p>;
  }

  return (
    <div className="overflow-x-auto">
      <table className="min-w-full text-[11px]">
        <thead>
          <tr className="text-left text-outline border-b border-outline-variant/20">
            {columns.map((col) => (
              <th key={col} className="py-1 pr-3 font-bold uppercase tracking-widest text-[9px]">
                {col}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {limited.map((row, idx) => (
            <tr key={idx} className="border-b border-outline-variant/10">
              {columns.map((col) => (
                <td key={col} className="py-1 pr-3 text-on-surface">
                  {formatCell(row[col])}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};

function formatCell(value: unknown) {
  if (value === null || value === undefined) return 'null';
  if (typeof value === 'object') return JSON.stringify(value);
  return String(value);
}
