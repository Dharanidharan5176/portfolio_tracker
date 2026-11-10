import React, { useState, useEffect } from 'react';
import { Bell, CheckCircle2, ShieldAlert, Clock } from 'lucide-react';
import { api } from '../../api/client';

export const NotificationsPage: React.FC = () => {
  const [notifications, setNotifications] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  const loadNotifications = () => {
    setLoading(true);
    api.getNotifications()
      .then((data) => {
        setNotifications(data);
        setLoading(false);
      })
      .catch((err) => {
        console.error(err);
        setLoading(false);
      });
  };

  useEffect(() => {
    loadNotifications();
  }, []);

  const handleMarkRead = async (id: number) => {
    try {
      await api.markNotificationRead(id);
      loadNotifications();
    } catch (err) {
      console.error(err);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-base font-semibold text-white">Notifications & Alerts</h2>
          <p className="text-xs text-slate-400">In-app notifications for data anomalies, stale observations, and backups</p>
        </div>
      </div>

      <div className="bg-slate-950/80 border border-slate-800 rounded-xl p-5 space-y-3">
        {loading ? (
          <p className="text-xs text-slate-500 text-center py-6">Loading notifications...</p>
        ) : notifications.length === 0 ? (
          <div className="text-center py-8 text-slate-400 space-y-2">
            <CheckCircle2 className="w-6 h-6 text-emerald-400 mx-auto" />
            <p className="text-xs">No pending notifications. You are completely up to date.</p>
          </div>
        ) : (
          notifications.map((n) => (
            <div
              key={n.id}
              className={`p-3.5 rounded-lg border text-xs flex items-start justify-between gap-4 transition-colors ${
                n.status === 'unread' ? 'bg-slate-900 border-slate-700' : 'bg-slate-950/60 border-slate-800/60 opacity-60'
              }`}
            >
              <div className="space-y-1">
                <div className="flex items-center gap-2">
                  <span className="font-semibold text-slate-200">{n.title}</span>
                  <span className="text-[10px] text-slate-500">{n.created_at?.slice(0, 16)}</span>
                </div>
                <p className="text-slate-400 text-[11px] leading-relaxed">{n.message}</p>
              </div>

              {n.status === 'unread' && (
                <button
                  onClick={() => handleMarkRead(n.id)}
                  className="px-2.5 py-1 text-[10px] bg-slate-800 hover:bg-slate-700 text-slate-300 rounded border border-slate-700 flex-shrink-0"
                >
                  Mark Read
                </button>
              )}
            </div>
          ))
        )}
      </div>
    </div>
  );
};

