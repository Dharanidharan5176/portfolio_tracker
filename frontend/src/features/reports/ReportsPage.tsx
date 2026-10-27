import React, { useState } from 'react';
import { useOutletContext } from 'react-router-dom';
import { FileText, Download, ShieldCheck, CheckCircle } from 'lucide-react';
import { api } from '../../api/client';

export const ReportsPage: React.FC = () => {
  const { selectedPortfolioId } = useOutletContext<{ selectedPortfolioId?: number }>();
  const [downloading, setDownloading] = useState<string | null>(null);

  const downloadReport = async (reportType: string, format: 'json' | 'csv') => {
    setDownloading(`${reportType}_${format}`);
    try {
      const res = await fetch(`/api/v1/reports/${reportType}?portfolio_id=${selectedPortfolioId || ''}&format=${format}`);
      if (format === 'json') {
        const data = await res.json();
        const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `${reportType}_report_${new Date().toISOString().slice(0, 10)}.json`;
        a.click();
      } else {
        const text = await res.text();
        const blob = new Blob([text], { type: 'text/csv' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `${reportType}_report_${new Date().toISOString().slice(0, 10)}.csv`;
        a.click();
      }
    } catch (err) {
      console.error(err);
    } finally {
      setDownloading(null);
    }
  };

  const reports = [
    {
      id: 'holdings',
      name: 'Holdings Snapshot Report',
      desc: 'Complete position quantities, cost basis, average cost, dated prices, market values, and weightings.',
    },
    {
      id: 'transactions',
      name: 'Transaction Ledger Audit Report',
      desc: 'Chronological immutable transaction history with gross/net breakdown, taxes, and fees.',
    },
    {
      id: 'income',
      name: 'Cash Flows & Income Summary',
      desc: 'Itemized dividends, interest, withholding taxes, deposits and withdrawals with monthly rollups.',
    },
    {
      id: 'data-quality',
      name: 'Data Quality & Integrity Report',
      desc: 'Full audit of price observation freshness, unresolved ledger anomalies, and verification flags.',
    },
  ];

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-base font-semibold text-white">Reports & Data Exports</h2>
        <p className="text-xs text-slate-400">Generate deterministic offline CSV and JSON exports for reporting</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {reports.map((r) => (
          <div key={r.id} className="bg-slate-950/80 border border-slate-800 rounded-xl p-5 flex flex-col justify-between space-y-4">
            <div className="space-y-1.5">
              <div className="flex items-center gap-2">
                <FileText className="w-4 h-4 text-emerald-400" />
                <h3 className="font-semibold text-sm text-white">{r.name}</h3>
              </div>
              <p className="text-xs text-slate-400 leading-relaxed">{r.desc}</p>
            </div>

            <div className="flex items-center gap-2 pt-2 border-t border-slate-800/80">
              <button
                onClick={() => downloadReport(r.id, 'csv')}
                disabled={downloading === `${r.id}_csv`}
                className="px-3 py-1.5 bg-slate-900 hover:bg-slate-800 text-slate-200 border border-slate-700 rounded text-xs flex items-center gap-1.5 font-medium"
              >
                <Download className="w-3.5 h-3.5 text-slate-400" /> Export CSV
              </button>
              <button
                onClick={() => downloadReport(r.id, 'json')}
                disabled={downloading === `${r.id}_json`}
                className="px-3 py-1.5 bg-slate-900 hover:bg-slate-800 text-slate-200 border border-slate-700 rounded text-xs flex items-center gap-1.5 font-medium"
              >
                <Download className="w-3.5 h-3.5 text-slate-400" /> Export JSON
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
