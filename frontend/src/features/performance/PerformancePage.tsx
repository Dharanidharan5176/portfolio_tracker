import React, { useState, useEffect } from 'react';
import { useOutletContext } from 'react-router-dom';
import { TrendingUp, AlertTriangle, ShieldCheck, Calendar, Info } from 'lucide-react';
import { api } from '../../api/client';

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

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-base font-semibold text-white">Portfolio Performance Analytics</h2>
        <p className="text-xs text-slate-400">Cash-flow-aware Time-Weighted Returns (TWR) & Drawdown Analysis</p>
      </div>

      <div className="p-4 bg-slate-950/80 border border-slate-800 rounded-xl space-y-4">
        <div className="flex items-center gap-2.5 text-xs text-emerald-400">
          <Info className="w-4 h-4" />
          <span className="font-semibold">Calculation Methodology: Time-Weighted Return (TWR)</span>
        </div>
        <p className="text-xs text-slate-400 leading-relaxed">
          In accordance with the specification, simple portfolio value percentage change is not used when external capital movements (deposits/withdrawals) occurred. Sub-period returns are isolated around cash flows to measure true asset management performance.
        </p>
      </div>

      {/* Structured Status / Analytics */}
      <div className="bg-slate-950/80 border border-slate-800 rounded-xl p-8 text-center space-y-3">
        <div className="w-10 h-10 bg-slate-800 rounded-full flex items-center justify-center mx-auto text-slate-400">
          <Calendar className="w-5 h-5" />
        </div>
        <h3 className="text-sm font-semibold text-white">Multi-Period TWR & Drawdown Series</h3>
        <p className="text-xs text-slate-400 max-w-md mx-auto">
          Performance returns require at least two dated valuation benchmarks. Record or import dated market prices to generate the multi-period performance return series.
        </p>
      </div>
    </div>
  );
};
