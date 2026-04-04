import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { motion } from 'motion/react';
import { Shield, Mail, Lock, User, ArrowRight } from 'lucide-react';
import { useAppContext } from '../context/AppContext';
import { registerAccount } from '../api';

const Signup = () => {
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const { setSession } = useAppContext();
  const navigate = useNavigate();

  const handleSignup = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      const res = await registerAccount(name, email, password);
      setSession(res.user, res.access_token);
      navigate('/');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Could not create account');
    } finally {
      setLoading(false);
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
          <h2 className="text-2xl font-bold tracking-tight">Create Account</h2>
          <p className="text-[var(--muted)] text-sm">Join Veridict and start verifying intents</p>
        </div>

        <form onSubmit={handleSignup} className="space-y-4">
          {error ? (
            <p className="text-sm text-red-500 bg-red-500/10 border border-red-500/20 rounded-xl px-3 py-2" role="alert">
              {error}
            </p>
          ) : null}

          <div className="space-y-2">
            <label className="text-xs font-bold uppercase tracking-widest text-[var(--muted)] ml-1">Full Name</label>
            <div className="relative">
              <User className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-[var(--muted)]" />
              <input 
                type="text" 
                required
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="John Doe"
                autoComplete="name"
                className="w-full pl-11 pr-4 py-3 rounded-xl bg-[var(--background)] border border-[var(--border)] outline-none focus:border-blue-500 transition-colors"
              />
            </div>
          </div>

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
                autoComplete="email"
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
                minLength={8}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••"
                autoComplete="new-password"
                className="w-full pl-11 pr-4 py-3 rounded-xl bg-[var(--background)] border border-[var(--border)] outline-none focus:border-blue-500 transition-colors"
              />
            </div>
            <p className="text-xs text-[var(--muted)] ml-1">At least 8 characters</p>
          </div>

          <button 
            type="submit"
            disabled={loading}
            className="w-full py-4 bg-[var(--primary)] text-[var(--primary-foreground)] rounded-xl font-bold flex items-center justify-center gap-2 hover:opacity-90 transition-all active:scale-[0.98] disabled:opacity-60 disabled:pointer-events-none"
          >
            {loading ? 'Creating account…' : (
              <>Create Account <ArrowRight className="w-4 h-4" /></>
            )}
          </button>
        </form>

        <div className="mt-8 text-center">
          <p className="text-sm text-[var(--muted)]">
            Already have an account?{' '}
            <Link to="/login" className="text-[var(--foreground)] font-bold hover:underline">
              Sign in
            </Link>
          </p>
        </div>
      </motion.div>
    </div>
  );
};

export default Signup;
