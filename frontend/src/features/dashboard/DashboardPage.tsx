import React, { useState, useEffect } from 'react';
import { useOutletContext, Link } from 'react-router-dom';
import {
  TrendingUp,
  TrendingDown,
  DollarSign,
  AlertTriangle,
  Clock,
  ArrowRight,
  PlusCircle,
  UploadCloud,
  CheckCircle2,
  HelpCircle
} from 'lucide-react';
import { api } from '../../api/client';
import { DashboardSummary } from '../../api/types';

export const DashboardPage: React.FC = () => {
  const { selectedPortfolioId } = useOutletContext<{ selectedPortfolioId?: number }>();
  const [data, setData] = useState<DashboardSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setLoading(true);
    setError(null);
    api.getDashboard(selectedPortfolioId)
      .then((res) => {
        setData(res);
        setLoading(false);
      })
      .catch((err) => {
        setError(err.message || 'Failed to load dashboard data');
        setLoading(false);
      });
  }, [selectedPortfolioId]);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64 text-slate-400">
        <Clock className="w-5 h-5 animate-spin mr-2" />
        <span>Loading authoritative ledger balances...</span>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-4 bg-rose-500/10 border border-rose-500/30 rounded-lg text-rose-400 text-sm flex items-center gap-3">
        <AlertTriangle className="w-5 h-5 flex-shrink-0" />
        <div>
          <p className="font-semibold">Unable to load dashboard</p>
          <p className="text-xs text-rose-300">{error}</p>
        </div>
      </div>
    );
  }

  if (!data || !data.portfolio_id) {
    return (
      <div className="border border-slate-800 bg-slate-950/50 rounded-xl p-10 text-center max-w-lg mx-auto mt-12">
        <div className="w-12 h-12 bg-emerald-500/10 text-emerald-400 rounded-full flex items-center justify-center mx-auto mb-4">
          <TrendingUp className="w-6 h-6" />
        </div>
        <h2 className="text-lg font-semibold text-white mb-2">No Portfolio Found</h2>
        <p className="text-xs text-slate-400 mb-6 leading-relaxed">
          Start your local-first portfolio record. Create a portfolio or import transactions directly from CSV.
        </p>
        <div className="flex justify-center gap-3">
          <Link
            to="/portfolios"
            className="px-4 py-2 bg-emerald-500 hover:bg-emerald-600 text-slate-950 font-semibold text-xs rounded-md flex items-center gap-2"
          >
            <PlusCircle className="w-4 h-4" /> Create Portfolio
          </Link>
          <Link
            to="/imports"
            className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-200 font-semibold text-xs rounded-md flex items-center gap-2 border border-slate-700"
          >
            <UploadCloud className="w-4 h-4" /> Import CSV
          </Link>
        </div>
      </div>
    );
  }

  const isPositivePnl = Number(data.unrealized_pnl) >= 0;

  return (
    <div className="space-y-6">
      {/* Top Banner / Freshness */}
      <div className="flex flex-wrap items-center justify-between gap-4 bg-slate-950/60 border border-slate-800/80 p-3.5 rounded-lg">
        <div className="flex items-center gap-3">
          <span className="text-xs font-semibold text-slate-300">Data Status:</span>
          <span
            className={`px-2.5 py-0.5 rounded text-[11px] font-medium flex items-center gap-1.5 ${
              data.data_freshness.includes('stale') || data.data_freshness.includes('incomplete')
                ? 'bg-amber-500/10 text-amber-400 border border-amber-500/30'
                : 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/30'
            }`}
          >
            <CheckCircle2 className="w-3.5 h-3.5" />
            {data.data_freshness}
          </span>
        </div>

        <div className="flex items-center gap-3 text-xs">
          <Link
            to="/transactions/new"
            className="px-3 py-1.5 bg-emerald-500 hover:bg-emerald-600 text-slate-950 font-semibold rounded-md flex items-center gap-1.5 transition-colors"
          >
            <PlusCircle className="w-3.5 h-3.5" /> Add Transaction
          </Link>
          <Link
            to="/imports"
            className="px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-200 rounded-md border border-slate-700 flex items-center gap-1.5 transition-colors"
          >
            <UploadCloud className="w-3.5 h-3.5" /> Import
          </Link>
        </div>
      </div>

      {/* Metric Cards Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
        {/* Total Value */}
        <div className="p-4 bg-slate-950/80 border border-slate-800 rounded-xl">
          <p className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider mb-1">Total Market Value</p>
          <div className="text-xl font-bold text-white tracking-tight">
            {data.base_currency} {Number(data.total_portfolio_value).toLocaleString('en-IN', { minimumFractionDigits: 2 })}
          </div>
          <p className="text-[11px] text-slate-500 mt-2 flex items-center gap-1">
            <span>Holdings:</span> {data.base_currency} {Number(data.holdings_market_value).toLocaleString('en-IN', { minimumFractionDigits: 2 })}
          </p>
        </div>

        {/* Invested Cost Basis */}
        <div className="p-4 bg-slate-950/80 border border-slate-800 rounded-xl">
          <p className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider mb-1">Invested Cost Basis</p>
          <div className="text-xl font-bold text-slate-200 tracking-tight">
            {data.base_currency} {Number(data.invested_cost_basis).toLocaleString('en-IN', { minimumFractionDigits: 2 })}
          </div>
          <p className="text-[11px] text-slate-500 mt-2">Average cost accounting</p>
        </div>

        {/* Unrealized Gain/Loss */}
        <div className="p-4 bg-slate-950/80 border border-slate-800 rounded-xl">
          <p className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider mb-1">Unrealized P&L</p>
          <div className={`text-xl font-bold tracking-tight flex items-center gap-1.5 ${isPositivePnl ? 'text-emerald-400' : 'text-rose-400'}`}>
            {isPositivePnl ? <TrendingUp className="w-4 h-4" /> : <TrendingDown className="w-4 h-4" />}
            {data.base_currency} {Number(data.unrealized_pnl).toLocaleString('en-IN', { minimumFractionDigits: 2 })}
          </div>
          <p className={`text-[11px] mt-2 font-medium ${isPositivePnl ? 'text-emerald-400' : 'text-rose-400'}`}>
            {isPositivePnl ? '+' : ''}{data.unrealized_pnl_pct}%
          </p>
        </div>

        {/* Realized Gain/Loss */}
        <div className="p-4 bg-slate-950/80 border border-slate-800 rounded-xl">
          <p className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider mb-1">Realized P&L</p>
          <div className="text-xl font-bold text-slate-200 tracking-tight">
            {data.base_currency} {Number(data.realized_pnl).toLocaleString('en-IN', { minimumFractionDigits: 2 })}
          </div>
          <p className="text-[11px] text-slate-500 mt-2">Disposals & sales</p>
        </div>

        {/* Cash Balance */}
        <div className="p-4 bg-slate-950/80 border border-slate-800 rounded-xl">
          <p className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider mb-1">Cash Balance</p>
          <div className="text-xl font-bold text-emerald-400 tracking-tight">
            {data.base_currency} {Number(data.cash_balance).toLocaleString('en-IN', { minimumFractionDigits: 2 })}
          </div>
          <p className="text-[11px] text-slate-500 mt-2">Authoritative cash ledger</p>
        </div>
      </div>

      {/* Main Grid: Value Over Time & Asset Allocation */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Value Over Time Chart Card */}
        <div className="lg:col-span-2 bg-slate-950/80 border border-slate-800 rounded-xl p-5">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h3 className="font-semibold text-sm text-white">Portfolio Valuation Trajectory</h3>
              <p className="text-xs text-slate-400">Historical valuation vs invested cost basis</p>
            </div>
            <div className="flex gap-1 bg-slate-900 border border-slate-800 p-0.5 rounded-md text-[11px]">
              {['1M', '3M', '6M', 'YTD', '1Y', 'ALL'].map((r, i) => (
                <button
                  key={r}
                  className={`px-2 py-0.5 rounded font-medium ${i === 5 ? 'bg-slate-800 text-white' : 'text-slate-400 hover:text-slate-200'}`}
                >
                  {r}
                </button>
              ))}
            </div>
          </div>

          {/* Simple Canvas / Chart Representation */}
          <div className="h-48 border border-slate-800/80 rounded-lg p-3 flex flex-col justify-between bg-slate-900/30">
            <div className="flex justify-between text-[11px] text-slate-500">
              <span>{data.value_history[0]?.date || 'Start'}</span>
              <span>Latest: {data.base_currency} {Number(data.total_portfolio_value).toLocaleString('en-IN', { minimumFractionDigits: 2 })}</span>
            </div>

            {/* Sparkline / Step Visualization */}
            <div className="flex items-end gap-2 h-32 px-2 pt-4">
              {data.value_history.map((pt, idx) => {
                const maxVal = Math.max(...data.value_history.map((p) => Number(p.portfolio_value)), 1);
                const heightPct = Math.min(100, Math.max(10, (Number(pt.portfolio_value) / maxVal) * 100));
                return (
                  <div key={idx} className="flex-1 flex flex-col items-center gap-1 group relative">
                    <div
                      style={{ height: `${heightPct}%` }}
                      className="w-full bg-emerald-500/80 hover:bg-emerald-400 rounded-t transition-all cursor-pointer"
                    />
                    <div className="opacity-0 group-hover:opacity-100 absolute bottom-full mb-1 bg-slate-800 text-white text-[10px] py-1 px-2 rounded shadow-lg whitespace-nowrap pointer-events-none z-10">
                      {pt.date}: {data.base_currency} {pt.portfolio_value}
                    </div>
                  </div>
                );
              })}
            </div>

            <div className="text-[11px] text-slate-500 flex justify-between">
              <span>Points: {data.value_history.length}</span>
              <span className="text-emerald-400">Valuation Ledger</span>
            </div>
          </div>
        </div>

        {/* Asset Class Allocation Card */}
        <div className="bg-slate-950/80 border border-slate-800 rounded-xl p-5 flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-4">
              <h3 className="font-semibold text-sm text-white">Asset Allocation</h3>
              <Link to="/allocation" className="text-xs text-emerald-400 hover:underline flex items-center gap-1">
                Details <ArrowRight className="w-3 h-3" />
              </Link>
            </div>

            <div className="space-y-3">
              {data.allocation_by_asset.length === 0 ? (
                <p className="text-xs text-slate-500">No active assets</p>
              ) : (
                data.allocation_by_asset.map((item) => (
                  <div key={item.name} className="space-y-1">
                    <div className="flex justify-between text-xs">
                      <span className="text-slate-300 font-medium">{item.name}</span>
                      <span className="text-slate-400">{item.weight}%</span>
                    </div>
                    <div className="h-2 w-full bg-slate-800 rounded-full overflow-hidden">
                      <div
                        className="h-full bg-emerald-500 rounded-full"
                        style={{ width: `${item.weight}%` }}
                      />
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>

          <div className="pt-4 border-t border-slate-800 text-[11px] text-slate-400">
            Unclassified assets are not guessed. Configure in Settings.
          </div>
        </div>
      </div>

      {/* Holdings Table */}
      <div className="bg-slate-950/80 border border-slate-800 rounded-xl overflow-hidden">
        <div className="p-4 border-b border-slate-800 flex items-center justify-between">
          <div>
            <h3 className="font-semibold text-sm text-white">Current Holdings ({data.holdings.length})</h3>
            <p className="text-xs text-slate-400">Derived strictly from transaction history</p>
          </div>
          <Link to="/holdings" className="text-xs text-emerald-400 hover:underline flex items-center gap-1 font-medium">
            View All Holdings <ArrowRight className="w-3.5 h-3.5" />
          </Link>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-900/60 text-slate-400 uppercase text-[10px] tracking-wider border-b border-slate-800">
              <tr>
                <th className="py-2.5 px-4 font-semibold">Symbol</th>
                <th className="py-2.5 px-4 font-semibold">Quantity</th>
                <th className="py-2.5 px-4 font-semibold">Avg Cost</th>
                <th className="py-2.5 px-4 font-semibold">Latest Price</th>
                <th className="py-2.5 px-4 font-semibold">Market Value</th>
                <th className="py-2.5 px-4 font-semibold">Unrealized P&L</th>
                <th className="py-2.5 px-4 font-semibold">Weight</th>
                <th className="py-2.5 px-4 font-semibold">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60">
              {data.holdings.length === 0 ? (
                <tr>
                  <td colSpan={8} className="py-8 text-center text-slate-500">
                    No active positions held. Add a BUY transaction or import CSV to track assets.
                  </td>
                </tr>
              ) : (
                data.holdings.slice(0, 8).map((h) => {
                  const pnlNum = Number(h.unrealized_pnl || 0);
                  const isPositive = pnlNum >= 0;
                  return (
                    <tr key={h.instrument_id} className="hover:bg-slate-900/40 transition-colors">
                      <td className="py-3 px-4 font-medium text-white">
                        <Link to={`/holdings`} className="hover:text-emerald-400">
                          {h.symbol}
                        </Link>
                        <span className="block text-[10px] text-slate-400 font-normal">{h.display_name}</span>
                      </td>
                      <td className="py-3 px-4 text-slate-200">{h.quantity}</td>
                      <td className="py-3 px-4 text-slate-300">
                        {data.base_currency} {h.average_cost}
                      </td>
                      <td className="py-3 px-4 text-slate-300">
                        {h.latest_price ? `${data.base_currency} ${h.latest_price}` : <span className="text-amber-400 italic">Missing</span>}
                      </td>
                      <td className="py-3 px-4 font-medium text-white">
                        {h.market_value ? `${data.base_currency} ${h.market_value}` : '-'}
                      </td>
                      <td className="py-3 px-4">
                        {h.unrealized_pnl ? (
                          <span className={`font-semibold ${isPositive ? 'text-emerald-400' : 'text-rose-400'}`}>
                            {isPositive ? '+' : ''}{h.unrealized_pnl} ({h.unrealized_pnl_pct}%)
                          </span>
                        ) : (
                          '-'
                        )}
                      </td>
                      <td className="py-3 px-4 text-slate-300">{h.weight}%</td>
                      <td className="py-3 px-4">
                        <span
                          className={`px-2 py-0.5 rounded text-[10px] font-medium ${
                            h.quality_status === 'valid'
                              ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'
                              : 'bg-amber-500/10 text-amber-400 border border-amber-500/20'
                          }`}
                        >
                          {h.quality_status}
                        </span>
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Recent Activity List */}
      <div className="bg-slate-950/80 border border-slate-800 rounded-xl p-5">
        <div className="flex items-center justify-between mb-4">
          <h3 className="font-semibold text-sm text-white">Recent Ledger Transactions</h3>
          <Link to="/transactions" className="text-xs text-emerald-400 hover:underline flex items-center gap-1">
            View Ledger <ArrowRight className="w-3.5 h-3.5" />
          </Link>
        </div>

        <div className="space-y-2">
          {data.recent_activity.length === 0 ? (
            <p className="text-xs text-slate-500">No transactions recorded.</p>
          ) : (
            data.recent_activity.map((t) => (
              <div
                key={t.id}
                className="flex items-center justify-between p-2.5 rounded-lg bg-slate-900/50 border border-slate-800/60 text-xs"
              >
                <div className="flex items-center gap-3">
                  <span
                    className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                      t.type === 'BUY'
                        ? 'bg-blue-500/20 text-blue-400 border border-blue-500/30'
                        : t.type === 'SELL'
                        ? 'bg-purple-500/20 text-purple-400 border border-purple-500/30'
                        : t.type === 'CASH_DEPOSIT'
                        ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30'
                        : 'bg-slate-800 text-slate-300'
                    }`}
                  >
                    {t.type}
                  </span>
                  <span className="font-medium text-slate-200">{t.symbol}</span>
                  <span className="text-[11px] text-slate-500">{t.trade_date}</span>
                  {t.is_reversed && (
                    <span className="text-[10px] text-rose-400 bg-rose-500/10 px-1.5 py-0.5 rounded">Reversed</span>
                  )}
                </div>

                <div className="text-right font-medium text-slate-300">
                  {t.currency} {t.net_amount}
                </div>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
};

