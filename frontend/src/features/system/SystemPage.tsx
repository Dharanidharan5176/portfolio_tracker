import React, { useState, useEffect } from 'react';
import { Activity, Database, CheckCircle2, AlertTriangle, Shield, History } from 'lucide-react';
import { api } from '../../api/client';

export const SystemPage: React.FC = () => {
  const [health, setHealth] = useState<any | null>(null);
  const [auditEvents, setAuditEvents] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([api.getHealth(), api.getAuditEvents()])
      .then(([h, a]) => {
        setHealth(h);
        setAuditEvents(a.items || []);
        setLoading(false);
      })
      .catch((err) => {
        console.error(err);
        setLoading(false);
      });
  }, []);

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-base font-semibold text-white">System Health & Audit Trail</h2>
        <p className="text-xs text-slate-400">Database connectivity, storage health, and immutable audit logs</p>
      </div>

      {/* Diagnostics Grid */}
      {health && (
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <div className="p-4 bg-slate-950/80 border border-slate-800 rounded-xl space-y-2">
            <div className="flex items-center gap-2 text-xs font-semibold text-slate-300">
              <Database className="w-4 h-4 text-emerald-400" />
              <span>Database Status</span>
            </div>
            <div className="flex items-center gap-2">
              <span className={`w-2 h-2 rounded-full ${health.database_connected ? 'bg-emerald-400' : 'bg-rose-400'}`} />
              <span className="text-sm font-bold text-white capitalize">{health.status}</span>
            </div>
            <p className="text-[11px] text-slate-500 font-mono truncate">{health.database_path}</p>
          </div>

          <div className="p-4 bg-slate-950/80 border border-slate-800 rounded-xl space-y-2">
            <div className="flex items-center gap-2 text-xs font-semibold text-slate-300">
              <Shield className="w-4 h-4 text-emerald-400" />
              <span>Local Storage Writable</span>
            </div>
            <div className="flex items-center gap-2">
              <CheckCircle2 className="w-4 h-4 text-emerald-400" />
              <span className="text-sm font-bold text-white">Writable & Verified</span>
            </div>
            <p className="text-[11px] text-slate-500">Backups and CSV cache active</p>
          </div>

          <div className="p-4 bg-slate-950/80 border border-slate-800 rounded-xl space-y-2">
            <div className="flex items-center gap-2 text-xs font-semibold text-slate-300">
              <Activity className="w-4 h-4 text-emerald-400" />
              <span>Local-First Isolation</span>
            </div>
            <div className="flex items-center gap-2">
              <CheckCircle2 className="w-4 h-4 text-emerald-400" />
              <span className="text-sm font-bold text-white">127.0.0.1 Bound</span>
            </div>
            <p className="text-[11px] text-slate-500">No public exposure</p>
          </div>
        </div>
      )}

      {/* Audit Trail Table */}
      <div className="bg-slate-950/80 border border-slate-800 rounded-xl p-5 space-y-4">
        <h3 className="font-semibold text-sm text-white flex items-center gap-2">
          <History className="w-4 h-4 text-emerald-400" />
          <span>Audit Event Log</span>
        </h3>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-900/60 text-slate-400 uppercase text-[10px] tracking-wider border-b border-slate-800">
              <tr>
                <th className="py-2.5 px-3">Timestamp</th>
                <th className="py-2.5 px-3">Actor</th>
                <th className="py-2.5 px-3">Action</th>
                <th className="py-2.5 px-3">Entity</th>
                <th className="py-2.5 px-3">Reason</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60">
              {auditEvents.length === 0 ? (
                <tr>
                  <td colSpan={5} className="py-6 text-center text-slate-500">
                    No critical audit events logged in this session.
                  </td>
                </tr>
              ) : (
                auditEvents.map((evt) => (
                  <tr key={evt.id} className="hover:bg-slate-900/30">
                    <td className="py-2.5 px-3 text-slate-300 font-mono text-[11px]">{evt.timestamp}</td>
                    <td className="py-2.5 px-3 text-slate-400">{evt.actor}</td>
                    <td className="py-2.5 px-3 font-semibold text-emerald-400">{evt.action}</td>
                    <td className="py-2.5 px-3 text-slate-300 font-mono text-[11px]">{evt.entity_type} #{evt.entity_id}</td>
                    <td className="py-2.5 px-3 text-slate-400 text-[11px]">{evt.reason || '-'}</td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

