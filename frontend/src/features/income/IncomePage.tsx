import React, { useState, useEffect } from 'react';
import { useOutletContext } from 'react-router-dom';
import { DollarSign, Calendar, TrendingUp, AlertCircle } from 'lucide-react';
import { api } from '../../api/client';

export const IncomePage: React.FC = () => {
  const { selectedPortfolioId } = useOutletContext<{ selectedPortfolioId?: number }>();
  const [data, setData] = useState<any | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    api.getIncome(selectedPortfolioId)
      .then((res) => {
        setData(res);
        setLoading(false);
      })
      .catch((err) => {
        console.error(err);
        setLoading(false);
      });
  }, [selectedPortfolioId]);

  if (loading) {
    return <div className="text-xs text-slate-400 p-8 text-center">Summarizing recorded income and cash movements...</div>;
  }

  if (!data) {
    return <div className="text-xs text-slate-400 p-8 text-center">No income records available.</div>;
  }

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-base font-semibold text-white">Cash Flows & Income</h2>
        <p className="text-xs text-slate-400">Dividends, interest, withholding taxes and fees</p>
      </div>

      {/* Metric Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
        <div className="p-4 bg-slate-950/80 border border-slate-800 rounded-xl">
          <p className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider mb-1">Net Income Received</p>
          <div className="text-xl font-bold text-emerald-400 font-mono">
            {data.total_net_income}
          </div>
          <p className="text-[11px] text-slate-500 mt-2">After taxes & fees</p>
        </div>

        <div className="p-4 bg-slate-950/80 border border-slate-800 rounded-xl">
          <p className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider mb-1">Gross Dividends</p>
          <div className="text-xl font-bold text-white font-mono">
            {data.total_dividends}
          </div>
          <p className="text-[11px] text-slate-500 mt-2">Stock dividends</p>
        </div>

        <div className="p-4 bg-slate-950/80 border border-slate-800 rounded-xl">
          <p className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider mb-1">Gross Interest</p>
          <div className="text-xl font-bold text-white font-mono">
            {data.total_interest}
          </div>
          <p className="text-[11px] text-slate-500 mt-2">Cash & debt interest</p>
        </div>

        <div className="p-4 bg-slate-950/80 border border-slate-800 rounded-xl">
          <p className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider mb-1">Total Fees Paid</p>
          <div className="text-xl font-bold text-slate-300 font-mono">
            {data.total_fees}
          </div>
          <p className="text-[11px] text-slate-500 mt-2">Brokerage & account fees</p>
        </div>

        <div className="p-4 bg-slate-950/80 border border-slate-800 rounded-xl">
          <p className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider mb-1">Withholding Taxes</p>
          <div className="text-xl font-bold text-rose-400 font-mono">
            {data.total_taxes}
          </div>
          <p className="text-[11px] text-slate-500 mt-2">Taxes deducted</p>
        </div>
      </div>

      {/* Monthly Summary & Details */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* By Month */}
        <div className="bg-slate-950/80 border border-slate-800 rounded-xl p-5 space-y-4">
          <h3 className="text-sm font-semibold text-white">Income by Month</h3>
          <div className="space-y-2">
            {data.by_month.length === 0 ? (
              <p className="text-xs text-slate-500">No monthly income recorded.</p>
            ) : (
              data.by_month.map((m: any) => (
                <div key={m.month} className="flex justify-between text-xs p-2 rounded bg-slate-900/50 border border-slate-800/60">
                  <span className="text-slate-300 font-medium">{m.month}</span>
                  <span className="font-mono text-emerald-400 font-semibold">{m.income}</span>
                </div>
              ))
            )}
          </div>
        </div>

        {/* Traceable Transactions */}
        <div className="md:col-span-2 bg-slate-950/80 border border-slate-800 rounded-xl p-5 space-y-4">
          <h3 className="text-sm font-semibold text-white">Source Income Events ({data.items.length})</h3>
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-900/60 text-slate-400 uppercase text-[10px] tracking-wider border-b border-slate-800">
                <tr>
                  <th className="py-2.5 px-3">Date</th>
                  <th className="py-2.5 px-3">Type</th>
                  <th className="py-2.5 px-3">Symbol</th>
                  <th className="py-2.5 px-3">Gross</th>
                  <th className="py-2.5 px-3">Tax/Fee</th>
                  <th className="py-2.5 px-3">Net Cash</th>
                  <th className="py-2.5 px-3">Notes</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60">
                {data.items.length === 0 ? (
                  <tr>
                    <td colSpan={7} className="py-6 text-center text-slate-500">
                      No income records logged yet.
                    </td>
                  </tr>
                ) : (
                  data.items.map((it: any) => (
                    <tr key={it.id} className="hover:bg-slate-900/30">
                      <td className="py-2.5 px-3 text-slate-300">{it.trade_date}</td>
                      <td className="py-2.5 px-3">
                        <span className="px-1.5 py-0.5 rounded text-[10px] font-bold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                          {it.type}
                        </span>
                      </td>
                      <td className="py-2.5 px-3 font-semibold text-white">{it.symbol}</td>
                      <td className="py-2.5 px-3 font-mono text-slate-200">{it.gross_amount}</td>
                      <td className="py-2.5 px-3 font-mono text-slate-400">{it.tax} / {it.fee}</td>
                      <td className="py-2.5 px-3 font-mono font-semibold text-emerald-400">{it.net_amount}</td>
                      <td className="py-2.5 px-3 text-slate-400 text-[11px]">{it.notes || '-'}</td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
};
