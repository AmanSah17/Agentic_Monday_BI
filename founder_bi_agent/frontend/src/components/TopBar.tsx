import React from 'react';
import { motion } from 'motion/react';
import { Bell, Share2, Database, Activity } from 'lucide-react';

export const TopBar = () => {
  return (
    <header className="sticky top-0 w-full z-50 bg-surface/80 backdrop-blur-xl flex justify-between items-center h-16 px-8 ml-64 max-w-[calc(100%-16rem)] border-b border-outline-variant/10">
      <div className="flex items-center gap-8">
        <div className="flex flex-col">
          <div className="text-xl font-black text-white tracking-tighter uppercase italic">Monday BI Agent</div>
          <div className="text-[10px] text-primary-container font-bold tracking-[0.2em] -mt-1">INTEL-DRIVEN ANALYTICS</div>
        </div>
        
        <div className="hidden lg:flex items-center gap-4 text-xs">
          <div className="px-3 py-1 bg-white/5 rounded-full border border-white/10 text-outline flex items-center gap-2">
            <span className="w-1.5 h-1.5 rounded-full bg-green-500 shadow-[0_0_8px_rgba(34,197,94,0.5)]"></span>
            Real-time API
          </div>
          <div className="px-3 py-1 bg-white/5 rounded-full border border-white/10 text-outline flex items-center gap-2">
            <span className="w-1.5 h-1.5 rounded-full bg-blue-500 shadow-[0_0_8px_rgba(59,130,246,0.5)]"></span>
            MCP Tool
          </div>
          <div className="px-3 py-1 bg-white/5 rounded-full border border-white/10 text-outline flex items-center gap-2">
            <span className="w-1.5 h-1.5 rounded-full bg-purple-500 shadow-[0_0_8px_rgba(168,85,247,0.5)]"></span>
            DAG Reasoning
          </div>
        </div>
      </div>

      <div className="flex items-center gap-6">
        <div className="flex items-center gap-2 bg-surface-container-lowest px-4 py-2 rounded-xl border border-outline-variant/10 group cursor-help relative">
          <Activity className="w-4 h-4 text-primary-container animate-pulse" />
          <span className="text-[10px] text-on-surface uppercase tracking-widest font-black">System Ready</span>
          
          {/* Tooltip on hover */}
          <div className="absolute top-full right-0 mt-2 w-72 bg-[#16161e] border border-white/10 rounded-xl p-4 shadow-2xl transition-all opacity-0 invisible group-hover:opacity-100 group-hover:visible z-[100]">
            <h4 className="text-xs font-black text-white uppercase tracking-widest mb-2 border-b border-white/5 pb-2">About Monday BI Agent</h4>
            <p className="text-[10px] text-slate-400 leading-relaxed mb-3">
              An advanced AI agent that interprets messy business data, generates dynamic SQL, and provides executive-level insights from Monday.com boards.
            </p>
            <div className="space-y-2">
              <p className="text-[9px] font-bold text-primary-container uppercase tracking-widest">Core Capabilities:</p>
              <ul className="text-[9px] text-slate-500 space-y-1">
                <li>• Intelligent DAG-based reasoning flow</li>
                <li>• Dynamic SQL query generation & validation</li>
                <li>• Cross-board data synthesis and cleaning</li>
                <li>• Real-time insights and visualization</li>
              </ul>
            </div>
          </div>
        </div>
        
        <div className="flex items-center gap-2">
          <button className="p-2.5 hover:bg-white/5 rounded-xl transition-all text-outline hover:text-white border border-transparent hover:border-white/10">
            <Share2 className="w-4 h-4" />
          </button>
          <button className="p-2.5 hover:bg-white/5 rounded-xl transition-all text-outline hover:text-white border border-transparent hover:border-white/10">
            <Database className="w-4 h-4" />
          </button>
          <button className="p-2.5 hover:bg-white/5 rounded-xl transition-all text-outline hover:text-white border border-transparent hover:border-white/10 relative">
            <Bell className="w-4 h-4" />
            <span className="absolute top-2 right-2 w-2 h-2 bg-primary rounded-full border-2 border-surface"></span>
          </button>
        </div>
      </div>
    </header>
  );
};
