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

export type ViewMode = 'chat' | 'dashboard' | 'data-map' | 'library' | 'admin';

interface NavItem {
  icon: React.ComponentType<{ className?: string }>;
  label: string;
  view: ViewMode;
}

const navItems: NavItem[] = [
  { icon: MessageSquare, label: 'Chat', view: 'chat' },
  { icon: LayoutDashboard, label: 'Dashboard', view: 'dashboard' },
  { icon: Network, label: 'Data Map', view: 'data-map' },
  { icon: Library, label: 'Library', view: 'library' },
  { icon: Settings, label: 'Admin', view: 'admin' },
];

interface SidebarProps {
  currentView: ViewMode;
  onViewChange: (view: ViewMode) => void;
}

export const Sidebar: React.FC<SidebarProps> = ({ currentView, onViewChange }) => {
  return (
    <aside className="fixed left-0 top-0 h-full w-64 z-40 bg-surface-container-low border-r border-outline-variant/10 flex flex-col">
      <div className="px-6 py-8">
        <h1 className="text-lg font-bold tracking-tighter text-white">Executive Intelligence</h1>
        <p className="text-[10px] text-primary tracking-widest uppercase mt-1 opacity-60">Digital Architect v1.0</p>
      </div>

      <nav className="flex-1 space-y-1">
        {navItems.map((item) => (
          <a
            key={item.view}
            href={`/${item.view}`}
            onClick={(e) => {
              e.preventDefault();
              onViewChange(item.view);
            }}
            className={cn(
              "w-full flex items-center gap-3 px-6 py-4 transition-all duration-300 group text-left cursor-pointer",
              currentView === item.view
                ? "border-l-2 border-primary-container text-white bg-gradient-to-r from-primary-container/10 to-transparent" 
                : "text-outline hover:text-white hover:bg-white/5"
            )}
          >
            <item.icon className={cn("w-5 h-5", currentView === item.view ? "text-primary-container" : "text-outline group-hover:text-white")} />
            <span className="font-medium">{item.label}</span>
            {currentView === item.view && (
              <ChevronRight className="ml-auto w-4 h-4 text-primary-container" />
            )}
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
