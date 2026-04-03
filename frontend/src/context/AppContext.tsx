import React, { createContext, useContext, useState, useEffect } from 'react';
import { LogEntry } from '../types';

interface AppContextType {
  theme: string;
  toggleTheme: () => void;
  auditLogs: LogEntry[];
  addLog: (log: LogEntry) => void;
  clearLogs: () => void;
  user: { email: string } | null;
  setUser: (user: { email: string } | null) => void;
  exportLogs: (format: 'csv' | 'json') => void;
}

const AppContext = createContext<AppContextType | undefined>(undefined);

export const AppProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [theme, setTheme] = useState(() => localStorage.getItem('theme') || 'light');
  const [auditLogs, setAuditLogs] = useState<LogEntry[]>(() => {
    const saved = localStorage.getItem('audit_logs');
    return saved ? JSON.parse(saved) : [];
  });
  const [user, setUser] = useState<{ email: string } | null>(null);

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem('theme', theme);
  }, [theme]);

  useEffect(() => {
    localStorage.setItem('audit_logs', JSON.stringify(auditLogs));
  }, [auditLogs]);

  const toggleTheme = () => setTheme(prev => prev === 'light' ? 'dark' : 'light');

  const addLog = (log: LogEntry) => {
    setAuditLogs(prev => [log, ...prev]);
  };

  const clearLogs = () => {
    if (window.confirm('Are you sure you want to clear all audit logs?')) {
      setAuditLogs([]);
    }
  };

  const exportLogs = (format: 'csv' | 'json') => {
    if (auditLogs.length === 0) return;

    if (format === 'csv') {
      const headers = ["ID", "Timestamp", "Input", "Status", "Decision", "Confidence", "Risks"];
      const rows = auditLogs.map(log => [
        log.id,
        new Date(log.timestamp).toISOString(),
        `"${log.input.replace(/"/g, '""')}"`,
        log.status,
        `"${log.decision.replace(/"/g, '""')}"`,
        log.confidence,
        `"${(log.risks || []).join(", ").replace(/"/g, '""')}"`
      ]);

      const csvContent = "data:text/csv;charset=utf-8," 
        + [headers, ...rows].map(e => e.join(",")).join("\n");

      const link = document.createElement("a");
      link.setAttribute("href", encodeURI(csvContent));
      link.setAttribute("download", `veridict_audit_logs_${new Date().getTime()}.csv`);
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
    } else {
      const blob = new Blob([JSON.stringify(auditLogs, null, 2)], {
        type: "application/json",
      });
      const url = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = `veridict_audit_logs_${new Date().getTime()}.json`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      URL.revokeObjectURL(url);
    }
  };

  return (
    <AppContext.Provider value={{ 
      theme, 
      toggleTheme, 
      auditLogs, 
      addLog, 
      clearLogs,
      user, 
      setUser,
      exportLogs
    }}>
      {children}
    </AppContext.Provider>
  );
};

export const useAppContext = () => {
  const context = useContext(AppContext);
  if (context === undefined) {
    throw new Error('useAppContext must be used within an AppProvider');
  }
  return context;
};
