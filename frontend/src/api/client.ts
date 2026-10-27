import {
  DashboardSummary,
  Portfolio,
  Account,
  TransactionItem,
  TransactionPreview,
  ImportPreviewResponse,
  HoldingItem
} from './types';

const API_BASE = '/api/v1';

async function request<T>(endpoint: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${endpoint}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...options?.headers,
    },
  });

  if (!res.ok) {
    let errorDetail = 'API Request Failed';
    try {
      const errJson = await res.json();
      errorDetail = errJson.message || errJson.detail || JSON.stringify(errJson);
    } catch {
      errorDetail = `HTTP ${res.status}: ${res.statusText}`;
    }
    throw new Error(errorDetail);
  }

  return res.json();
}

export const api = {
  // System
  getHealth: () => request<any>('/system/health'),
  getAuditEvents: () => request<any>('/system/audit-events'),

  // Dashboard
  getDashboard: (portfolioId?: number) =>
    request<DashboardSummary>(portfolioId ? `/dashboard?portfolio_id=${portfolioId}` : '/dashboard'),

  // Portfolios & Accounts
  getPortfolios: () => request<Portfolio[]>('/portfolios'),
  createPortfolio: (data: { name: string; base_currency: string; timezone?: string; benchmark_symbol?: string; notes?: string }) =>
    request<Portfolio>('/portfolios', { method: 'POST', body: JSON.stringify(data) }),
  getAccounts: (portfolioId?: number) =>
    request<Account[]>(portfolioId ? `/accounts?portfolio_id=${portfolioId}` : '/accounts'),
  createAccount: (data: { portfolio_id: number; name: string; account_type: string; institution_label: string; currency: string }) =>
    request<Account>('/accounts', { method: 'POST', body: JSON.stringify(data) }),

  // Holdings
  getHoldings: (portfolioId?: number, staleOnly?: boolean) => {
    const params = new URLSearchParams();
    if (portfolioId) params.append('portfolio_id', portfolioId.toString());
    if (staleOnly) params.append('stale_only', 'true');
    return request<HoldingItem[]>(`/holdings?${params.toString()}`);
  },
  getHoldingDetail: (instrumentId: number, portfolioId?: number) =>
    request<any>(portfolioId ? `/holdings/${instrumentId}?portfolio_id=${portfolioId}` : `/holdings/${instrumentId}`),
  recordManualPrice: (data: { instrument_id: number; observed_at: string; price: string; currency: string; notes?: string }) =>
    request<any>('/holdings/prices', { method: 'POST', body: JSON.stringify(data) }),

  // Transactions
  getTransactions: (portfolioId?: number, symbol?: string, type?: string) => {
    const params = new URLSearchParams();
    if (portfolioId) params.append('portfolio_id', portfolioId.toString());
    if (symbol) params.append('symbol', symbol);
    if (type) params.append('type', type);
    return request<{ items: TransactionItem[]; total: number }>(`/transactions?${params.toString()}`);
  },
  previewTransaction: (data: any) =>
    request<TransactionPreview>('/transactions/preview', { method: 'POST', body: JSON.stringify(data) }),
  createTransaction: (data: any) =>
    request<TransactionItem>('/transactions', { method: 'POST', body: JSON.stringify(data) }),
  reverseTransaction: (id: number, reason: string) =>
    request<TransactionItem>(`/transactions/${id}/reverse?reason=${encodeURIComponent(reason)}`, { method: 'POST' }),

  // Allocation & Income
  getAllocation: (portfolioId?: number) =>
    request<any>(portfolioId ? `/allocation?portfolio_id=${portfolioId}` : '/allocation'),
  getIncome: (portfolioId?: number) =>
    request<any>(portfolioId ? `/income?portfolio_id=${portfolioId}` : '/income'),

  // Imports
  uploadAndPreviewCSV: async (file: File, sourceType: string = 'transactions') => {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('source_type', sourceType);

    const res = await fetch(`${API_BASE}/imports/preview`, {
      method: 'POST',
      body: formData,
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ message: res.statusText }));
      throw new Error(err.message || 'CSV preview failed');
    }
    return res.json() as Promise<ImportPreviewResponse>;
  },
  confirmImport: async (formData: FormData) => {
    const res = await fetch(`${API_BASE}/imports/confirm`, {
      method: 'POST',
      body: formData,
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ message: res.statusText }));
      throw new Error(err.message || 'Import commit failed');
    }
    return res.json();
  },
  getImportBatches: () => request<any[]>('/imports'),

  // Data Quality & Notifications
  getDataQualityIssues: () => request<any[]>('/data-quality/issues'),
  resolveIssue: (id: number, reason: string) =>
    request<any>(`/data-quality/issues/${id}/resolve?reason=${encodeURIComponent(reason)}`, { method: 'POST' }),
  getNotifications: () => request<any[]>('/notifications'),
  markNotificationRead: (id: number) =>
    request<any>(`/notifications/${id}/read`, { method: 'POST' }),

  // Settings
  getSettings: () => request<any>('/settings'),
};
