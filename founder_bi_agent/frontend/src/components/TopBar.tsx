import React from 'react';
import { motion } from 'motion/react';
import { Bell, Share2, Database, Activity } from 'lucide-react';

export const TopBar = () => {
  return (
    <header className="sticky top-0 w-full z-50 bg-surface/80 backdrop-blur-xl flex justify-between items-center h-16 px-8 ml-64 max-w-[calc(100%-16rem)] border-b border-outline-variant/10">
      <div className="flex items-center gap-8">
        <div className="text-xl font-black text-white tracking-tighter">Executive Intelligence</div>
        <nav className="hidden lg:flex gap-6">
          <a className="text-white font-bold border-b-2 border-primary-container pb-1 text-sm" href="#">
            Model Depth: Executive Reasoning
          </a>
        </nav>
      </div>

      <div className="flex items-center gap-4">
        <div className="flex items-center gap-2 bg-surface-container-lowest px-3 py-1.5 rounded-lg border border-outline-variant/10">
          <span className="w-2 h-2 rounded-full bg-secondary-container animate-pulse shadow-[0_0_8px_rgba(255,203,5,0.5)]"></span>
          <span className="text-[10px] text-on-surface uppercase tracking-widest font-bold">Active Reasoning</span>
        </div>
        
        <div className="flex gap-1">
          <button className="p-2 hover:bg-white/5 rounded-lg transition-all text-outline hover:text-white">
            <Share2 className="w-4 h-4" />
          </button>
          <button className="p-2 hover:bg-white/5 rounded-lg transition-all text-outline hover:text-white">
            <Database className="w-4 h-4" />
          </button>
          <button className="p-2 hover:bg-white/5 rounded-lg transition-all text-outline hover:text-white relative">
            <Bell className="w-4 h-4" />
            <span className="absolute top-2 right-2 w-1.5 h-1.5 bg-primary-container rounded-full"></span>
          </button>
        </div>
      </div>
    </header>
  );
};
