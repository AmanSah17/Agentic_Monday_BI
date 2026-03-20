import React from 'react';
import { motion } from 'motion/react';
import { Terminal, Sparkles } from 'lucide-react';
import { ReasoningStep } from '../services/ai';
import { cn } from '../lib/utils';

interface ReasoningTraceProps {
  steps: ReasoningStep[];
}

export const ReasoningTrace = ({ steps }: ReasoningTraceProps) => {
  return (
    <aside className="w-[24rem] h-[calc(100vh-8rem)] sticky top-24 bg-surface-container-low rounded-2xl border border-outline-variant/10 overflow-hidden flex flex-col">
      <div className="p-5 border-b border-outline-variant/10 flex justify-between items-center bg-surface-container-low">
        <div className="flex items-center gap-2">
          <Terminal className="w-4 h-4 text-primary" />
          <span className="text-xs font-black uppercase tracking-widest text-white">Reasoning Trace</span>
        </div>
        <span className="text-[10px] text-outline">v4.2-turbo</span>
      </div>

      <div className="flex-1 overflow-y-auto p-6 space-y-8 no-scrollbar">
        {steps.map((step, index) => (
          <motion.div 
            key={step.id}
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: index * 0.1 }}
            className="relative pl-8"
          >
            <div className={cn(
              "absolute left-0 top-0 w-6 h-6 rounded-full border flex items-center justify-center transition-colors",
              step.status === 'completed' ? "bg-primary-container/20 border-primary-container/40" : 
              step.status === 'active' ? "bg-secondary-container/20 border-secondary-container/40 animate-pulse" :
              "bg-surface-container-highest border-outline-variant/20"
            )}>
              <span className={cn(
                "text-[10px] font-bold",
                step.status === 'completed' ? "text-primary" : 
                step.status === 'active' ? "text-secondary-container" : "text-outline"
              )}>{step.id}</span>
            </div>
            
            {index < steps.length - 1 && (
              <div className="absolute left-3 top-6 bottom-[-32px] w-[1px] bg-outline-variant/20" />
            )}

            <div>
              <h4 className="text-xs font-bold text-white uppercase tracking-tight">{step.title}</h4>
              <p className="text-[11px] text-outline mt-1 leading-relaxed">{step.description}</p>
              
              {step.code && (
                <div className="mt-2 bg-surface-container-high/50 p-2 rounded-lg text-[10px] font-mono text-primary-container/80 overflow-x-auto">
                  {step.code}
                </div>
              )}

              {step.status === 'active' && (
                <div className="mt-3 p-3 bg-secondary-container/5 rounded-lg border border-secondary-container/20 border-dashed">
                  <div className="flex items-center gap-2 text-secondary-container">
                    <Sparkles className="w-3 h-3" />
                    <span className="text-[10px] font-bold uppercase tracking-widest">Logic Lock: Active</span>
                  </div>
                </div>
              )}
            </div>
          </motion.div>
        ))}
      </div>

      <div className="p-4 bg-surface-container-high/40 border-t border-outline-variant/10">
        <div className="flex justify-between text-[10px] text-outline font-mono">
          <span>Latency: 1.2s</span>
          <span>Tokens: 14.2k</span>
          <span>Context: 98%</span>
        </div>
      </div>
    </aside>
  );
};
