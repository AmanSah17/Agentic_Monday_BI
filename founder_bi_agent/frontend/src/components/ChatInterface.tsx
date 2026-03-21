import React, { useState, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'motion/react';
import { Paperclip, Zap, Cpu, BarChart3, TrendingUp, Users, Clock, DollarSign, CheckCircle } from 'lucide-react';
import { Message } from '../services/ai';
import { cn } from '../lib/utils';
import confetti from 'canvas-confetti';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from 'recharts';

interface ChatInterfaceProps {
  onMessageSent: (prompt: string) => void;
  messages: Message[];
  isTyping: boolean;
}

const SUGGESTED_QUESTIONS = [
  {
    text: "Deals by owner: who has the most value in pipeline?",
    icon: Users,
    category: "Sales Pipeline"
  },
  {
    text: "What's the status breakdown of work orders by execution?",
    icon: CheckCircle,
    category: "Work Orders"
  },
  {
    text: "Which sectors are generating the most revenue?",
    icon: TrendingUp,
    category: "Revenue Analysis"
  },
  {
    text: "What's the deal-to-work-order conversion rate by stage?",
    icon: BarChart3,
    category: "Conversion"
  },
  {
    text: "Which deals are closest to closing in the next 30 days?",
    icon: Clock,
    category: "Pipeline Forecast"
  },
  {
    text: "What's the billing and collection status of all work orders?",
    icon: DollarSign,
    category: "Financials"
  }
];

export const ChatInterface = ({ onMessageSent, messages, isTyping }: ChatInterfaceProps) => {
  const [input, setInput] = useState('');
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages, isTyping]);

  const handleSuggestedQuestion = (question: string) => {
    setInput(question);
    // Trigger submit on next render
    setTimeout(() => {
      const form = document.querySelector('form');
      if (form) {
        form.dispatchEvent(new Event('submit', { bubbles: true }));
      }
    }, 0);
  };

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


      <div ref={scrollRef} className="flex-1 flex flex-col gap-6 overflow-y-auto no-scrollbar pb-32 px-2">
        {messages.length === 0 && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, staggerChildren: 0.1 }}
            className="flex flex-col gap-4 mt-12"
          >
            <div className="text-center mb-4">
              <h3 className="text-lg font-bold text-white mb-2">Suggested Questions</h3>
              <p className="text-xs text-outline">Click any question or type your own to get started</p>
            </div>
            <motion.div
              className="grid grid-cols-1 md:grid-cols-2 gap-3"
              variants={{
                container: {
                  transition: {
                    staggerChildren: 0.08,
                  }
                }
              }}
              initial="container"
              animate="container"
            >
              {SUGGESTED_QUESTIONS.map((q, i) => {
                const IconComponent = q.icon;
                return (
                  <motion.button
                    key={i}
                    onClick={() => handleSuggestedQuestion(q.text)}
                    variants={{
                      container: {
                        opacity: 0,
                        y: 10,
                      }
                    }}
                    animate={{
                      opacity: 1,
                      y: 0,
                    }}
                    transition={{ delay: i * 0.08 }}
                    className="p-4 rounded-xl bg-surface-container-low border border-outline-variant/20 text-left hover:border-primary-container/50 hover:bg-surface-container transition-all duration-200 group cursor-pointer"
                  >
                    <div className="flex items-start gap-3">
                      <div className="w-8 h-8 rounded-lg bg-primary-container/20 text-primary-container flex items-center justify-center shrink-0 group-hover:bg-primary-container/40 transition-colors">
                        <IconComponent className="w-4 h-4" />
                      </div>
                      <div className="flex-1 min-w-0">
                        <p className="text-xs text-outline mb-1 font-medium">{q.category}</p>
                        <p className="text-sm text-on-surface group-hover:text-white transition-colors line-clamp-2">
                          {q.text}
                        </p>
                      </div>
                    </div>
                  </motion.button>
                );
              })}
            </motion.div>
          </motion.div>
        )}
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


                {msg.role === 'model' && msg.payload?.result_records?.length ? (
                  <div className="mt-4 rounded-xl border border-outline-variant/20 bg-surface-container-lowest p-3">
                    <p className="text-[10px] uppercase tracking-widest text-outline mb-2">
                      Result Rows ({msg.payload.result_records.length})
                    </p>
                    <ResultPreview records={msg.payload.result_records} />
                  </div>
                ) : null}

                {msg.role === 'model' && msg.payload?.chart_spec?.kind === 'bar' && msg.payload?.result_records?.length ? (
                  <div className="mt-4 h-64 w-full rounded-xl border border-outline-variant/20 bg-surface-container-lowest p-4">
                    <p className="text-xs font-bold text-outline mb-4">{String(msg.payload.chart_spec.title)}</p>
                    <ResponsiveContainer width="100%" height="100%">
                      <BarChart data={msg.payload.result_records as any[]}>
                        <CartesianGrid strokeDasharray="3 3" stroke="#333" vertical={false} />
                        <XAxis dataKey={msg.payload.chart_spec.x as string} stroke="#888" tick={{fontSize: 10}} />
                        <YAxis stroke="#888" tick={{fontSize: 10}} width={80} />
                        <Tooltip contentStyle={{backgroundColor: '#111', borderColor: '#333'}} itemStyle={{color: '#fff'}} />
                        <Bar dataKey={msg.payload.chart_spec.y as string} fill="#6161ff" radius={[4, 4, 0, 0]} />
                      </BarChart>
                    </ResponsiveContainer>
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
      Object.keys(row).forEach((k) => {
        // filter out raw subitems or internal monday IDs to show real business data
        if (!k.includes('__raw') && !['subitems', 'item_id', 'group_id', 'created_at', 'updated_at'].includes(k)) {
          set.add(k);
        }
      });
      return set;
    }, new Set<string>())
  ).slice(0, 15);

  if (!columns.length) {
    return <p className="text-xs text-outline">No tabular rows to display.</p>;
  }

  return (
    <div className="mt-3">
      <details className="group border border-gray-700 rounded-md bg-gray-900 overflow-hidden">
        <summary className="p-2 cursor-pointer text-xs font-semibold hover:bg-gray-800 transition-colors select-none flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span className="text-gray-400 font-mono transition-transform duration-200 group-open:rotate-90">▶</span>
            <span>View Raw Data ({records.length} rows)</span>
          </div>
        </summary>
        <div className="w-full overflow-x-auto border-t border-gray-700 bg-gray-950 p-2">
          <table className="w-full text-xs text-left whitespace-nowrap">
            <thead>
              <tr className="border-b border-gray-700">
                {columns.map((col) => (
                  <th key={col} className="px-3 py-2 font-mono text-outline">
                    {col}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {limited.map((row, i) => (
                <tr key={i} className="border-b border-gray-800/40 hover:bg-gray-800/20">
                  {columns.map((col) => {
                    const val = row[col];
                    const displayVal =
                      val !== null && val !== undefined ? String(val) : "null";
                    return (
                      <td key={col} className="px-3 py-1 font-mono text-gray-300">
                        {displayVal}
                      </td>
                    );
                  })}
                </tr>
              ))}
            </tbody>
          </table>
          {records.length > 8 && (
            <p className="px-3 py-2 text-xs italic text-outline border-t border-gray-800">
              Showing first 8 records. Next {records.length - 8} rows truncated.
            </p>
          )}
        </div>
      </details>
    </div>
  );
};

function formatCell(value: unknown) {
  if (value === null || value === undefined) return 'null';
  if (typeof value === 'object') return JSON.stringify(value);
  return String(value);
}
