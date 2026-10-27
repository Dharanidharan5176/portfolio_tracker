import React, { useState, useEffect } from 'react';
import { Settings, Shield, HardDrive, Key, CheckCircle, Info } from 'lucide-react';
import { api } from '../../api/client';

export const SettingsPage: React.FC = () => {
  const [settingsData, setSettingsData] = useState<any | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.getSettings()
      .then((data) => {
        setSettingsData(data);
        setLoading(false);
      })
      .catch((err) => {
        console.error(err);
        setLoading(false);
      });
  }, []);

  return (
    <div className="space-y-6 max-w-4xl">
      <div>
        <h2 className="text-base font-semibold text-white">System Settings & Privacy Disclosure</h2>
        <p className="text-xs text-slate-400">Local runtime configurations and privacy guarantees</p>
      </div>

      {/* Local-First Disclosure */}
      <div className="p-4 bg-emerald-500/10 border border-emerald-500/30 rounded-xl space-y-2">
        <div className="flex items-center gap-2 text-xs font-semibold text-emerald-400">
          <Shield className="w-4 h-4" />
          <span>Local-Only Architecture Guarantee</span>
        </div>
        <p className="text-xs text-slate-300 leading-relaxed">
          The Local Portfolio Tracker runs exclusively on your local computer. No brokerage passwords or API keys are stored in plaintext. No tracking telemetry, cloud databases, external CDNs, or remote fonts are used. All financial records, prices, and database files remain in your local directory.
        </p>
      </div>

      {/* Config Settings Display */}
      {settingsData && (
        <div className="bg-slate-950/80 border border-slate-800 rounded-xl p-5 space-y-4 text-xs">
          <h3 className="font-semibold text-sm text-white">Active Configuration</h3>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div className="p-3 bg-slate-900/60 rounded border border-slate-800">
              <span className="text-slate-400 block mb-1">Base Currency</span>
              <span className="font-semibold text-white text-sm">{settingsData.base_currency}</span>
            </div>

            <div className="p-3 bg-slate-900/60 rounded border border-slate-800">
              <span className="text-slate-400 block mb-1">Application Timezone</span>
              <span className="font-semibold text-white text-sm">{settingsData.timezone}</span>
            </div>

            <div className="p-3 bg-slate-900/60 rounded border border-slate-800">
              <span className="text-slate-400 block mb-1">Market Data Provider</span>
              <span className="font-semibold text-white text-sm">{settingsData.market_data_provider}</span>
              <span className="text-[10px] text-slate-500 block mt-1">Zero internet required for manual/CSV mode</span>
            </div>

            <div className="p-3 bg-slate-900/60 rounded border border-slate-800">
              <span className="text-slate-400 block mb-1">Data Storage Path</span>
              <span className="font-mono text-[11px] text-slate-300 truncate block">{settingsData.data_dir}</span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
