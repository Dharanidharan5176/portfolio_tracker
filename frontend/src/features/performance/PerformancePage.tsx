import React, { useState, useEffect } from 'react';
import { useOutletContext } from 'react-router-dom';
import { TrendingUp, TrendingDown, AlertTriangle, ShieldCheck, Calendar, Info, Activity } from 'lucide-react';

export const PerformancePage: React.FC = () => {
  const { selectedPortfolioId } = useOutletContext<{ selectedPortfolioId?: number }>();
  const [data, setData] = useState<any | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    fetch(`/api/v1/performance?portfolio_id=${selectedPortfolioId || ''}`)
      .then((res) => res.json())
      .then((res) => {
        setData(res);
        setLoading(false);
      })
      .catch((err) => {
        console.error(err);
        setLoading(false);
      });
  }, [selectedPortfolioId]);

  const hasPerformance = data && data.status === 'valid' && data.twr_pct !== null && data.twr_pct !== undefined;
  const isPositive = hasPerformance && parseFloat(data.twr_pct) >= 0;

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-base font-semibold text-white">Portfolio Performance Analytics</h2>
        <p className="text-xs text-slate-400">Cash-flow-aware Time-Weighted Returns (TWR) & Drawdown Analysis</p>
      </div>

      <div className="p-4 bg-slate-950/80 border border-slate-800 rounded-xl space-y-2">
        <div className="flex items-center gap-2 text-xs text-emerald-400 font-semibold">
          <Info className="w-4 h-4" />
          <span>Calculation Methodology: Time-Weighted Return (TWR)</span>
        </div>
        <p className="text-xs text-slate-400 leading-relaxed">
          Sub-period returns are isolated around cash flows (deposits/withdrawals) using standard GIPS-compliant compounding:
          <code className="text-emerald-300 ml-1">R_TWR = ∏(1 + R_i) - 1</code>. This prevents distortion from external capital movements.
        </p>
      </div>

      {loading ? (
        <div className="p-12 text-center text-xs text-slate-400">Loading performance calculations...</div>
      ) : hasPerformance ? (
        <div className="space-y-6">
          {/* Top Metric Cards */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="p-4 bg-slate-950/80 border border-slate-800 rounded-xl space-y-1">
              <span className="text-xs text-slate-400">Time-Weighted Return (TWR)</span>
              <div className="flex items-center gap-2">
                {isPositive ? (
                  <TrendingUp className="w-5 h-5 text-emerald-400" />
                ) : (
                  <TrendingDown className="w-5 h-5 text-rose-400" />
                )}
                <span className={`text-xl font-bold ${isPositive ? 'text-emerald-400' : 'text-rose-400'}`}>
                  {isPositive ? '+' : ''}{data.twr_pct}%
                </span>
              </div>
              <span className="text-[11px] text-slate-500">Compounded across {data.sub_periods?.length || 0} sub-period(s)</span>
            </div>

            <div className="p-4 bg-slate-950/80 border border-slate-800 rounded-xl space-y-1">
              <span className="text-xs text-slate-400">Max Drawdown</span>
              <div className="flex items-center gap-2">
                <Activity className="w-5 h-5 text-amber-400" />
                <span className="text-xl font-bold text-amber-400">
                  {data.max_drawdown_pct}%
                </span>
              </div>
              <span className="text-[11px] text-slate-500">From highest historical peak</span>
            </div>

            <div className="p-4 bg-slate-950/80 border border-slate-800 rounded-xl space-y-1">
              <span className="text-xs text-slate-400">Evaluation Window</span>
              <div className="text-sm font-semibold text-white mt-1">
                {data.start_date} <span className="text-slate-500">→</span> {data.end_date}
              </div>
              <span className="text-[11px] text-slate-500">Currency: {data.base_currency}</span>
            </div>

            <div className="p-4 bg-slate-950/80 border border-slate-800 rounded-xl space-y-1">
              <span className="text-xs text-slate-400">Integrity & Method</span>
              <div className="flex items-center gap-1.5 text-xs text-emerald-400 mt-1 font-medium">
                <ShieldCheck className="w-4 h-4" />
                <span>Deterministic Local Calc</span>
              </div>
              <span className="text-[11px] text-slate-500">No simulated or mocked return</span>
            </div>
          </div>

          {/* Sub-Periods Table */}
          {data.sub_periods && data.sub_periods.length > 0 && (
            <div className="bg-slate-950/80 border border-slate-800 rounded-xl overflow-hidden">
              <div className="p-4 border-b border-slate-800">
                <h3 className="text-xs font-semibold text-slate-200 uppercase tracking-wider">
                  Cash Flow Boundary Sub-Periods
                </h3>
              </div>
              <div className="overflow-x-auto">
                <table className="w-full text-xs text-left">
                  <thead className="bg-slate-900/60 text-slate-400 border-b border-slate-800">
                    <tr>
                      <th className="py-2.5 px-4 font-medium">Sub-Period</th>
                      <th className="py-2.5 px-4 font-medium text-right">Start Value</th>
                      <th className="py-2.5 px-4 font-medium text-right">Net Cash Flow</th>
                      <th className="py-2.5 px-4 font-medium text-right">End Value</th>
                      <th className="py-2.5 px-4 font-medium text-right">Sub-Period Return</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800/60 font-mono">
                    {data.sub_periods.map((sp: any, idx: number) => {
                      const retVal = parseFloat(sp.return_pct);
                      return (
                        <tr key={idx} className="hover:bg-slate-900/40">
                          <td className="py-2.5 px-4 font-sans text-slate-300">
                            {sp.start} <span className="text-slate-500">→</span> {sp.end}
                          </td>
                          <td className="py-2.5 px-4 text-right text-slate-300">{sp.start_value}</td>
                          <td className="py-2.5 px-4 text-right text-slate-400">{sp.cash_flow}</td>
                          <td className="py-2.5 px-4 text-right text-slate-300">{sp.end_value}</td>
                          <td className={`py-2.5 px-4 text-right font-semibold ${retVal >= 0 ? 'text-emerald-400' : 'text-rose-400'}`}>
                            {retVal >= 0 ? '+' : ''}{sp.return_pct}%
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* Drawdown Series Table */}
          {data.drawdown_series && data.drawdown_series.length > 0 && (
            <div className="bg-slate-950/80 border border-slate-800 rounded-xl overflow-hidden">
              <div className="p-4 border-b border-slate-800">
                <h3 className="text-xs font-semibold text-slate-200 uppercase tracking-wider">
                  Historical Valuation Peak & Drawdown Series
                </h3>
              </div>
              <div className="overflow-x-auto">
                <table className="w-full text-xs text-left">
                  <thead className="bg-slate-900/60 text-slate-400 border-b border-slate-800">
                    <tr>
                      <th className="py-2.5 px-4 font-medium">Date</th>
                      <th className="py-2.5 px-4 font-medium text-right">Portfolio Value</th>
                      <th className="py-2.5 px-4 font-medium text-right">Peak Value</th>
                      <th className="py-2.5 px-4 font-medium text-right">Drawdown %</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800/60 font-mono">
                    {data.drawdown_series.map((dd: any, idx: number) => (
                      <tr key={idx} className="hover:bg-slate-900/40">
                        <td className="py-2.5 px-4 font-sans text-slate-300">{dd.date}</td>
                        <td className="py-2.5 px-4 text-right text-slate-300">{dd.portfolio_value}</td>
                        <td className="py-2.5 px-4 text-right text-slate-400">{dd.peak_value}</td>
                        <td className="py-2.5 px-4 text-right text-amber-400 font-semibold">{dd.drawdown_pct}%</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>
      ) : (
        <div className="bg-slate-950/80 border border-slate-800 rounded-xl p-8 text-center space-y-3">
          <div className="w-10 h-10 bg-slate-800 rounded-full flex items-center justify-center mx-auto text-slate-400">
            <Calendar className="w-5 h-5" />
          </div>
          <h3 className="text-sm font-semibold text-white">Multi-Period TWR & Drawdown Series</h3>
          <p className="text-xs text-slate-400 max-w-md mx-auto">
            {data?.message || 'Performance returns require at least two dated transaction benchmarks with prices. Record transactions or import CSVs to see the compounded return series.'}
          </p>
        </div>
      )}
    </div>
  );
};
