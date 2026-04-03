import React from 'react';
import { motion } from 'motion/react';
import { Shield, Lock, Activity, Zap, ArrowRight, Building2, Globe, Users, CheckCircle2 } from 'lucide-react';

const Enterprise = () => {
  const features = [
    {
      title: 'Custom Policy Engine',
      description: 'Design and deploy bespoke rules that match your institution\'s specific risk appetite and compliance requirements.',
      icon: Lock
    },
    {
      title: 'Global Infrastructure',
      description: 'Deploy Veridict across multiple regions with sub-millisecond latency for high-frequency autonomous trading.',
      icon: Globe
    },
    {
      title: 'Team Management',
      description: 'Role-based access control for policy management, log auditing, and system configuration.',
      icon: Users
    }
  ];

  return (
    <div className="flex-1 px-8 py-24 max-w-6xl mx-auto w-full">
      <motion.div 
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="text-center mb-24"
      >
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-purple-500/10 text-purple-500 text-xs font-bold mb-6 border border-purple-500/20">
          <Building2 className="w-3 h-3" />
          Enterprise-Grade Security
        </div>
        <h1 className="text-5xl md:text-7xl font-bold tracking-tighter mb-8">
          Built for financial<br />
          institutions.
        </h1>
        <p className="text-xl text-[var(--muted)] max-w-3xl mx-auto leading-relaxed">
          Veridict provides the security, compliance, and reliability required by the world's most demanding financial organizations.
        </p>
      </motion.div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-12 mb-32">
        {features.map((feature, i) => (
          <motion.div
            key={feature.title}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: i * 0.2 }}
            className="p-8 rounded-3xl border border-[var(--border)] glass card-shadow group hover:border-purple-500/20 transition-all"
          >
            <div className="w-12 h-12 rounded-xl flex items-center justify-center mb-6 bg-purple-500/10 text-purple-500">
              <feature.icon className="w-6 h-6" />
            </div>
            <h3 className="text-2xl font-bold mb-4">{feature.title}</h3>
            <p className="text-[var(--muted)] leading-relaxed">{feature.description}</p>
          </motion.div>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 items-center mb-32">
        <div className="space-y-8">
          <h2 className="text-4xl font-bold tracking-tight">Custom integrations for complex workflows.</h2>
          <p className="text-lg text-[var(--muted)] leading-relaxed">
            Our enterprise team works directly with your engineers to integrate Veridict into your existing trading infrastructure, ensuring seamless intent verification.
          </p>
          <div className="space-y-4">
            {[
              'Dedicated account management',
              'SLA-backed uptime guarantees',
              'On-premise deployment options',
              'Custom compliance reporting'
            ].map((item) => (
              <div key={item} className="flex items-center gap-3">
                <CheckCircle2 className="w-5 h-5 text-purple-500" />
                <span className="font-medium">{item}</span>
              </div>
            ))}
          </div>
          <button className="px-8 py-4 bg-[var(--primary)] text-[var(--primary-foreground)] rounded-2xl font-bold flex items-center gap-2 hover:gap-3 transition-all">
            Contact Enterprise Sales <ArrowRight className="w-5 h-5" />
          </button>
        </div>
        <div className="p-12 rounded-[3rem] border border-[var(--border)] glass card-shadow relative overflow-hidden">
          <div className="relative z-10 space-y-6">
            <div className="flex items-center gap-4 p-6 rounded-2xl bg-white/5 border border-white/10">
              <div className="w-10 h-10 rounded-full bg-gradient-to-br from-blue-500 to-purple-500" />
              <div>
                <div className="font-bold">Global Bank Corp</div>
                <div className="text-xs opacity-60">Enterprise Client</div>
              </div>
            </div>
            <p className="text-xl font-medium italic leading-relaxed">
              "Veridict has transformed how we manage our autonomous trading agents. The intent-level verification provides a safety net that was previously missing from our stack."
            </p>
            <div className="flex items-center gap-2">
              {[1, 2, 3, 4, 5].map((s) => (
                <Zap key={s} className="w-4 h-4 text-yellow-500 fill-yellow-500" />
              ))}
            </div>
          </div>
          <div className="absolute top-0 right-0 w-full h-full bg-gradient-to-br from-purple-500/10 to-blue-500/10 pointer-events-none" />
        </div>
      </div>
    </div>
  );
};

export default Enterprise;
