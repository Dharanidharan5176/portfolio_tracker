import React, { useState, useEffect } from 'react';
import { Settings, Shield, HardDrive, Key, CheckCircle, Info, Save } from 'lucide-react';
import { api } from '../../api/client';

export const SettingsPage: React.FC = () => {
  const [settingsData, setSettingsData] = useState<any | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [saveSuccess, setSaveSuccess] = useState(false);
  const [formData, setFormData] = useState({
    base_currency: 'INR',
    timezone: 'Asia/Kolkata',
    stale_price_days: 7,
  });

  useEffect(() => {
    loadSettings();
  }, []);

  const loadSettings = () => {
    setLoading(true);
    api.getSettings()
      .then((data) => {
        setSettingsData(data);
        setFormData({
          base_currency: data.base_currency || 'INR',
          timezone: data.timezone || 'Asia/Kolkata',
          stale_price_days: data.stale_price_days || 7,
        });
        setLoading(false);
      })
      .catch((err) => {
        console.error(err);
        setLoading(false);
      });
  };

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    setSaveSuccess(false);
    try {
      await api.updateSettings(formData);
      setSaveSuccess(true);
      setTimeout(() => setSaveSuccess(false), 3000);
      loadSettings();
    } catch (err: any) {
      alert(`Failed to save settings: ${err.message}`);
    } finally {
      setSaving(false);
    }
  };

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

      {/* Config Settings Form */}
      {settingsData && (
        <form onSubmit={handleSave} className="bg-slate-950/80 border border-slate-800 rounded-xl p-5 space-y-5 text-xs">
          <div className="flex items-center justify-between">
            <h3 className="font-semibold text-sm text-white">Application Preferences</h3>
            {saveSuccess && (
              <span className="flex items-center gap-1.5 text-xs text-emerald-400 font-medium">
                <CheckCircle className="w-4 h-4" /> Settings updated
              </span>
            )}
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div className="space-y-1.5">
              <label className="text-slate-400 block font-medium">Base Currency</label>
              <input
                type="text"
                value={formData.base_currency}
                onChange={(e) => setFormData({ ...formData, base_currency: e.target.value.toUpperCase() })}
                maxLength={3}
                className="w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded text-slate-200 uppercase font-mono text-xs focus:outline-none focus:border-emerald-500"
                placeholder="INR, USD, EUR..."
                required
              />
              <span className="text-[11px] text-slate-500">Default currency for reporting and valuation</span>
            </div>

            <div className="space-y-1.5">
              <label className="text-slate-400 block font-medium">Application Timezone</label>
              <input
                type="text"
                value={formData.timezone}
                onChange={(e) => setFormData({ ...formData, timezone: e.target.value })}
                className="w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded text-slate-200 text-xs focus:outline-none focus:border-emerald-500"
                placeholder="Asia/Kolkata, UTC, America/New_York..."
                required
              />
              <span className="text-[11px] text-slate-500">Timezone used for trade day alignment</span>
            </div>

            <div className="space-y-1.5">
              <label className="text-slate-400 block font-medium">Stale Price Threshold (Days)</label>
              <input
                type="number"
                min={1}
                max={365}
                value={formData.stale_price_days}
                onChange={(e) => setFormData({ ...formData, stale_price_days: parseInt(e.target.value) || 7 })}
                className="w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded text-slate-200 text-xs focus:outline-none focus:border-emerald-500"
                required
              />
              <span className="text-[11px] text-slate-500">Days without updated price before holding is flagged stale</span>
            </div>

            <div className="space-y-1.5">
              <label className="text-slate-400 block font-medium">Market Data Provider</label>
              <div className="px-3 py-2 bg-slate-900/60 border border-slate-800 rounded text-slate-300 font-mono text-xs">
                {settingsData.market_data_provider} (local_csv)
              </div>
              <span className="text-[11px] text-slate-500">Zero external network dependency</span>
            </div>
          </div>

          <div className="pt-2 border-t border-slate-800 flex items-center justify-between">
            <span className="text-[11px] font-mono text-slate-500">Storage: {settingsData.data_dir}</span>
            <button
              type="submit"
              disabled={saving}
              className="px-4 py-2 bg-emerald-600 hover:bg-emerald-500 text-white rounded font-medium text-xs flex items-center gap-1.5 shadow-sm transition"
            >
              <Save className="w-3.5 h-3.5" />
              {saving ? 'Saving...' : 'Save Settings'}
            </button>
          </div>
        </form>
      )}
    </div>
  );
};
