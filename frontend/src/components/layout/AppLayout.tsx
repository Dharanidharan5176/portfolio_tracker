import React, { useState, useEffect } from 'react';
import { NavLink, Outlet, useLocation } from 'react-router-dom';
import {
  LayoutDashboard,
  Briefcase,
  Layers,
  ArrowLeftRight,
  TrendingUp,
  PieChart,
  DollarSign,
  UploadCloud,
  ShieldAlert,
  Bell,
  FileText,
  Settings,
  Activity,
  ChevronDown
} from 'lucide-react';
import { api } from '../../api/client';
import { Portfolio } from '../../api/types';

export const AppLayout: React.FC = () => {
  const [portfolios, setPortfolios] = useState<Portfolio[]>([]);
  const [selectedPortfolioId, setSelectedPortfolioId] = useState<number | undefined>();
  const [unreadCount, setUnreadCount] = useState<number>(0);
  const [openIssuesCount, setOpenIssuesCount] = useState<number>(0);
  const location = useLocation();

  useEffect(() => {
    api.getPortfolios()
      .then((data) => {
        setPortfolios(data);
        if (data.length > 0 && !selectedPortfolioId) {
          setSelectedPortfolioId(data[0].id);
        }
      })
      .catch((err) => console.error('Failed to load portfolios:', err));

    api.getDashboard()
      .then((dash) => {
        setUnreadCount(dash.unread_notifications_count || 0);
        setOpenIssuesCount(dash.open_issues_count || 0);
      })
      .catch(() => {});
  }, []);

  const navItems = [
    { name: 'Dashboard', path: '/', icon: LayoutDashboard },
    { name: 'Portfolios', path: '/portfolios', icon: Briefcase },
    { name: 'Holdings', path: '/holdings', icon: Layers },
    { name: 'Transactions', path: '/transactions', icon: ArrowLeftRight },
    { name: 'Performance', path: '/performance', icon: TrendingUp },
    { name: 'Allocation', path: '/allocation', icon: PieChart },
    { name: 'Income & Cash', path: '/income', icon: DollarSign },
    { name: 'Import Center', path: '/imports', icon: UploadCloud },
    {
      name: 'Data Quality',
      path: '/data-quality',
      icon: ShieldAlert,
      badge: openIssuesCount > 0 ? openIssuesCount : null,
      badgeColor: 'bg-rose-500',
    },
    {
      name: 'Notifications',
      path: '/notifications',
      icon: Bell,
      badge: unreadCount > 0 ? unreadCount : null,
      badgeColor: 'bg-amber-500',
    },
    { name: 'Reports', path: '/reports', icon: FileText },
    { name: 'Settings', path: '/settings', icon: Settings },
    { name: 'System Health', path: '/system', icon: Activity },
  ];

  return (
    <div className="flex h-screen w-screen overflow-hidden bg-slate-900 text-slate-100 font-sans">
      {/* Sidebar */}
      <aside className="w-64 flex-shrink-0 bg-slate-950 border-r border-slate-800 flex flex-col">
        <div className="p-4 border-b border-slate-800 flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-emerald-500 flex items-center justify-center font-bold text-slate-950 shadow-md">
            PT
          </div>
          <div>
            <h1 className="font-semibold text-sm tracking-wide text-white">PORTFOLIO TRACKER</h1>
            <p className="text-xs text-slate-400">Local-First Ledger</p>
          </div>
        </div>

        {/* Portfolio Quick Selector */}
        <div className="p-3 border-b border-slate-800/60 bg-slate-900/40">
          <label className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider block mb-1">
            Active Portfolio
          </label>
          <div className="relative">
            <select
              value={selectedPortfolioId || ''}
              onChange={(e) => setSelectedPortfolioId(Number(e.target.value))}
              className="w-full bg-slate-800 text-xs text-slate-200 border border-slate-700 rounded-md py-1.5 px-2 appearance-none focus:outline-none focus:border-emerald-500 cursor-pointer"
            >
              {portfolios.length === 0 ? (
                <option value="">No Portfolios</option>
              ) : (
                portfolios.map((p) => (
                  <option key={p.id} value={p.id}>
                    {p.name} ({p.base_currency})
                  </option>
                ))
              )}
            </select>
            <ChevronDown className="w-3.5 h-3.5 text-slate-400 absolute right-2 top-2.5 pointer-events-none" />
          </div>
        </div>

        {/* Navigation Links */}
        <nav className="flex-1 overflow-y-auto p-3 space-y-1">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = location.pathname === item.path;
            return (
              <NavLink
                key={item.path}
                to={item.path}
                className={`flex items-center justify-between px-3 py-2 rounded-md text-xs font-medium transition-colors ${
                  isActive
                    ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/30'
                    : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60'
                }`}
              >
                <div className="flex items-center gap-2.5">
                  <Icon className={`w-4 h-4 ${isActive ? 'text-emerald-400' : 'text-slate-400'}`} />
                  <span>{item.name}</span>
                </div>
                {item.badge !== null && item.badge !== undefined && (
                  <span
                    className={`px-1.5 py-0.2 rounded-full text-[10px] font-bold text-white ${item.badgeColor}`}
                  >
                    {item.badge}
                  </span>
                )}
              </NavLink>
            );
          })}
        </nav>

        {/* Footer info */}
        <div className="p-3 border-t border-slate-800/80 text-[11px] text-slate-400 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-emerald-400 inline-block animate-pulse"></span>
            <span>127.0.0.1:8000</span>
          </div>
          <span>Offline Ready</span>
        </div>
      </aside>

      {/* Main Content Area */}
      <main className="flex-1 flex flex-col min-w-0 overflow-y-auto bg-slate-900">
        <header className="h-14 border-b border-slate-800 bg-slate-950/40 px-6 flex items-center justify-between flex-shrink-0">
          <div className="flex items-center gap-3">
            <span className="text-xs uppercase tracking-wider font-semibold text-slate-400">
              {navItems.find((n) => n.path === location.pathname)?.name || 'Local Portfolio'}
            </span>
            <span className="text-xs text-slate-600">•</span>
            <span className="text-xs text-slate-400">
              As of: <span className="text-slate-300 font-medium">{new Date().toISOString().slice(0, 10)}</span>
            </span>
          </div>

          <div className="flex items-center gap-4 text-xs">
            <div className="px-2.5 py-1 rounded bg-slate-800 border border-slate-700 text-slate-300">
              Source: <span className="text-emerald-400 font-medium">SQLite Local DB</span>
            </div>
          </div>
        </header>

        <div className="p-6 flex-1 min-w-0">
          <Outlet context={{ selectedPortfolioId, portfolios }} />
        </div>
      </main>
    </div>
  );
};
