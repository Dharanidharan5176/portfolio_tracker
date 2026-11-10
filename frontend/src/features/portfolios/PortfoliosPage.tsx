import React, { useState, useEffect } from 'react';
import { PlusCircle, Briefcase, CheckCircle, Shield, AlertCircle } from 'lucide-react';
import { api } from '../../api/client';
import { Portfolio, Account } from '../../api/types';

export const PortfoliosPage: React.FC = () => {
  const [portfolios, setPortfolios] = useState<Portfolio[]>([]);
  const [accounts, setAccounts] = useState<Account[]>([]);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [newName, setNewName] = useState('');
  const [newCurrency, setNewCurrency] = useState('INR');
  const [newBenchmark, setNewBenchmark] = useState('^NSEI');
  const [error, setError] = useState<string | null>(null);

  const loadData = () => {
    api.getPortfolios().then(setPortfolios).catch(console.error);
    api.getAccounts().then(setAccounts).catch(console.error);
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    try {
      await api.createPortfolio({
        name: newName,
        base_currency: newCurrency,
        benchmark_symbol: newBenchmark,
      });
      setShowCreateModal(false);
      setNewName('');
      loadData();
    } catch (err: any) {
      setError(err.message || 'Failed to create portfolio');
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-base font-semibold text-white">Portfolios & Accounts</h2>
          <p className="text-xs text-slate-400">Manage segregated investment strategies and accounts</p>
        </div>
        <button
          onClick={() => setShowCreateModal(true)}
          className="px-3.5 py-1.5 bg-emerald-500 hover:bg-emerald-600 text-slate-950 font-semibold text-xs rounded-md flex items-center gap-1.5 transition-colors"
        >
          <PlusCircle className="w-4 h-4" /> New Portfolio
        </button>
      </div>

      {/* Portfolios Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {portfolios.map((p) => {
          const pAccounts = accounts.filter((a) => a.portfolio_id === p.id);
          return (
            <div key={p.id} className="bg-slate-950/80 border border-slate-800 rounded-xl p-5 space-y-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2.5">
                  <div className="p-2 bg-emerald-500/10 text-emerald-400 rounded-lg">
                    <Briefcase className="w-4 h-4" />
                  </div>
                  <div>
                    <h3 className="font-semibold text-sm text-white">{p.name}</h3>
                    <p className="text-[11px] text-slate-400">Base Currency: {p.base_currency}</p>
                  </div>
                </div>
                <span className="px-2 py-0.5 rounded text-[10px] font-medium bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                  {p.status}
                </span>
              </div>

              <div className="border-t border-slate-800/80 pt-3">
                <p className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider mb-2">
                  Linked Accounts ({pAccounts.length})
                </p>
                <div className="space-y-1.5">
                  {pAccounts.map((acc) => (
                    <div
                      key={acc.id}
                      className="flex items-center justify-between text-xs p-2 rounded bg-slate-900/60 border border-slate-800/60"
                    >
                      <span className="text-slate-300">{acc.name}</span>
                      <span className="text-[11px] text-slate-500">{acc.institution_label}</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {/* Create Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-slate-950/80 backdrop-blur-sm flex items-center justify-center p-4 z-50">
          <div className="bg-slate-900 border border-slate-800 rounded-xl max-w-md w-full p-6 space-y-4">
            <h3 className="text-sm font-semibold text-white">Create New Portfolio</h3>
            {error && (
              <div className="p-3 bg-rose-500/10 border border-rose-500/30 rounded text-rose-400 text-xs">
                {error}
              </div>
            )}
            <form onSubmit={handleCreate} className="space-y-4">
              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">Portfolio Name</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Long-Term Growth"
                  value={newName}
                  onChange={(e) => setNewName(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded px-3 py-2 text-xs text-white focus:outline-none focus:border-emerald-500"
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">Base Currency</label>
                <input
                  type="text"
                  required
                  maxLength={3}
                  value={newCurrency}
                  onChange={(e) => setNewCurrency(e.target.value.toUpperCase())}
                  className="w-full bg-slate-950 border border-slate-800 rounded px-3 py-2 text-xs text-white focus:outline-none focus:border-emerald-500"
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">Benchmark Symbol</label>
                <input
                  type="text"
                  placeholder="e.g. ^NSEI or SPY"
                  value={newBenchmark}
                  onChange={(e) => setNewBenchmark(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded px-3 py-2 text-xs text-white focus:outline-none focus:border-emerald-500"
                />
              </div>

              <div className="flex justify-end gap-2 pt-2">
                <button
                  type="button"
                  onClick={() => setShowCreateModal(false)}
                  className="px-3 py-1.5 bg-slate-800 text-slate-300 hover:bg-slate-700 text-xs rounded"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-3.5 py-1.5 bg-emerald-500 hover:bg-emerald-600 text-slate-950 font-semibold text-xs rounded"
                >
                  Create
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

