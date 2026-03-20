import React from 'react';
import { motion } from 'motion/react';
import { 
  MessageSquare, 
  LayoutDashboard, 
  Network, 
  Library, 
  Settings, 
  ChevronRight 
} from 'lucide-react';
import { cn } from '../lib/utils';

const navItems = [
  { icon: MessageSquare, label: 'Chat', active: true },
  { icon: LayoutDashboard, label: 'Dashboard' },
  { icon: Network, label: 'Data Map' },
  { icon: Library, label: 'Library' },
  { icon: Settings, label: 'Admin' },
];

export const Sidebar = () => {
  return (
    <aside className="fixed left-0 top-0 h-full w-64 z-40 bg-surface-container-low border-r border-outline-variant/10 flex flex-col">
      <div className="px-6 py-8">
        <h1 className="text-lg font-bold tracking-tighter text-white">Executive Intelligence</h1>
        <p className="text-[10px] text-primary tracking-widest uppercase mt-1 opacity-60">Digital Architect v1.0</p>
      </div>

      <nav className="flex-1 space-y-1">
        {navItems.map((item) => (
          <a
            key={item.label}
            href="#"
            className={cn(
              "flex items-center gap-3 px-6 py-4 transition-all duration-300 group",
              item.active 
                ? "border-l-2 border-primary-container text-white bg-gradient-to-r from-primary-container/10 to-transparent" 
                : "text-outline hover:text-white hover:bg-white/5"
            )}
          >
            <item.icon className={cn("w-5 h-5", item.active ? "text-primary-container" : "text-outline group-hover:text-white")} />
            <span className="font-medium">{item.label}</span>
          </a>
        ))}
      </nav>

      <div className="p-6 mt-auto border-t border-outline-variant/10">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-full bg-surface-container-highest overflow-hidden border border-outline-variant/20">
            <img 
              src="https://picsum.photos/seed/executive/100/100" 
              alt="User Profile" 
              className="w-full h-full object-cover"
              referrerPolicy="no-referrer"
            />
          </div>
          <div>
            <p className="text-xs font-bold text-white">Alex Sterling</p>
            <p className="text-[10px] text-outline">Chief Architect</p>
          </div>
        </div>
      </div>
    </aside>
  );
};
