import React, { useState } from 'react';
import { motion } from 'motion/react';
import { 
  Search, 
  Filter, 
  Download, 
  ChevronLeft, 
  ChevronRight, 
  ExternalLink,
  Activity,
  CheckCircle2,
  AlertTriangle,
  XCircle,
  Database,
  SearchX,
  Trash2,
  FileJson,
  FileSpreadsheet
} from 'lucide-react';
import { useAppContext } from '../context/AppContext';

const Logs = () => {
  const { auditLogs, exportLogs, clearLogs } = useAppContext();
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('ALL');

  const filteredLogs = auditLogs.filter(log => {
    const matchesSearch = log.input.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         log.id.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesStatus = statusFilter === 'ALL' || log.status === statusFilter;
    return matchesSearch && matchesStatus;
  });

  const stats = {
    total: auditLogs.length,
    allowed: auditLogs.filter(l => l.status === 'ALLOWED').length,
    warning: auditLogs.filter(l => l.status === 'WARNING').length,
    blocked: auditLogs.filter(l => l.status === 'BLOCKED').length,
  };

  const allowedPercentage = stats.total > 0 ? Math.round((stats.allowed / stats.total) * 100) : 0;
  const riskyPercentage = stats.total > 0 ? Math.round(((stats.warning + stats.blocked) / stats.total) * 100) : 0;

  return (
    <div className="flex-1 px-8 py-12 max-w-[1600px] mx-auto w-full">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="space-y-8"
      >
        {/* Header */}
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-6">
          <div>
            <h1 className="text-4xl font-bold tracking-tight mb-2">Audit Logs</h1>
            <p className="text-[var(--muted)]">Comprehensive record of all intent evaluations and policy enforcements.</p>
          </div>
          <div className="flex items-center gap-3">
            <button 
              onClick={clearLogs}
              className="p-2.5 rounded-xl border border-rose-500/20 text-rose-500 hover:bg-rose-500/10 transition-all glass"
              title="Clear all logs"
            >
              <Trash2 className="w-5 h-5" />
            </button>
            <div className="h-8 w-[1px] bg-[var(--border)] mx-2" />
            <button 
              onClick={() => exportLogs('json')}
              className="px-4 py-2.5 border border-[var(--border)] rounded-xl font-bold flex items-center gap-2 hover:bg-[var(--accent)] transition-all glass"
            >
              <FileJson className="w-4 h-4" />
              JSON
            </button>
            <button 
              onClick={() => exportLogs('csv')}
              className="px-6 py-2.5 bg-[var(--primary)] text-[var(--primary-foreground)] rounded-xl font-bold shadow-lg hover:shadow-blue-500/20 transition-all flex items-center gap-2"
            >
              <FileSpreadsheet className="w-4 h-4" />
              Export CSV
            </button>
          </div>
        </div>

        {/* Stats Summary */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="p-6 rounded-3xl border border-[var(--border)] glass card-shadow">
            <div className="text-xs font-bold text-[var(--muted)] uppercase tracking-widest mb-1">Total Evaluations</div>
            <div className="text-3xl font-bold">{stats.total}</div>
          </div>
          <div className="p-6 rounded-3xl border border-[var(--border)] glass card-shadow">
            <div className="text-xs font-bold text-emerald-500 uppercase tracking-widest mb-1">Approved</div>
            <div className="text-3xl font-bold text-emerald-500">{allowedPercentage}%</div>
          </div>
          <div className="p-6 rounded-3xl border border-[var(--border)] glass card-shadow">
            <div className="text-xs font-bold text-rose-500 uppercase tracking-widest mb-1">Risky/Blocked</div>
            <div className="text-3xl font-bold text-rose-500">{riskyPercentage}%</div>
          </div>
          <div className="p-6 rounded-3xl border border-[var(--border)] glass card-shadow">
            <div className="text-xs font-bold text-blue-500 uppercase tracking-widest mb-1">System Health</div>
            <div className="text-3xl font-bold text-blue-500">Optimal</div>
          </div>
        </div>

        {/* Filters */}
        <div className="flex flex-col md:flex-row gap-4">
          <div className="flex-1 relative group">
            <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-[var(--muted)] group-focus-within:text-blue-500 transition-colors" />
            <input 
              type="text" 
              placeholder="Search by intent or ID..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full pl-12 pr-4 py-3 rounded-2xl bg-[var(--card)] border border-[var(--border)] outline-none focus:border-blue-500/50 transition-all glass"
            />
          </div>
          <div className="flex items-center gap-2 p-1 rounded-2xl border border-[var(--border)] glass">
            {['ALL', 'ALLOWED', 'WARNING', 'BLOCKED'].map((status) => (
              <button
                key={status}
                onClick={() => setStatusFilter(status)}
                className={`px-4 py-2 rounded-xl text-xs font-bold transition-all ${
                  statusFilter === status 
                    ? 'bg-[var(--primary)] text-[var(--primary-foreground)]' 
                    : 'hover:bg-[var(--accent)] text-[var(--muted)]'
                }`}
              >
                {status}
              </button>
            ))}
          </div>
        </div>

        {/* Timeline View */}
        <div className="relative space-y-6">
          {filteredLogs.length > 0 ? filteredLogs.map((log, i) => (
            <motion.div
              key={log.id}
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: i * 0.05 }}
              className="group relative pl-16"
            >
              {/* Timeline Node */}
              <div className={`absolute left-0 top-1 w-14 h-14 rounded-2xl border-2 flex items-center justify-center transition-all duration-500 glass z-10 ${
                log.status === 'ALLOWED' ? 'border-emerald-500/50 bg-emerald-500/5 text-emerald-500 shadow-[0_0_15px_rgba(16,185,129,0.1)]' :
                log.status === 'WARNING' ? 'border-amber-500/50 bg-amber-500/5 text-amber-500 shadow-[0_0_15px_rgba(245,158,11,0.1)]' : 
                'border-rose-500/50 bg-rose-500/5 text-rose-500 shadow-[0_0_15px_rgba(239,68,68,0.1)]'
              }`}>
                {log.status === 'ALLOWED' && <CheckCircle2 className="w-6 h-6" />}
                {log.status === 'WARNING' && <AlertTriangle className="w-6 h-6" />}
                {log.status === 'BLOCKED' && <XCircle className="w-6 h-6" />}
              </div>

              {/* Log Content Card */}
              <motion.div 
                whileHover={{ y: -4 }}
                className="p-6 rounded-[2rem] border border-[var(--border)] bg-[var(--card)] glass card-shadow relative overflow-hidden"
              >
                <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                  <div className="space-y-1">
                    <div className="flex items-center gap-3">
                      <span className="text-xs font-bold text-[var(--muted)] uppercase tracking-widest">
                        {new Date(log.timestamp).toLocaleTimeString()}
                      </span>
                      <span className="w-1 h-1 rounded-full bg-[var(--border)]" />
                      <span className="text-xs font-mono text-[var(--muted)]">{log.id}</span>
                    </div>
                    <h3 className="text-lg font-bold tracking-tight">
                      "{log.input}"
                    </h3>
                  </div>
                  
                  <div className="flex items-center gap-6">
                    <div className="text-right">
                      <div className="text-[10px] font-bold text-[var(--muted)] uppercase tracking-widest mb-1">Confidence</div>
                      <div className="text-xl font-bold text-blue-500">{log.confidence.toFixed(1)}%</div>
                    </div>
                    <button className="p-3 rounded-xl hover:bg-[var(--accent)] text-[var(--muted)] hover:text-[var(--foreground)] transition-all">
                      <ExternalLink className="w-5 h-5" />
                    </button>
                  </div>
                </div>

                {/* Expandable Details (Visible on Hover) */}
                <motion.div 
                  initial={{ height: 0, opacity: 0 }}
                  whileHover={{ height: 'auto', opacity: 1 }}
                  className="overflow-hidden"
                >
                  <div className="pt-6 mt-6 border-t border-[var(--border)] space-y-4">
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                      <div className="space-y-2">
                        <div className="text-[10px] font-bold text-[var(--muted)] uppercase tracking-widest">Decision Reasoning</div>
                        <p className="text-sm text-[var(--foreground)] leading-relaxed opacity-80">
                          {log.decision}
                        </p>
                      </div>
                      <div className="space-y-2">
                        <div className="text-[10px] font-bold text-[var(--muted)] uppercase tracking-widest">Triggered Policies</div>
                        <div className="flex flex-wrap gap-2">
                          {log.risks && log.risks.length > 0 ? log.risks.map((risk, idx) => (
                            <span key={idx} className="px-2.5 py-1 rounded-lg bg-[var(--accent)] border border-[var(--border)] text-[10px] font-bold">
                              {risk}
                            </span>
                          )) : (
                            <span className="text-xs text-[var(--muted)] italic">No specific risk flags triggered.</span>
                          )}
                        </div>
                      </div>
                    </div>
                  </div>
                </motion.div>
              </motion.div>
            </motion.div>
          )) : (
            <div className="py-24 text-center">
              <div className="flex flex-col items-center gap-4 max-w-xs mx-auto">
                <div className="w-16 h-16 rounded-3xl bg-[var(--accent)] flex items-center justify-center mb-2">
                  <Database className="w-8 h-8 text-[var(--muted)] opacity-50" />
                </div>
                <h3 className="text-lg font-bold mb-1">No logs available</h3>
                <p className="text-sm text-[var(--muted)] leading-relaxed">
                  Your audit history is currently empty. Run evaluations on the home page to populate this timeline.
                </p>
              </div>
            </div>
          )}
        </div>
      </motion.div>
    </div>
  );
};

export default Logs;
