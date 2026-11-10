import React from 'react';
import { createBrowserRouter, Navigate } from 'react-router-dom';
import { AppLayout } from '../components/layout/AppLayout';
import { DashboardPage } from '../features/dashboard/DashboardPage';
import { PortfoliosPage } from '../features/portfolios/PortfoliosPage';
import { HoldingsPage } from '../features/holdings/HoldingsPage';
import { TransactionsPage } from '../features/transactions/TransactionsPage';
import { PerformancePage } from '../features/performance/PerformancePage';
import { AllocationPage } from '../features/allocation/AllocationPage';
import { IncomePage } from '../features/income/IncomePage';
import { ImportsPage } from '../features/imports/ImportsPage';
import { DataQualityPage } from '../features/data-quality/DataQualityPage';
import { NotificationsPage } from '../features/notifications/NotificationsPage';
import { ReportsPage } from '../features/reports/ReportsPage';
import { SettingsPage } from '../features/settings/SettingsPage';
import { SystemPage } from '../features/system/SystemPage';

export const router = createBrowserRouter([
  {
    path: '/',
    element: <AppLayout />,
    children: [
      { index: true, element: <DashboardPage /> },
      { path: 'dashboard', element: <Navigate to="/" replace /> },
      { path: 'portfolios', element: <PortfoliosPage /> },
      { path: 'holdings', element: <HoldingsPage /> },
      { path: 'transactions', element: <TransactionsPage /> },
      { path: 'transactions/new', element: <TransactionsPage /> },
      { path: 'performance', element: <PerformancePage /> },
      { path: 'allocation', element: <AllocationPage /> },
      { path: 'income', element: <IncomePage /> },
      { path: 'imports', element: <ImportsPage /> },
      { path: 'data-quality', element: <DataQualityPage /> },
      { path: 'notifications', element: <NotificationsPage /> },
      { path: 'reports', element: <ReportsPage /> },
      { path: 'settings', element: <SettingsPage /> },
      { path: 'system', element: <SystemPage /> },
    ],
  },
]);

