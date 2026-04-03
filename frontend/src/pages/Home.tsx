import React, { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'motion/react';
import { 
  Search, 
  Activity, 
  CheckCircle2, 
  AlertTriangle, 
  XCircle, 
  ArrowRight, 
  Send,
  History,
  Lock,
  Zap,
  MousePointer2,
  Sparkles
} from 'lucide-react';
import { evaluateIntent } from '../services/armoriqEngine';
import { EvaluationResult } from '../types';
import { useAppContext } from '../context/AppContext';
import DecisionCard from '../components/DecisionCard';

const Hero = () => (
  <div className="flex flex-col justify-center h-full max-w-xl relative z-10">
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.6 }}
    >
      <span className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-blue-500/10 text-blue-500 text-xs font-bold mb-6 border border-blue-500/20">
        <Zap className="w-3 h-3 text-yellow-500" />
        Armoriq Policy Intelligence v2.4
      </span>
      <h1 className="text-6xl font-bold tracking-tighter leading-[1.1] mb-6">
        Intent-enforced,<br />
        Autonomous trading.
      </h1>
      <p className="text-xl text-[var(--muted)] leading-relaxed mb-8">
        Veridict ensures every financial action is verified before execution using Armoriq policy intelligence. Secure your autonomous agents with intent-level enforcement.
      </p>
      <div className="flex items-center gap-4">
        <button className="px-8 py-4 bg-[var(--primary)] text-[var(--primary-foreground)] rounded-xl font-bold flex items-center gap-2 hover:gap-3 transition-all shadow-lg hover:shadow-blue-500/20">
          Get Started <ArrowRight className="w-5 h-5" />
        </button>
        <button className="px-8 py-4 border border-[var(--border)] rounded-xl font-bold hover:bg-[var(--accent)] transition-all glass">
          View Docs
        </button>
      </div>
    </motion.div>
  </div>
);

