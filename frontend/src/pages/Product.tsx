import React from 'react';
import { motion } from 'motion/react';
import { Shield, Search, Lock, Activity, Zap, ArrowRight, CheckCircle2 } from 'lucide-react';

const Product = () => {
  const steps = [
    {
      title: 'Intent Parsing',
      icon: Search,
      description: 'Veridict uses advanced NLP to parse raw user input into structured financial intents, identifying actions, assets, and amounts.',
      color: 'blue'
    },
    {
      title: 'Armoriq Policy Engine',
      icon: Lock,
      description: 'The core intelligence layer that evaluates every intent against a complex set of risk, compliance, and security policies.',
      color: 'purple'
    },
    {
      title: 'Decision Layer',
      icon: Activity,
      description: 'The final verification step that either allows, warns, or blocks the execution based on the policy evaluation results.',
      color: 'emerald'
    }
  ];

  return (
    <div className="flex-1 px-8 py-24 max-w-6xl mx-auto w-full">
      <motion.div 
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="text-center mb-24"
      >
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-blue-500/10 text-blue-500 text-xs font-bold mb-6 border border-blue-500/20">
          <Shield className="w-3 h-3" />
          The Future of Autonomous Trading
        </div>
        <h1 className="text-5xl md:text-7xl font-bold tracking-tighter mb-8">
          The decision verification layer<br />
          for the autonomous era.
        </h1>
        <p className="text-xl text-[var(--muted)] max-w-3xl mx-auto leading-relaxed">
          Veridict acts as a sentinel between your AI agents and the financial markets, ensuring every action is intentional, safe, and compliant.
        </p>
      </motion.div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-12 mb-32">
        {steps.map((step, i) => (
          <motion.div
            key={step.title}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: i * 0.2 }}
            className="p-8 rounded-3xl border border-[var(--border)] glass card-shadow relative overflow-hidden group"
          >
            <div className={`w-12 h-12 rounded-xl flex items-center justify-center mb-6 bg-${step.color}-500/10`}>
              <step.icon className={`w-6 h-6 text-${step.color}-500`} />
            </div>
            <h3 className="text-2xl font-bold mb-4">{step.title}</h3>
            <p className="text-[var(--muted)] leading-relaxed">{step.description}</p>
            <div className={`absolute -bottom-4 -right-4 w-24 h-24 bg-${step.color}-500/5 rounded-full blur-2xl group-hover:scale-150 transition-transform duration-700`} />
          </motion.div>
        ))}
      </div>

      <div className="p-12 rounded-[3rem] bg-[var(--primary)] text-[var(--primary-foreground)] relative overflow-hidden">
        <div className="relative z-10 flex flex-col md:flex-row items-center justify-between gap-12">
          <div className="max-w-xl">
            <h2 className="text-4xl font-bold mb-6 tracking-tight">Ready to secure your trading agents?</h2>
            <p className="text-lg opacity-80 mb-8">
              Join the leading financial institutions using Veridict to enforce intent and prevent unauthorized executions.
            </p>
            <div className="flex flex-wrap gap-4">
              <button className="px-8 py-4 bg-[var(--background)] text-[var(--foreground)] rounded-2xl font-bold flex items-center gap-2 hover:gap-3 transition-all">
                Get Started <ArrowRight className="w-5 h-5" />
              </button>
              <button className="px-8 py-4 border border-white/20 rounded-2xl font-bold hover:bg-white/10 transition-all">
                Talk to Sales
              </button>
            </div>
          </div>
          <div className="w-full max-w-sm space-y-4">
            {[
              'Real-time intent verification',
              'Custom policy rule engine',
              'Audit-ready execution logs',
              'Multi-wallet support'
            ].map((feature) => (
              <div key={feature} className="flex items-center gap-3 p-4 rounded-2xl bg-white/5 border border-white/10">
                <CheckCircle2 className="w-5 h-5 text-emerald-400" />
                <span className="font-medium">{feature}</span>
              </div>
            ))}
          </div>
        </div>
        <div className="absolute top-0 right-0 w-full h-full bg-gradient-to-br from-blue-500/20 to-purple-500/20 pointer-events-none" />
      </div>
    </div>
  );
};

export default Product;
