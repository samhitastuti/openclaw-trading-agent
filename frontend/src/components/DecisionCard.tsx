import React from 'react';
import { motion, AnimatePresence } from 'motion/react';
import { AlertTriangle, CheckCircle2, XCircle, ShieldCheck, ChevronDown } from 'lucide-react';
import { DecisionStatus } from '../types';

interface DecisionCardProps {
  title: string;
  icon: any;
  children: React.ReactNode;
  isActive?: boolean;
  status?: DecisionStatus;
  confidence?: number;
  triggeredRules?: string[];
  reason?: string;
}

const DecisionCard: React.FC<DecisionCardProps> = ({ 
  title, 
  icon: Icon, 
  children, 
  isActive, 
  status,
  confidence,
  triggeredRules,
  reason
}) => {
  const getStatusColor = () => {
    if (status === 'ALLOWED') return 'border-emerald-500/30 bg-emerald-50/30 dark:bg-emerald-500/5 shadow-[0_0_20px_rgba(16,185,129,0.1)]';
    if (status === 'WARNING') return 'border-amber-500/30 bg-amber-50/30 dark:bg-amber-500/5 shadow-[0_0_20px_rgba(245,158,11,0.1)]';
    if (status === 'BLOCKED') return 'border-rose-500/30 bg-rose-50/30 dark:bg-rose-500/5 shadow-[0_0_20px_rgba(239,68,68,0.1)]';
    return 'border-[var(--border)] bg-[var(--card)]';
  };

  const getStatusIcon = () => {
    if (status === 'ALLOWED') return <CheckCircle2 className="w-6 h-6 text-emerald-500" />;
    if (status === 'WARNING') return <AlertTriangle className="w-6 h-6 text-amber-500" />;
    if (status === 'BLOCKED') return <XCircle className="w-6 h-6 text-rose-500" />;
    return null;
  };

  return (
    <motion.div 
      layout
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ 
        opacity: 1, 
        scale: status ? 1 : (isActive ? 1.05 : 1),
        boxShadow: status ? (
          status === 'ALLOWED' ? '0 0 30px rgba(16,185,129,0.2)' :
          status === 'WARNING' ? '0 0 30px rgba(245,158,11,0.2)' :
          '0 0 30px rgba(239,68,68,0.2)'
        ) : '0 0 0px rgba(0,0,0,0)',
        transition: { 
          duration: 0.4, 
          ease: "easeOut",
        }
      }}
      className={`flex-1 p-6 rounded-3xl border-2 transition-all duration-500 card-shadow ${getStatusColor()} ${isActive ? 'z-10' : 'z-0'}`}
    >
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <div className="p-2.5 rounded-xl bg-[var(--background)] border border-[var(--border)] shadow-sm">
            <Icon className="w-5 h-5" />
          </div>
          <h3 className="font-bold text-xs uppercase tracking-[0.2em] text-[var(--muted)]">{title}</h3>
        </div>
        {isActive && (
          <motion.div 
            animate={{ opacity: [0.5, 1], scale: [1, 1.2] }} 
            transition={{ repeat: Infinity, repeatType: "reverse", duration: 0.75 }}
            className="w-2 h-2 rounded-full bg-blue-500 shadow-[0_0_8px_rgba(59,130,246,0.5)]"
          />
        )}
      </div>

      <div className="min-h-[140px] flex flex-col justify-center">
        <AnimatePresence mode="wait">
          {children}
        </AnimatePresence>

        <AnimatePresence mode="wait">
          {status && (
            <motion.div 
              key={status}
              initial={{ opacity: 0, y: 20, scale: 0.98 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              exit={{ opacity: 0, y: -10, scale: 0.98 }}
              transition={{ duration: 0.5, ease: [0.23, 1, 0.32, 1] }}
              className="mt-6 pt-6 border-t border-[var(--border)] space-y-4"
            >
              {/* Status & Confidence */}
              <div className="flex items-center justify-between">
                <motion.div 
                  initial={{ scale: 0.9, opacity: 0 }}
                  animate={{ scale: 1, opacity: 1 }}
                  transition={{ delay: 0.1, duration: 0.4 }}
                  className="flex items-center gap-2 font-bold text-lg"
                >
                  <motion.div
                    initial={{ rotate: -20, scale: 0.5 }}
                    animate={{ rotate: 0, scale: 1 }}
                    transition={{ type: "spring", stiffness: 300, damping: 15, delay: 0.2 }}
                  >
                    {getStatusIcon()}
                  </motion.div>
                  <span className={
                    status === 'ALLOWED' ? 'text-emerald-500' : 
                    status === 'WARNING' ? 'text-amber-500' : 'text-rose-500'
                  }>{status}</span>
                </motion.div>
                {confidence !== undefined && (
                  <motion.div 
                    initial={{ opacity: 0, x: 10 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: 0.3 }}
                    className="text-right"
                  >
                    <div className="text-[10px] uppercase font-bold text-[var(--muted)] mb-1">Confidence</div>
                    <div className="text-sm font-bold">{confidence}%</div>
                  </motion.div>
                )}
              </div>

              {/* Confidence Bar */}
              {confidence !== undefined && (
                <div className="h-1.5 w-full bg-[var(--accent)] rounded-full overflow-hidden">
                  <motion.div 
                    initial={{ width: 0 }}
                    animate={{ width: `${confidence}%` }}
                    transition={{ duration: 1.2, ease: [0.23, 1, 0.32, 1], delay: 0.4 }}
                    className={`h-full rounded-full ${
                      status === 'ALLOWED' ? 'bg-emerald-500' : 
                      status === 'WARNING' ? 'bg-amber-500' : 'bg-rose-500'
                    }`}
                  />
                </div>
              )}

              {/* Risk Flags as Chips */}
              {triggeredRules && triggeredRules.length > 0 && (
                <motion.div 
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  transition={{ delay: 0.5 }}
                  className="flex flex-wrap gap-2"
                >
                  {triggeredRules.map((rule, i) => (
                    <motion.span 
                      key={i}
                      initial={{ scale: 0.8, opacity: 0 }}
                      animate={{ scale: 1, opacity: 1 }}
                      transition={{ delay: 0.5 + (i * 0.1) }}
                      className="px-2 py-1 rounded-lg bg-rose-500/10 text-rose-500 text-[9px] font-bold uppercase border border-rose-500/20"
                    >
                      {rule}
                    </motion.span>
                  ))}
                </motion.div>
              )}

              {/* Reason Dropdown Style */}
              {reason && (
                <motion.div 
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.6 }}
                  className="p-3 rounded-xl bg-[var(--background)] border border-[var(--border)] text-[11px] leading-relaxed opacity-80 font-medium"
                >
                  <div className="flex items-center gap-2 mb-1 text-[10px] uppercase font-bold text-[var(--muted)]">
                    <ShieldCheck className="w-3 h-3" />
                    Policy Reasoning
                  </div>
                  {reason}
                </motion.div>
              )}
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </motion.div>
  );
};

export default DecisionCard;
