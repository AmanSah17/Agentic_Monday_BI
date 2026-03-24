import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { User, Lock, LogIn } from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';

export const LoginPage: React.FC<{ onToggle: () => void }> = ({ onToggle }) => {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const { login } = useAuth();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);
    setError('');

    try {
      const resp = await fetch('/api/v1/user/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body: new URLSearchParams({ username, password }),
      });

      if (!resp.ok) {
        throw new Error('Invalid username or password');
      }

      const data = await resp.json();
      await login(data.access_token);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Login failed');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-[#0a0a0f] p-4 relative overflow-hidden">
      {/* Background purely decorative elements */}
      <div className="absolute top-[-10%] left-[-10%] w-[40%] h-[40%] bg-primary/20 rounded-full blur-[120px]" />
      <div className="absolute bottom-[-10%] right-[-10%] w-[40%] h-[40%] bg-secondary-container/20 rounded-full blur-[120px]" />

      <motion.div 
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        whileHover={{ y: -5 }}
        className="w-full max-w-md bg-[#16161e] rounded-2xl shadow-[0_20px_50px_rgba(0,0,0,0.5)] border border-white/10 overflow-hidden relative z-10"
      >
        <div className="bg-primary p-8 text-white text-center">
          <h1 className="text-3xl font-black tracking-tighter uppercase italic">Monday BI Agent</h1>
          <p className="mt-3 text-sm text-primary-content/90 font-medium leading-relaxed">
            Quick, accurate answers to your founder-level business questions across all your data sources.
          </p>
        </div>
        
        <form onSubmit={handleSubmit} className="p-8 space-y-6">
          {error && (
            <motion.div 
              initial={{ opacity: 0, x: -10 }}
              animate={{ opacity: 1, x: 0 }}
              className="p-4 bg-red-500/10 text-red-400 text-sm rounded-xl border border-red-500/20"
            >
              {error}
            </motion.div>
          )}
          
          <div className="space-y-4">
            <div className="relative group">
              <User className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-500 group-focus-within:text-primary transition-colors w-5 h-5" />
              <input
                type="text"
                placeholder="Username"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                className="w-full pl-12 pr-4 py-4 bg-white/5 border border-white/10 rounded-xl focus:ring-2 focus:ring-primary focus:border-transparent outline-none transition-all text-white placeholder:text-slate-600"
                required
              />
            </div>
            
            <div className="relative group">
              <Lock className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-500 group-focus-within:text-primary transition-colors w-5 h-5" />
              <input
                type="password"
                placeholder="Password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full pl-12 pr-4 py-4 bg-white/5 border border-white/10 rounded-xl focus:ring-2 focus:ring-primary focus:border-transparent outline-none transition-all text-white placeholder:text-slate-600"
                required
              />
            </div>
          </div>
          
          <motion.button
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
            type="submit"
            disabled={isSubmitting}
            className="w-full py-4 bg-primary text-white rounded-xl font-black uppercase tracking-widest flex items-center justify-center gap-3 hover:brightness-110 transition-all disabled:opacity-50 shadow-xl shadow-primary/20 group"
          >
            {isSubmitting ? 'Authenticating...' : 'Sign In'}
            <LogIn className="w-5 h-5 group-hover:translate-x-1 transition-transform" />
          </motion.button>
          
          <div className="text-center text-sm">
            <span className="text-slate-500">Don't have an account?</span>{' '}
            <button 
              type="button" 
              onClick={onToggle}
              className="text-primary font-black hover:text-white transition-colors"
            >
              Register Now
            </button>
          </div>
        </form>
      </motion.div>
    </div>
  );
};
