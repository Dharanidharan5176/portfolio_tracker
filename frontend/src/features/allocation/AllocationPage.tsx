import React, { useState, useEffect } from 'react';
import { useOutletContext } from 'react-router-dom';
import { PieChart, AlertTriangle, ShieldCheck, Layers } from 'lucide-react';
import { api } from '../../api/client';

export const AllocationPage: React.FC = () => {
  const { selectedPortfolioId } = useOutletContext<{ selectedPortfolioId?: number }>();
  const [data, setData] = useState<any | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    api.getAllocation(selectedPortfolioId)
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
    return <div className="text-xs text-slate-400 p-8 text-center">Computing portfolio exposure...</div>;
  }

  if (!data || !data.by_asset_class) {
    return <div className="text-xs text-slate-400 p-8 text-center">No portfolio data available.</div>;
  }

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-base font-semibold text-white">Asset Allocation & Exposure</h2>
        <p className="text-xs text-slate-400">Portfolio concentration and asset class distribution</p>
      </div>

      {/* Concentration Alerts */}
      {data.concentration?.high_concentration_alert ? (
        <div className="p-3.5 bg-amber-500/10 border border-amber-500/30 rounded-xl flex items-center gap-3 text-xs text-amber-400">
          <AlertTriangle className="w-5 h-5 flex-shrink-0" />
          <div>
            <p className="font-semibold">Portfolio Concentration Alert</p>
            <p className="text-[11px] text-amber-300">
              Largest holding: {data.concentration.largest_holding_weight}% | Top 5 holdings: {data.concentration.top_5_holdings_weight}%. Informational warning.
            </p>
          </div>
        </div>
      ) : (
        <div className="p-3 bg-emerald-500/10 border border-emerald-500/20 rounded-xl flex items-center gap-2.5 text-xs text-emerald-400">
          <ShieldCheck className="w-4 h-4" />
          <span>Concentration is within normal risk thresholds (Top holding &lt; 25%, Top 5 &lt; 60%).</span>
        </div>
      )}

      {/* Asset Class Distribution */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="bg-slate-950/80 border border-slate-800 rounded-xl p-5 space-y-4">
          <h3 className="text-sm font-semibold text-white">By Asset Class</h3>
          <div className="space-y-3">
            {data.by_asset_class.map((item: any) => (
              <div key={item.category} className="space-y-1">
                <div className="flex justify-between text-xs">
                  <span className="text-slate-300 font-medium">{item.category}</span>
                  <span className="text-slate-400">{item.market_value} ({item.weight}%)</span>
                </div>
                <div className="h-2 w-full bg-slate-800 rounded-full overflow-hidden">
                  <div className="h-full bg-emerald-500 rounded-full" style={{ width: `${item.weight}%` }} />
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* By Holding */}
        <div className="bg-slate-950/80 border border-slate-800 rounded-xl p-5 space-y-4">
          <h3 className="text-sm font-semibold text-white">Individual Positions Weight</h3>
          <div className="space-y-3 max-h-72 overflow-y-auto pr-1">
            {data.by_holding.map((h: any) => (
              <div key={h.symbol} className="space-y-1">
                <div className="flex justify-between text-xs">
                  <span className="text-slate-300 font-medium">{h.symbol} <span className="text-slate-500 font-normal">({h.display_name})</span></span>
                  <span className="text-slate-400">{h.weight}%</span>
                </div>
                <div className="h-1.5 w-full bg-slate-800 rounded-full overflow-hidden">
                  <div className="h-full bg-blue-500 rounded-full" style={{ width: `${h.weight}%` }} />
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

