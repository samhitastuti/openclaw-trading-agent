import React from 'react';
import { motion } from 'motion/react';
import { Shield, Lock, AlertTriangle, XCircle, CheckCircle2, Search, Activity, Zap } from 'lucide-react';

const Policies = () => {
  const policies = [
    {
      id: 'POL-001',
      name: 'High Transaction Detection',
      description: 'Flags transactions exceeding standard liquidity thresholds (> $10,000).',
      status: 'ACTIVE',
      severity: 'WARNING',
      icon: AlertTriangle
    },
    {
      id: 'POL-002',
      name: 'Critical Value Limit',
      description: 'Blocks transactions exceeding maximum safety limits (> $25,000).',
      status: 'ACTIVE',
      severity: 'BLOCKED',
      icon: XCircle
    },
    {
      id: 'POL-003',
      name: 'Urgent Intent Block',
      description: 'Blocks executions containing emotional or urgent sentiment (e.g., "urgent", "all funds").',
      status: 'ACTIVE',
      severity: 'BLOCKED',
      icon: XCircle
    },
    {
      id: 'POL-004',
      name: 'Unverified Asset Flag',
      description: 'Warns when an intent involves an asset not currently in the verified allowlist.',
      status: 'ACTIVE',
      severity: 'WARNING',
      icon: AlertTriangle
    },
    {
      id: 'POL-005',
      name: 'Standard Intent Verification',
      description: 'Ensures basic intent structure (action, asset, amount) is present and valid.',
      status: 'ACTIVE',
      severity: 'ALLOWED',
      icon: CheckCircle2
    }
  ];

  return (
    <div className="flex-1 px-8 py-12 max-w-6xl mx-auto w-full">
      <motion.div 
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="flex flex-col md:flex-row items-center justify-between gap-8 mb-12"
      >
        <div>
          <h1 className="text-4xl font-bold tracking-tight mb-2">Armoriq Policy Engine</h1>
          <p className="text-[var(--muted)]">Manage and monitor the rules governing your autonomous agents.</p>
        </div>
        <div className="flex items-center gap-4">
          <button className="px-5 py-2.5 bg-[var(--primary)] text-[var(--primary-foreground)] rounded-xl text-sm font-bold flex items-center gap-2 hover:opacity-90 transition-all">
            <Zap className="w-4 h-4" />
            New Policy
          </button>
          <button className="px-5 py-2.5 border border-[var(--border)] rounded-xl text-sm font-bold hover:bg-[var(--accent)] transition-all">
            Export Rules
          </button>
        </div>
      </motion.div>

      <div className="grid grid-cols-1 gap-6">
        {policies.map((policy, i) => (
          <motion.div
            key={policy.id}
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: i * 0.1 }}
            className="p-6 rounded-2xl border border-[var(--border)] glass card-shadow flex flex-col md:flex-row items-center gap-6 group hover:border-blue-500/30 transition-all"
          >
            <div className={`w-14 h-14 rounded-xl flex items-center justify-center shrink-0 ${
              policy.severity === 'ALLOWED' ? 'bg-emerald-500/10 text-emerald-500' :
              policy.severity === 'WARNING' ? 'bg-amber-500/10 text-amber-500' : 'bg-rose-500/10 text-rose-500'
            }`}>
              <policy.icon className="w-7 h-7" />
            </div>
            <div className="flex-1 text-center md:text-left">
              <div className="flex items-center justify-center md:justify-start gap-3 mb-1">
                <h3 className="text-xl font-bold">{policy.name}</h3>
                <span className="px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-500 text-[10px] font-bold tracking-widest uppercase">
                  {policy.status}
                </span>
              </div>
              <p className="text-sm text-[var(--muted)] leading-relaxed">{policy.description}</p>
            </div>
            <div className="flex items-center gap-8 shrink-0">
              <div className="text-center md:text-right">
                <div className="text-[10px] font-bold uppercase text-[var(--muted)] mb-1">Severity</div>
                <div className={`text-sm font-bold ${
                  policy.severity === 'ALLOWED' ? 'text-emerald-500' :
                  policy.severity === 'WARNING' ? 'text-amber-500' : 'text-rose-500'
                }`}>
                  {policy.severity}
                </div>
              </div>
              <div className="text-center md:text-right">
                <div className="text-[10px] font-bold uppercase text-[var(--muted)] mb-1">Policy ID</div>
                <div className="text-sm font-mono font-bold opacity-60">{policy.id}</div>
              </div>
              <button className="p-2 rounded-lg hover:bg-[var(--accent)] transition-colors">
                <Lock className="w-5 h-5 text-[var(--muted)]" />
              </button>
            </div>
          </motion.div>
        ))}
      </div>

      <div className="mt-12 p-8 rounded-3xl border border-dashed border-[var(--border)] text-center">
        <p className="text-[var(--muted)] text-sm mb-4">Looking for custom policy integration?</p>
        <button className="text-blue-500 font-bold hover:underline">Contact our engineering team</button>
      </div>
    </div>
  );
};

export default Policies;
