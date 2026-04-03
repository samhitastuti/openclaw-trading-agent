import React, { useState } from 'react';
import { motion, AnimatePresence } from 'motion/react';
import { Wallet, CheckCircle2, ArrowRight, ShieldCheck, Zap, Activity } from 'lucide-react';

const ConnectWallet = () => {
  const [connecting, setConnecting] = useState(false);
  const [connected, setConnected] = useState(false);
  const [selectedWallet, setSelectedWallet] = useState<string | null>(null);

  const wallets = [
    { name: 'MetaMask', icon: '🦊', description: 'Connect to your MetaMask Wallet' },
    { name: 'WalletConnect', icon: '🌐', description: 'Scan with WalletConnect to connect' },
    { name: 'Coinbase Wallet', icon: '💙', description: 'Connect to your Coinbase Wallet' },
    { name: 'Phantom', icon: '👻', description: 'Connect to your Phantom Wallet' },
  ];

  const handleConnect = () => {
    if (!selectedWallet) return;
    setConnecting(true);
    setTimeout(() => {
      setConnecting(false);
      setConnected(true);
    }, 1500);
  };

  return (
    <div className="flex-1 flex items-center justify-center px-8 py-12">
      <motion.div 
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        className="w-full max-w-2xl p-8 rounded-3xl border border-[var(--border)] glass card-shadow"
      >
        <AnimatePresence mode="wait">
          {!connected ? (
            <motion.div 
              key="connect"
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: 20 }}
              className="space-y-8"
            >
              <div className="text-center">
                <div className="w-16 h-16 bg-blue-500/10 rounded-2xl flex items-center justify-center mx-auto mb-4">
                  <Wallet className="w-8 h-8 text-blue-500" />
                </div>
                <h2 className="text-3xl font-bold tracking-tight">Connect your wallet</h2>
                <p className="text-[var(--muted)] mt-2">Select a wallet provider to start trading with Veridict</p>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {wallets.map((wallet) => (
                  <button
                    key={wallet.name}
                    onClick={() => setSelectedWallet(wallet.name)}
                    className={`p-6 rounded-2xl border-2 text-left transition-all ${
                      selectedWallet === wallet.name 
                        ? 'border-blue-500 bg-blue-500/5' 
                        : 'border-[var(--border)] hover:border-[var(--muted)]'
                    }`}
                  >
                    <div className="text-3xl mb-3">{wallet.icon}</div>
                    <div className="font-bold text-lg">{wallet.name}</div>
                    <div className="text-xs text-[var(--muted)] mt-1">{wallet.description}</div>
                  </button>
                ))}
              </div>

              <button
                onClick={handleConnect}
                disabled={!selectedWallet || connecting}
                className="w-full py-4 bg-[var(--primary)] text-[var(--primary-foreground)] rounded-xl font-bold flex items-center justify-center gap-2 hover:opacity-90 transition-all disabled:opacity-50 relative overflow-hidden"
              >
                <AnimatePresence mode="wait">
                  {connecting ? (
                    <motion.div
                      key="connecting"
                      initial={{ y: 20, opacity: 0 }}
                      animate={{ y: 0, opacity: 1 }}
                      exit={{ y: -20, opacity: 0 }}
                      className="flex items-center gap-2"
                    >
                      <Activity className="w-5 h-5 animate-spin text-blue-400" />
                      <span>Establishing Secure Link...</span>
                    </motion.div>
                  ) : (
                    <motion.div
                      key="idle"
                      initial={{ y: 20, opacity: 0 }}
                      animate={{ y: 0, opacity: 1 }}
                      exit={{ y: -20, opacity: 0 }}
                      className="flex items-center gap-2"
                    >
                      <span>Connect {selectedWallet || 'Wallet'}</span>
                      <ArrowRight className="w-5 h-5" />
                    </motion.div>
                  )}
                </AnimatePresence>
              </button>
            </motion.div>
          ) : (
            <motion.div 
              key="success"
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              className="text-center py-12 space-y-6"
            >
              <div className="w-20 h-20 bg-emerald-500/10 rounded-full flex items-center justify-center mx-auto relative">
                <CheckCircle2 className="w-10 h-10 text-emerald-500" />
                <motion.div 
                  initial={{ scale: 0 }}
                  animate={{ scale: 1 }}
                  className="absolute -top-1 -right-1 bg-emerald-500 text-white text-[10px] font-bold px-2 py-0.5 rounded-full"
                >
                  LIVE
                </motion.div>
              </div>
              <div className="space-y-2">
                <h2 className="text-3xl font-bold tracking-tight">Connected ✅</h2>
                <p className="text-[var(--muted)]">Successfully established a secure link to your {selectedWallet} wallet.</p>
              </div>
              <div className="p-4 rounded-xl bg-[var(--accent)] border border-[var(--border)] inline-flex items-center gap-3">
                <ShieldCheck className="w-5 h-5 text-blue-500" />
                <span className="font-mono text-sm">0x71C...392A</span>
              </div>
              <div className="pt-6">
                <button 
                  onClick={() => setConnected(false)}
                  className="px-8 py-3 border border-[var(--border)] rounded-xl font-bold hover:bg-[var(--accent)] transition-all"
                >
                  Disconnect
                </button>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </motion.div>
    </div>
  );
};

export default ConnectWallet;
