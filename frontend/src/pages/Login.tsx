import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { motion } from 'motion/react';
import { Shield, Mail, Lock, ArrowRight } from 'lucide-react';
import { useAppContext } from '../context/AppContext';

const Login = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const { setUser } = useAppContext();
  const navigate = useNavigate();

  const handleLogin = (e: React.FormEvent) => {
    e.preventDefault();
    if (email && password) {
      setUser({ email });
      navigate('/');
    }
  };

  return (
    <div className="flex-1 flex items-center justify-center px-8 py-12">
      <motion.div 
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="w-full max-w-md p-8 rounded-3xl border border-[var(--border)] glass card-shadow"
      >
        <div className="flex flex-col items-center mb-8">
          <div className="w-12 h-12 bg-black dark:bg-white rounded-xl flex items-center justify-center mb-4">
            <Shield className="w-6 h-6 text-white dark:text-black" />
          </div>
          <h2 className="text-2xl font-bold tracking-tight">Welcome back</h2>
          <p className="text-[var(--muted)] text-sm">Enter your credentials to access Veridict</p>
        </div>

        <form onSubmit={handleLogin} className="space-y-4">
          <div className="space-y-2">
            <label className="text-xs font-bold uppercase tracking-widest text-[var(--muted)] ml-1">Email Address</label>
            <div className="relative">
              <Mail className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-[var(--muted)]" />
              <input 
                type="email" 
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="name@company.com"
                className="w-full pl-11 pr-4 py-3 rounded-xl bg-[var(--background)] border border-[var(--border)] outline-none focus:border-blue-500 transition-colors"
              />
            </div>
          </div>

          <div className="space-y-2">
            <label className="text-xs font-bold uppercase tracking-widest text-[var(--muted)] ml-1">Password</label>
            <div className="relative">
              <Lock className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-[var(--muted)]" />
              <input 
                type="password" 
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••"
                className="w-full pl-11 pr-4 py-3 rounded-xl bg-[var(--background)] border border-[var(--border)] outline-none focus:border-blue-500 transition-colors"
              />
            </div>
          </div>

          <button 
            type="submit"
            className="w-full py-4 bg-[var(--primary)] text-[var(--primary-foreground)] rounded-xl font-bold flex items-center justify-center gap-2 hover:opacity-90 transition-all active:scale-[0.98]"
          >
            Sign In <ArrowRight className="w-4 h-4" />
          </button>
        </form>

        <div className="mt-8 text-center">
          <p className="text-sm text-[var(--muted)]">
            Don't have an account?{' '}
            <Link to="/signup" className="text-[var(--foreground)] font-bold hover:underline">
              Sign up
            </Link>
          </p>
        </div>
      </motion.div>
    </div>
  );
};

export default Login;
