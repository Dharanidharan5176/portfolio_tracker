import React, { useState, useEffect } from 'react';
import { ShieldAlert, CheckCircle, RefreshCw, AlertCircle, XCircle } from 'lucide-react';
import { api } from '../../api/client';

export const DataQualityPage: React.FC = () => {
  const [issues, setIssues] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [resolvingId, setResolvingId] = useState<number | null>(null);
  const [resolveReason, setResolveReason] = useState('');

  const loadIssues = () => {
    setLoading(true);
    api.getDataQualityIssues()
      .then((data) => {
        setIssues(data);
        setLoading(false);
      })
      .catch((err) => {
        console.error(err);
        setLoading(false);
      });
  };

  useEffect(() => {
    loadIssues();
  }, []);

  const handleResolve = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!resolvingId || !resolveReason) return;
    try {
      await api.resolveIssue(resolvingId, resolveReason);
      setResolvingId(null);
      setResolveReason('');
      loadIssues();
    } catch (err: any) {
      alert(err.message || 'Resolution failed');
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-base font-semibold text-white">Data Quality & Integrity Queue</h2>
          <p className="text-xs text-slate-400">Automated validation checks detect anomalies, stale prices, and ledger inconsistencies</p>
        </div>
        <button
          onClick={loadIssues}
          className="px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs rounded border border-slate-700 flex items-center gap-1.5"
        >
          <RefreshCw className="w-3.5 h-3.5" /> Re-run Validation
        </button>
      </div>

      <div className="bg-slate-950/80 border border-slate-800 rounded-xl overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-900/60 text-slate-400 uppercase text-[10px] tracking-wider border-b border-slate-800">
              <tr>
                <th className="py-3 px-4 font-semibold">Severity</th>
                <th className="py-3 px-4 font-semibold">Issue Key</th>
                <th className="py-3 px-4 font-semibold">Category</th>
                <th className="py-3 px-4 font-semibold">Details</th>
                <th className="py-3 px-4 font-semibold">First / Last Seen</th>
                <th className="py-3 px-4 font-semibold">Status</th>
                <th className="py-3 px-4 font-semibold text-right">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60">
              {loading ? (
                <tr>
                  <td colSpan={7} className="py-8 text-center text-slate-500">
                    Checking ledger data integrity...
                  </td>
                </tr>
              ) : issues.length === 0 ? (
                <tr>
                  <td colSpan={7} className="py-8 text-center text-emerald-400/80">
                    <CheckCircle className="w-5 h-5 mx-auto mb-2 text-emerald-400" />
                    No open data quality issues detected. All holding and transaction records are sound.
                  </td>
                </tr>
              ) : (
                issues.map((iss) => (
                  <tr key={iss.id} className="hover:bg-slate-900/40">
                    <td className="py-3 px-4">
                      <span
                        className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase ${
                          iss.severity === 'critical'
                            ? 'bg-rose-500/20 text-rose-400 border border-rose-500/30'
                            : iss.severity === 'error'
                            ? 'bg-amber-500/20 text-amber-400 border border-amber-500/30'
                            : 'bg-blue-500/20 text-blue-400 border border-blue-500/30'
                        }`}
                      >
                        {iss.severity}
                      </span>
                    </td>
                    <td className="py-3 px-4 font-medium text-slate-200">{iss.issue_key}</td>
                    <td className="py-3 px-4 text-slate-400 capitalize">{iss.category}</td>
                    <td className="py-3 px-4 text-slate-300 max-w-sm">{iss.details || '-'}</td>
                    <td className="py-3 px-4 text-slate-400 text-[11px]">
                      {iss.first_seen.slice(0, 10)} / {iss.last_seen.slice(0, 10)}
                    </td>
                    <td className="py-3 px-4">
                      <span className="text-[11px] font-semibold text-slate-300 capitalize">{iss.status}</span>
                    </td>
                    <td className="py-3 px-4 text-right">
                      {iss.status === 'open' && (
                        <button
                          onClick={() => setResolvingId(iss.id)}
                          className="px-2.5 py-1 text-[11px] bg-slate-800 hover:bg-slate-700 text-slate-200 rounded border border-slate-700"
                        >
                          Resolve
                        </button>
                      )}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {resolvingId && (
        <div className="fixed inset-0 bg-slate-950/80 backdrop-blur-sm flex items-center justify-center p-4 z-50">
          <div className="bg-slate-900 border border-slate-800 rounded-xl max-w-md w-full p-6 space-y-4">
            <h3 className="text-sm font-semibold text-white">Resolve Data Quality Issue</h3>
            <p className="text-xs text-slate-400">
              Critical integrity issues require an audited resolution note to prevent silent data suppression.
            </p>
            <form onSubmit={handleResolve} className="space-y-4">
              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">Resolution Reason</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Verified price split adjustment via provider circular"
                  value={resolveReason}
                  onChange={(e) => setResolveReason(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded px-3 py-2 text-xs text-white focus:outline-none focus:border-emerald-500"
                />
              </div>

              <div className="flex justify-end gap-2">
                <button
                  type="button"
                  onClick={() => setResolvingId(null)}
                  className="px-3 py-1.5 bg-slate-800 text-slate-300 hover:bg-slate-700 text-xs rounded"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-3.5 py-1.5 bg-emerald-500 hover:bg-emerald-600 text-slate-950 font-semibold text-xs rounded"
                >
                  Confirm Resolution
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