const Home = () => {
  const { addLog, auditLogs } = useAppContext();
  const [input, setInput] = useState('');
  const [isEvaluating, setIsEvaluating] = useState(false);
  const [result, setResult] = useState<EvaluationResult | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (inputRef.current) inputRef.current.focus();
  }, []);

  const handleEvaluate = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!input.trim() || isEvaluating) return;

    setIsEvaluating(true);
    setResult(null);

    try {
      const evaluation = await evaluateIntent(input);
      setResult(evaluation);
      addLog({ 
        id: Math.random().toString(36).substr(2, 9), 
        input: evaluation.input, 
        status: evaluation.status, 
        timestamp: evaluation.timestamp,
        decision: evaluation.reason,
        confidence: evaluation.confidence,
        risks: evaluation.triggeredRules
      });
    } catch (error) {
      console.error('Evaluation failed', error);
    } finally {
      setIsEvaluating(false);
    }
  };

  return (
    <div className="flex-1 flex flex-col relative">
      <main className="flex-1 flex flex-col lg:flex-row px-8 py-12 gap-12 max-w-[1600px] mx-auto w-full relative z-10">
        {/* Left Side: Hero */}
        <div className="lg:w-[40%]">
          <Hero />
        </div>

        {/* Right Side: Decision Flow */}
        <div className="lg:w-[60%] flex flex-col gap-8">
          <div className="flex flex-col md:flex-row gap-6 items-stretch relative">
            <div className="hidden md:block absolute top-1/2 left-0 w-full h-0.5 bg-[var(--border)] -z-10 opacity-50" />

            {/* Card 1: Parse Intent */}
            <DecisionCard 
              title="1. Parse Intent" 
              icon={Search} 
              isActive={isEvaluating && !result}
            >
              <AnimatePresence mode="wait">
                {input ? (
                  <motion.div 
                    key="input"
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: -10 }}
                    className="space-y-2"
                  >
                    <div className="text-sm font-mono p-3 rounded-xl bg-[var(--background)] border border-[var(--border)] break-all glass shadow-inner">
                      "{input}"
                    </div>
                    {result && (
                      <motion.div 
                        initial={{ opacity: 0, scale: 0.9 }}
                        animate={{ opacity: 1, scale: 1 }}
                        className="flex flex-wrap gap-2"
                      >
                        <span className="px-2 py-1 rounded-lg bg-blue-500/10 text-blue-500 text-[10px] font-bold uppercase border border-blue-500/20">{result.parsedIntent.action}</span>
                        <span className="px-2 py-1 rounded-lg bg-purple-500/10 text-purple-500 text-[10px] font-bold uppercase border border-purple-500/20">{result.parsedIntent.asset}</span>
                        <span className="px-2 py-1 rounded-lg bg-orange-500/10 text-orange-500 text-[10px] font-bold uppercase border border-orange-500/20">${result.parsedIntent.amount.toLocaleString()}</span>
                      </motion.div>
                    )}
                  </motion.div>
                ) : (
                  <motion.div 
                    key="placeholder"
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    className="text-center text-[var(--muted)] italic text-sm flex flex-col items-center gap-2"
                  >
                    <MousePointer2 className="w-5 h-5 opacity-20 animate-bounce" />
                    Waiting for input...
                  </motion.div>
                )}
              </AnimatePresence>
            </DecisionCard>

            {/* Card 2: Armoriq Policies */}
            <DecisionCard 
              title="2. Armoriq Policies" 
              icon={Lock} 
              isActive={isEvaluating}
            >
              <AnimatePresence mode="wait">
                {isEvaluating ? (
                  <motion.div 
                    key="evaluating"
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    exit={{ opacity: 0 }}
                    className="flex flex-col items-center gap-3"
                  >
                    <Activity className="w-6 h-6 text-blue-500 animate-pulse" />
                    <span className="text-xs font-bold tracking-tight animate-pulse text-blue-500">Evaluating with Armoriq...</span>
                  </motion.div>
                ) : result ? (
                  <motion.div 
                    key="result"
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="space-y-2"
                  >
                    <div className="flex items-center gap-2 mb-2">
                      <span className="px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-500 text-[10px] font-bold tracking-widest border border-emerald-500/20">ACTIVE</span>
                    </div>
                    {result.triggeredRules.length > 0 ? (
                      <div className="space-y-1">
                        {result.triggeredRules.map((rule, i) => (
                          <div key={i} className="flex items-center gap-2 text-[11px] font-medium text-[var(--muted)]">
                            <AlertTriangle className="w-3 h-3 text-amber-500" />
                            {rule}
                          </div>
                        ))}
                      </div>
                    ) : (
                      <div className="flex items-center gap-2 text-[11px] font-medium text-emerald-500">
                        <CheckCircle2 className="w-3 h-3" />
                        All standard policies passed
                      </div>
                    )}
                  </motion.div>
                ) : (
                  <motion.div 
                    key="placeholder"
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    className="text-center text-[var(--muted)] italic text-sm"
                  >
                    Awaiting intent parse...
                  </motion.div>
                )}
              </AnimatePresence>
            </DecisionCard>

            {/* Card 3: Final Decision */}
            <DecisionCard 
              title="3. Final Decision" 
              icon={Activity} 
              status={result?.status}
              confidence={result?.confidence}
              triggeredRules={result?.triggeredRules}
              reason={result?.reason}
            >
              <AnimatePresence mode="wait">
                {!result && (
                  <motion.div 
                    key="pending"
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    className="text-center text-[var(--muted)] font-bold tracking-[0.3em] text-xl opacity-10"
                  >
                    PENDING
                  </motion.div>
                )}
              </AnimatePresence>
            </DecisionCard>
          </div>

          {/* Logs Panel (Mini) */}
          <div className="mt-auto">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-2 text-[var(--muted)]">
                <History className="w-4 h-4" />
                <h4 className="text-xs font-bold uppercase tracking-widest">Recent Evaluations</h4>
              </div>
              {auditLogs.length > 0 && (
                <span className="text-[10px] font-bold text-blue-500 uppercase tracking-widest">Live Stream</span>
              )}
            </div>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {auditLogs.slice(0, 3).length > 0 ? auditLogs.slice(0, 3).map((log) => (
                <motion.div 
                  key={log.id} 
                  initial={{ opacity: 0, scale: 0.9 }}
                  animate={{ opacity: 1, scale: 1 }}
                  className="p-4 rounded-2xl border border-[var(--border)] glass flex items-center justify-between card-shadow hover:border-blue-500/30 transition-all cursor-default"
                >
                  <div className="flex flex-col gap-1 overflow-hidden">
                    <span className="text-[10px] font-mono text-[var(--muted)] truncate">"{log.input}"</span>
                    <span className="text-[10px] font-bold opacity-60">{new Date(log.timestamp).toLocaleTimeString()}</span>
                  </div>
                  <div className={`px-2 py-1 rounded-lg text-[9px] font-bold uppercase border ${
                    log.status === 'ALLOWED' ? 'bg-emerald-500/10 text-emerald-500 border-emerald-500/20' :
                    log.status === 'WARNING' ? 'bg-amber-500/10 text-amber-500 border-amber-500/20' : 'bg-rose-500/10 text-rose-500 border-rose-500/20'
                  }`}>
                    {log.status}
                  </div>
                </motion.div>
              )) : (
                <div className="col-span-3 py-10 text-center border-2 border-dashed border-[var(--border)] rounded-[2rem] glass flex flex-col items-center gap-3">
                  <div className="w-10 h-10 rounded-full bg-[var(--accent)] flex items-center justify-center">
                    <Sparkles className="w-5 h-5 text-[var(--muted)] opacity-50" />
                  </div>
                  <div>
                    <p className="text-sm font-bold text-[var(--muted)]">No evaluations yet</p>
                    <p className="text-[11px] text-[var(--muted)] opacity-60 max-w-[200px] mx-auto mt-1">
                      Type a trade intent below to see the Armoriq engine in action.
                    </p>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      </main>

      {/* Floating Input Bar */}
      <div className="fixed bottom-12 left-1/2 -translate-x-1/2 w-full max-w-2xl px-6 z-50">
        <form 
          onSubmit={handleEvaluate}
          className="relative group"
        >
          <div className="absolute -inset-1 bg-gradient-to-r from-blue-500 to-purple-500 rounded-[2rem] blur opacity-20 group-focus-within:opacity-40 transition duration-1000"></div>
          <div className="relative flex items-center bg-[var(--background)] border border-[var(--border)] rounded-[2rem] p-2 pl-6 card-shadow glass focus-within:border-blue-500/50 transition-all">
            <Search className="w-5 h-5 text-[var(--muted)] mr-4" />
            <input 
              ref={inputRef}
              type="text" 
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Ask AI: 'BUY 50 AAPL' or 'transfer all funds'..."
              className="flex-1 bg-transparent border-none outline-none text-sm font-medium placeholder:text-[var(--muted)] placeholder:font-normal"
            />
            <button 
              type="submit"
              disabled={isEvaluating || !input.trim()}
              className="ml-4 p-3 bg-[var(--primary)] text-[var(--primary-foreground)] rounded-full hover:scale-105 active:scale-95 transition-all disabled:opacity-50 disabled:scale-100 shadow-lg"
            >
              {isEvaluating ? (
                <Activity className="w-5 h-5 animate-spin" />
              ) : (
                <Send className="w-5 h-5" />
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default Home;
