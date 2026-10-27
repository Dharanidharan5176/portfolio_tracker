import React, { useState, useEffect } from 'react';
import { useOutletContext } from 'react-router-dom';
import {
  Layers,
  Filter,
  TrendingUp,
  TrendingDown,
  Clock,
  Edit3,
  Calendar,
  X,
  CheckCircle,
  AlertTriangle
} from 'lucide-react';
import { api } from '../../api/client';
import { HoldingItem } from '../../api/types';

export const HoldingsPage: React.FC = () => {
  const { selectedPortfolioId } = useOutletContext<{ selectedPortfolioId?: number }>();
  const [holdings, setHoldings] = useState<HoldingItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [staleOnly, setStaleOnly] = useState(false);
  const [selectedHolding, setSelectedHolding] = useState<any | null>(null);
  const [showOverrideModal, setShowOverrideModal] = useState<HoldingItem | null>(null);
  const [overridePrice, setOverridePrice] = useState('');
  const [overrideDate, setOverrideDate] = useState(new Date().toISOString().slice(0, 16));
  const [overrideNotes, setOverrideNotes] = useState('');
  const [overrideError, setOverrideError] = useState<string | null>(null);

  const loadHoldings = () => {
    setLoading(true);
    api.getHoldings(selectedPortfolioId, staleOnly)
      .then((data) => {
        setHoldings(data);
        setLoading(false);
      })
      .catch((err) => {
        console.error(err);
        setLoading(false);
      });
  };

  useEffect(() => {
    loadHoldings();
  }, [selectedPortfolioId, staleOnly]);

  const openHoldingDetail = async (instId: number) => {
    try {
      const detail = await api.getHoldingDetail(instId, selectedPortfolioId);
      setSelectedHolding(detail);
    } catch (err) {
      console.error(err);
    }
  };

  const handleManualOverride = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!showOverrideModal) return;
    setOverrideError(null);

    try {
      await api.recordManualPrice({
        instrument_id: showOverrideModal.instrument_id,
        price: overridePrice,
        observed_at: new Date(overrideDate).toISOString(),
        currency: showOverrideModal.currency,
        notes: overrideNotes,
      });
      setShowOverrideModal(null);
      setOverridePrice('');
      setOverrideNotes('');
      loadHoldings();
      if (selectedHolding) {
        openHoldingDetail(showOverrideModal.instrument_id);
      }
    } catch (err: any) {
      setOverrideError(err.message || 'Failed to record manual price');
    }
  };

  return (
    <div className="space-y-6">
      {/* Header and Controls */}
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h2 className="text-base font-semibold text-white">Holdings & Positions</h2>
          <p className="text-xs text-slate-400">Authoritative position quantities derived from transactions</p>
        </div>

        <div className="flex items-center gap-3">
          <label className="flex items-center gap-2 text-xs text-slate-300 cursor-pointer bg-slate-950 px-3 py-1.5 rounded border border-slate-800">
            <input
              type="checkbox"
              checked={staleOnly}
              onChange={(e) => setStaleOnly(e.target.checked)}
              className="rounded bg-slate-900 border-slate-700 text-emerald-500 focus:ring-0"
            />
            <span>Show Stale / Missing Prices Only</span>
          </label>
        </div>
      </div>

      {/* Holdings Table */}
      <div className="bg-slate-950/80 border border-slate-800 rounded-xl overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-900/60 text-slate-400 uppercase text-[10px] tracking-wider border-b border-slate-800">
              <tr>
                <th className="py-3 px-4 font-semibold">Symbol</th>
                <th className="py-3 px-4 font-semibold">Asset Type</th>
                <th className="py-3 px-4 font-semibold">Quantity</th>
                <th className="py-3 px-4 font-semibold">Avg Cost</th>
                <th className="py-3 px-4 font-semibold">Cost Basis</th>
                <th className="py-3 px-4 font-semibold">Latest Price</th>
                <th className="py-3 px-4 font-semibold">Price Date</th>
                <th className="py-3 px-4 font-semibold">Market Value</th>
                <th className="py-3 px-4 font-semibold">Unrealized P&L</th>
                <th className="py-3 px-4 font-semibold">Weight</th>
                <th className="py-3 px-4 font-semibold">Status</th>
                <th className="py-3 px-4 font-semibold text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60">
              {loading ? (
                <tr>
                  <td colSpan={12} className="py-8 text-center text-slate-500">
                    <Clock className="w-4 h-4 animate-spin inline-block mr-2" />
                    Calculating position valuations...
                  </td>
                </tr>
              ) : holdings.length === 0 ? (
                <tr>
                  <td colSpan={12} className="py-8 text-center text-slate-500">
                    No matching holdings found.
                  </td>
                </tr>
              ) : (
                holdings.map((h) => {
                  const pnl = Number(h.unrealized_pnl || 0);
                  const isPositive = pnl >= 0;
                  return (
                    <tr
                      key={h.instrument_id}
                      onClick={() => openHoldingDetail(h.instrument_id)}
                      className="hover:bg-slate-900/40 cursor-pointer transition-colors"
                    >
                      <td className="py-3 px-4 font-medium text-white">
                        <div className="font-semibold text-emerald-400">{h.symbol}</div>
                        <div className="text-[10px] text-slate-400">{h.display_name}</div>
                      </td>
                      <td className="py-3 px-4 text-slate-300 capitalize">{h.asset_type}</td>
                      <td className="py-3 px-4 text-slate-200 font-mono">{h.quantity}</td>
                      <td className="py-3 px-4 text-slate-300 font-mono">{h.average_cost}</td>
                      <td className="py-3 px-4 text-slate-300 font-mono">{h.cost_basis}</td>
                      <td className="py-3 px-4 text-slate-200 font-mono">
                        {h.latest_price ? (
                          <span>
                            {h.latest_price} {h.is_manual_override && <span className="text-[10px] text-amber-400 font-sans ml-1">(override)</span>}
                          </span>
                        ) : (
                          <span className="text-amber-400 italic">None</span>
                        )}
                      </td>
                      <td className="py-3 px-4 text-[11px] text-slate-400">
                        {h.price_date ? h.price_date.slice(0, 10) : '-'}
                      </td>
                      <td className="py-3 px-4 font-medium text-white font-mono">
                        {h.market_value || '-'}
                      </td>
                      <td className="py-3 px-4">
                        {h.unrealized_pnl ? (
                          <span className={`font-semibold font-mono ${isPositive ? 'text-emerald-400' : 'text-rose-400'}`}>
                            {isPositive ? '+' : ''}{h.unrealized_pnl} ({h.unrealized_pnl_pct}%)
                          </span>
                        ) : (
                          '-'
                        )}
                      </td>
                      <td className="py-3 px-4 text-slate-300 font-mono">{h.weight}%</td>
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
                      <td className="py-3 px-4 text-right" onClick={(e) => e.stopPropagation()}>
                        <button
                          onClick={() => {
                            setShowOverrideModal(h);
                            setOverridePrice(h.latest_price || '');
                          }}
                          className="p-1 hover:bg-slate-800 text-slate-400 hover:text-white rounded"
                          title="Record Audited Price Observation"
                        >
                          <Edit3 className="w-3.5 h-3.5" />
                        </button>
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Manual Price Observation Modal */}
      {showOverrideModal && (
        <div className="fixed inset-0 bg-slate-950/80 backdrop-blur-sm flex items-center justify-center p-4 z-50">
          <div className="bg-slate-900 border border-slate-800 rounded-xl max-w-md w-full p-6 space-y-4">
            <div className="flex justify-between items-center">
              <h3 className="text-sm font-semibold text-white">
                Record Price Observation: {showOverrideModal.symbol}
              </h3>
              <button onClick={() => setShowOverrideModal(null)} className="text-slate-400 hover:text-white">
                <X className="w-4 h-4" />
              </button>
            </div>

            <p className="text-xs text-slate-400 leading-relaxed">
              Records an explicit, dated price observation with full audit history. This will not silently overwrite provider prices.
            </p>

            {overrideError && (
              <div className="p-3 bg-rose-500/10 border border-rose-500/30 rounded text-rose-400 text-xs">
                {overrideError}
              </div>
            )}

            <form onSubmit={handleManualOverride} className="space-y-4">
              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">Observation Date & Time (UTC)</label>
                <input
                  type="datetime-local"
                  required
                  value={overrideDate}
                  onChange={(e) => setOverrideDate(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded px-3 py-2 text-xs text-white focus:outline-none focus:border-emerald-500"
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">Price ({showOverrideModal.currency})</label>
                <input
                  type="number"
                  step="0.0001"
                  required
                  placeholder="e.g. 1520.50"
                  value={overridePrice}
                  onChange={(e) => setOverridePrice(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded px-3 py-2 text-xs text-white focus:outline-none focus:border-emerald-500"
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">Reason / Notes</label>
                <input
                  type="text"
                  placeholder="e.g. Verified from NSE closing circular"
                  value={overrideNotes}
                  onChange={(e) => setOverrideNotes(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded px-3 py-2 text-xs text-white focus:outline-none focus:border-emerald-500"
                />
              </div>

              <div className="flex justify-end gap-2 pt-2">
                <button
                  type="button"
                  onClick={() => setShowOverrideModal(null)}
                  className="px-3 py-1.5 bg-slate-800 text-slate-300 hover:bg-slate-700 text-xs rounded"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-3.5 py-1.5 bg-emerald-500 hover:bg-emerald-600 text-slate-950 font-semibold text-xs rounded"
                >
                  Save Observation
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Holding Detail Drawer / Modal */}
      {selectedHolding && (
        <div className="fixed inset-0 bg-slate-950/80 backdrop-blur-sm flex items-center justify-end z-40">
          <div className="bg-slate-900 border-l border-slate-800 w-full max-w-xl h-full p-6 overflow-y-auto space-y-6">
            <div className="flex justify-between items-start">
              <div>
                <h3 className="text-lg font-bold text-white">{selectedHolding.instrument.canonical_symbol}</h3>
                <p className="text-xs text-slate-400">{selectedHolding.instrument.display_name} • {selectedHolding.instrument.asset_type}</p>
              </div>
              <button onClick={() => setSelectedHolding(null)} className="p-1 hover:bg-slate-800 text-slate-400 rounded">
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Position Summary */}
            <div className="grid grid-cols-2 gap-3 p-3 bg-slate-950/60 rounded-lg border border-slate-800/80 text-xs">
              <div>
                <span className="text-slate-400">Quantity Held:</span>
                <p className="font-semibold text-slate-200">{selectedHolding.position.quantity}</p>
              </div>
              <div>
                <span className="text-slate-400">Average Cost Basis:</span>
                <p className="font-semibold text-slate-200">{selectedHolding.position.average_cost}</p>
              </div>
              <div>
                <span className="text-slate-400">Total Cost:</span>
                <p className="font-semibold text-slate-200">{selectedHolding.position.cost_basis}</p>
              </div>
              <div>
                <span className="text-slate-400">Market Value:</span>
                <p className="font-semibold text-emerald-400">{selectedHolding.position.market_value || 'N/A'}</p>
              </div>
            </div>

            {/* Price Observations History */}
            <div>
              <h4 className="text-xs font-semibold text-slate-300 uppercase tracking-wider mb-2">
                Price Observations ({selectedHolding.price_history.length})
              </h4>
              <div className="max-h-48 overflow-y-auto border border-slate-800/80 rounded-lg">
                <table className="w-full text-left text-[11px]">
                  <thead className="bg-slate-950 text-slate-400 border-b border-slate-800">
                    <tr>
                      <th className="py-2 px-3">Date</th>
                      <th className="py-2 px-3">Price</th>
                      <th className="py-2 px-3">Source</th>
                      <th className="py-2 px-3">Type</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800/60">
                    {selectedHolding.price_history.map((p: any) => (
                      <tr key={p.id}>
                        <td className="py-2 px-3 text-slate-300">{p.observed_at.slice(0, 16)}</td>
                        <td className="py-2 px-3 font-semibold text-white">{p.price}</td>
                        <td className="py-2 px-3 text-slate-400">{p.provider}</td>
                        <td className="py-2 px-3">
                          {p.is_manual_override ? (
                            <span className="text-amber-400 text-[10px]">Manual</span>
                          ) : (
                            <span className="text-slate-400 text-[10px]">Import</span>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>

            {/* Traded Transactions History */}
            <div>
              <h4 className="text-xs font-semibold text-slate-300 uppercase tracking-wider mb-2">
                Transaction Ledger Trace ({selectedHolding.transaction_history.length})
              </h4>
              <div className="space-y-1.5 max-h-56 overflow-y-auto">
                {selectedHolding.transaction_history.map((t: any) => (
                  <div key={t.id} className="p-2 rounded bg-slate-950/60 border border-slate-800 text-[11px] flex justify-between">
                    <div>
                      <span className="font-semibold text-slate-300">{t.type}</span> • {t.trade_date}
                      {t.is_reversed && <span className="ml-2 text-rose-400">(Reversed)</span>}
                    </div>
                    <div className="text-right">
                      <span className="text-slate-400">{t.quantity ? `${t.quantity} @ ` : ''}{t.unit_price || ''}</span>
                      <span className="ml-2 font-mono text-white">{t.net_amount}</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
