import React, { useState, useEffect } from 'react';
import { useOutletContext } from 'react-router-dom';
import {
  ArrowLeftRight,
  PlusCircle,
  RotateCcw,
  Search,
  Filter,
  AlertTriangle,
  CheckCircle,
  Clock,
  X
} from 'lucide-react';
import { api } from '../../api/client';
import { TransactionItem, TransactionPreview, Account } from '../../api/types';

export const TransactionsPage: React.FC = () => {
  const { selectedPortfolioId } = useOutletContext<{ selectedPortfolioId?: number }>();
  const [transactions, setTransactions] = useState<TransactionItem[]>([]);
  const [accounts, setAccounts] = useState<Account[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [typeFilter, setTypeFilter] = useState('');
  const [reverseModalTx, setReverseModalTx] = useState<TransactionItem | null>(null);
  const [reverseReason, setReverseReason] = useState('');
  const [showAddModal, setShowAddModal] = useState(false);

  // New Transaction Form State
  const [newType, setNewType] = useState('BUY');
  const [newAccountId, setNewAccountId] = useState<number | undefined>();
  const [newSymbol, setNewSymbol] = useState('');
  const [newDate, setNewDate] = useState(new Date().toISOString().slice(0, 10));
  const [newQuantity, setNewQuantity] = useState('');
  const [newUnitPrice, setNewUnitPrice] = useState('');
  const [newGrossAmount, setNewGrossAmount] = useState('');
  const [newFee, setNewFee] = useState('0.00');
  const [newTax, setNewTax] = useState('0.00');
  const [newCurrency, setNewCurrency] = useState('INR');
  const [newRef, setNewRef] = useState('');
  const [newNotes, setNewNotes] = useState('');
  const [preview, setPreview] = useState<TransactionPreview | null>(null);
  const [previewError, setPreviewError] = useState<string | null>(null);
  const [submitError, setSubmitError] = useState<string | null>(null);

  const loadData = () => {
    setLoading(true);
    api.getTransactions(selectedPortfolioId, searchTerm || undefined, typeFilter || undefined)
      .then((res) => {
        setTransactions(res.items);
        setLoading(false);
      })
      .catch((err) => {
        console.error(err);
        setLoading(false);
      });

    if (selectedPortfolioId) {
      api.getAccounts(selectedPortfolioId).then((accs) => {
        setAccounts(accs);
        if (accs.length > 0 && !newAccountId) {
          setNewAccountId(accs[0].id);
        }
      });
    }
  };

  useEffect(() => {
    loadData();
  }, [selectedPortfolioId, typeFilter]);

  // Handle live preview calculation
  useEffect(() => {
    if (!showAddModal || !selectedPortfolioId || !newAccountId) return;
    setPreviewError(null);

    const payload: any = {
      portfolio_id: selectedPortfolioId,
      account_id: newAccountId,
      type: newType,
      trade_date: newDate,
      symbol: newSymbol ? newSymbol.trim().toUpperCase() : null,
      currency: newCurrency,
      fee: newFee || '0.00',
      tax: newTax || '0.00',
    };

    if (['BUY', 'SELL', 'SPLIT'].includes(newType)) {
      if (newQuantity) payload.quantity = newQuantity;
      if (newUnitPrice) payload.unit_price = newUnitPrice;
    }
    if (newGrossAmount) {
      payload.gross_amount = newGrossAmount;
    } else if (newQuantity && newUnitPrice) {
      payload.gross_amount = (Number(newQuantity) * Number(newUnitPrice)).toFixed(2);
    }

    api.previewTransaction(payload)
      .then(setPreview)
      .catch((err) => {
        setPreview(null);
        setPreviewError(err.message);
      });
  }, [showAddModal, newType, newAccountId, newSymbol, newDate, newQuantity, newUnitPrice, newGrossAmount, newFee, newTax]);

  const handleCreateTransaction = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitError(null);

    try {
      const payload: any = {
        portfolio_id: selectedPortfolioId,
        account_id: newAccountId,
        type: newType,
        trade_date: newDate,
        symbol: newSymbol ? newSymbol.trim().toUpperCase() : null,
        quantity: newQuantity || null,
        unit_price: newUnitPrice || null,
        gross_amount: newGrossAmount || (newQuantity && newUnitPrice ? (Number(newQuantity) * Number(newUnitPrice)).toFixed(2) : null),
        fee: newFee || '0.00',
        tax: newTax || '0.00',
        currency: newCurrency,
        external_ref: newRef || null,
        notes: newNotes || null,
      };

      await api.createTransaction(payload);
      setShowAddModal(false);
      resetForm();
      loadData();
    } catch (err: any) {
      setSubmitError(err.message || 'Failed to create transaction');
    }
  };

  const resetForm = () => {
    setNewSymbol('');
    setNewQuantity('');
    setNewUnitPrice('');
    setNewGrossAmount('');
    setNewFee('0.00');
    setNewTax('0.00');
    setNewRef('');
    setNewNotes('');
    setPreview(null);
    setSubmitError(null);
  };

  const handleReverse = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!reverseModalTx) return;

    try {
      await api.reverseTransaction(reverseModalTx.id, reverseReason || 'User requested reversal');
      setReverseModalTx(null);
      setReverseReason('');
      loadData();
    } catch (err: any) {
      alert(`Reversal failed: ${err.message}`);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header and Controls */}
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h2 className="text-base font-semibold text-white">Transaction Ledger</h2>
          <p className="text-xs text-slate-400">Authoritative immutable financial transaction history</p>
        </div>

        <div className="flex flex-wrap items-center gap-3">
          {/* Search Box */}
          <div className="relative">
            <Search className="w-3.5 h-3.5 text-slate-400 absolute left-3 top-2.5 pointer-events-none" />
            <input
              type="text"
              placeholder="Search symbol..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && loadData()}
              className="bg-slate-950 border border-slate-800 rounded px-3 py-1.5 pl-8 text-xs text-white focus:outline-none focus:border-emerald-500 w-44"
            />
          </div>

          {/* Type Filter */}
          <select
            value={typeFilter}
            onChange={(e) => setTypeFilter(e.target.value)}
            className="bg-slate-950 text-xs text-slate-200 border border-slate-800 rounded px-2.5 py-1.5 focus:outline-none focus:border-emerald-500"
          >
            <option value="">All Types</option>
            <option value="BUY">BUY</option>
            <option value="SELL">SELL</option>
            <option value="CASH_DEPOSIT">DEPOSIT</option>
            <option value="CASH_WITHDRAWAL">WITHDRAWAL</option>
            <option value="DIVIDEND">DIVIDEND</option>
            <option value="FEE">FEE</option>
            <option value="SPLIT">SPLIT</option>
            <option value="CORRECTION_REVERSAL">REVERSAL</option>
          </select>

          <button
            onClick={() => setShowAddModal(true)}
            className="px-3.5 py-1.5 bg-emerald-500 hover:bg-emerald-600 text-slate-950 font-semibold text-xs rounded-md flex items-center gap-1.5 transition-colors"
          >
            <PlusCircle className="w-4 h-4" /> Add Transaction
          </button>
        </div>
      </div>

      {/* Ledger Table */}
      <div className="bg-slate-950/80 border border-slate-800 rounded-xl overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-900/60 text-slate-400 uppercase text-[10px] tracking-wider border-b border-slate-800">
              <tr>
                <th className="py-3 px-4 font-semibold">ID</th>
                <th className="py-3 px-4 font-semibold">Trade Date</th>
                <th className="py-3 px-4 font-semibold">Type</th>
                <th className="py-3 px-4 font-semibold">Symbol</th>
                <th className="py-3 px-4 font-semibold">Quantity</th>
                <th className="py-3 px-4 font-semibold">Unit Price</th>
                <th className="py-3 px-4 font-semibold">Gross Amount</th>
                <th className="py-3 px-4 font-semibold">Fee / Tax</th>
                <th className="py-3 px-4 font-semibold">Net Cash Impact</th>
                <th className="py-3 px-4 font-semibold">Ref / Notes</th>
                <th className="py-3 px-4 font-semibold text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60">
              {loading ? (
                <tr>
                  <td colSpan={11} className="py-8 text-center text-slate-500">
                    <Clock className="w-4 h-4 animate-spin inline-block mr-2" />
                    Loading ledger records...
                  </td>
                </tr>
              ) : transactions.length === 0 ? (
                <tr>
                  <td colSpan={11} className="py-8 text-center text-slate-500">
                    No transactions match the selected filters.
                  </td>
                </tr>
              ) : (
                transactions.map((tx) => (
                  <tr
                    key={tx.id}
                    className={`hover:bg-slate-900/40 transition-colors ${
                      tx.is_reversed ? 'opacity-50 line-through bg-slate-900/20' : ''
                    }`}
                  >
                    <td className="py-3 px-4 font-mono text-slate-400">#{tx.id}</td>
                    <td className="py-3 px-4 text-slate-300 font-medium">{tx.trade_date}</td>
                    <td className="py-3 px-4">
                      <span
                        className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                          tx.type === 'BUY'
                            ? 'bg-blue-500/20 text-blue-400 border border-blue-500/30'
                            : tx.type === 'SELL'
                            ? 'bg-purple-500/20 text-purple-400 border border-purple-500/30'
                            : tx.type === 'CASH_DEPOSIT'
                            ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30'
                            : tx.type === 'CORRECTION_REVERSAL'
                            ? 'bg-rose-500/20 text-rose-400 border border-rose-500/30'
                            : 'bg-slate-800 text-slate-300'
                        }`}
                      >
                        {tx.type}
                      </span>
                    </td>
                    <td className="py-3 px-4 font-semibold text-white">{tx.symbol || '-'}</td>
                    <td className="py-3 px-4 text-slate-200 font-mono">{tx.quantity || '-'}</td>
                    <td className="py-3 px-4 text-slate-300 font-mono">{tx.unit_price || '-'}</td>
                    <td className="py-3 px-4 text-slate-200 font-mono">{tx.gross_amount}</td>
                    <td className="py-3 px-4 text-[11px] text-slate-400 font-mono">
                      {tx.fee} / {tx.tax}
                    </td>
                    <td className="py-3 px-4 font-semibold font-mono text-slate-100">
                      {tx.currency} {tx.net_amount}
                    </td>
                    <td className="py-3 px-4 text-[11px] text-slate-400 max-w-xs truncate">
                      {tx.external_ref ? `[${tx.external_ref}] ` : ''}{tx.notes || ''}
                    </td>
                    <td className="py-3 px-4 text-right">
                      {!tx.is_reversed && tx.type !== 'CORRECTION_REVERSAL' && (
                        <button
                          onClick={() => setReverseModalTx(tx)}
                          className="px-2 py-1 text-[11px] bg-slate-900 hover:bg-rose-500/20 text-slate-400 hover:text-rose-400 border border-slate-800 rounded transition-colors flex items-center gap-1 ml-auto"
                          title="Reverse this transaction"
                        >
                          <RotateCcw className="w-3 h-3" /> Reverse
                        </button>
                      )}
                      {tx.is_reversed && (
                        <span className="text-[10px] text-rose-400">Reversed</span>
                      )}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Add Transaction Modal with Live Preview */}
      {showAddModal && (
        <div className="fixed inset-0 bg-slate-950/80 backdrop-blur-sm flex items-center justify-center p-4 z-50 overflow-y-auto">
          <div className="bg-slate-900 border border-slate-800 rounded-xl max-w-2xl w-full p-6 space-y-4 my-8">
            <div className="flex justify-between items-center">
              <h3 className="text-base font-bold text-white">Add Financial Transaction</h3>
              <button onClick={() => setShowAddModal(false)} className="text-slate-400 hover:text-white">
                <X className="w-5 h-5" />
              </button>
            </div>

            {submitError && (
              <div className="p-3 bg-rose-500/10 border border-rose-500/30 rounded text-rose-400 text-xs">
                {submitError}
              </div>
            )}

            <form onSubmit={handleCreateTransaction} className="space-y-4">
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                <div>
                  <label className="block text-xs font-medium text-slate-300 mb-1">Transaction Type</label>
                  <select
                    value={newType}
                    onChange={(e) => setNewType(e.target.value)}
                    className="w-full bg-slate-950 border border-slate-800 rounded px-2.5 py-1.5 text-xs text-white focus:outline-none focus:border-emerald-500"
                  >
                    <option value="BUY">BUY (Stock / Asset)</option>
                    <option value="SELL">SELL (Stock / Asset)</option>
                    <option value="CASH_DEPOSIT">CASH DEPOSIT</option>
                    <option value="CASH_WITHDRAWAL">CASH WITHDRAWAL</option>
                    <option value="DIVIDEND">DIVIDEND</option>
                    <option value="INTEREST">INTEREST</option>
                    <option value="FEE">FEE</option>
                    <option value="SPLIT">STOCK SPLIT</option>
                  </select>
                </div>

                <div>
                  <label className="block text-xs font-medium text-slate-300 mb-1">Account</label>
                  <select
                    value={newAccountId || ''}
                    onChange={(e) => setNewAccountId(Number(e.target.value))}
                    className="w-full bg-slate-950 border border-slate-800 rounded px-2.5 py-1.5 text-xs text-white focus:outline-none focus:border-emerald-500"
                  >
                    {accounts.map((a) => (
                      <option key={a.id} value={a.id}>
                        {a.name} ({a.currency})
                      </option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block text-xs font-medium text-slate-300 mb-1">Trade Date</label>
                  <input
                    type="date"
                    required
                    value={newDate}
                    onChange={(e) => setNewDate(e.target.value)}
                    className="w-full bg-slate-950 border border-slate-800 rounded px-2.5 py-1.5 text-xs text-white focus:outline-none focus:border-emerald-500"
                  />
                </div>
              </div>

              {/* Conditional fields based on type */}
              {['BUY', 'SELL', 'DIVIDEND', 'SPLIT'].includes(newType) && (
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                  <div>
                    <label className="block text-xs font-medium text-slate-300 mb-1">Symbol / Ticker</label>
                    <input
                      type="text"
                      required={['BUY', 'SELL', 'SPLIT'].includes(newType)}
                      placeholder="e.g. RELIANCE, INFY"
                      value={newSymbol}
                      onChange={(e) => setNewSymbol(e.target.value.toUpperCase())}
                      className="w-full bg-slate-950 border border-slate-800 rounded px-2.5 py-1.5 text-xs text-white focus:outline-none focus:border-emerald-500"
                    />
                  </div>

                  {['BUY', 'SELL', 'SPLIT'].includes(newType) && (
                    <>
                      <div>
                        <label className="block text-xs font-medium text-slate-300 mb-1">
                          {newType === 'SPLIT' ? 'Split Ratio (e.g. 2 for 2:1)' : 'Quantity'}
                        </label>
                        <input
                          type="number"
                          step="0.0001"
                          required
                          value={newQuantity}
                          onChange={(e) => setNewQuantity(e.target.value)}
                          className="w-full bg-slate-950 border border-slate-800 rounded px-2.5 py-1.5 text-xs text-white focus:outline-none focus:border-emerald-500"
                        />
                      </div>

                      {newType !== 'SPLIT' && (
                        <div>
                          <label className="block text-xs font-medium text-slate-300 mb-1">Unit Price</label>
                          <input
                            type="number"
                            step="0.0001"
                            required
                            value={newUnitPrice}
                            onChange={(e) => setNewUnitPrice(e.target.value)}
                            className="w-full bg-slate-950 border border-slate-800 rounded px-2.5 py-1.5 text-xs text-white focus:outline-none focus:border-emerald-500"
                          />
                        </div>
                      )}
                    </>
                  )}
                </div>
              )}

              {/* Amount, Fee, Tax */}
              <div className="grid grid-cols-1 sm:grid-cols-4 gap-3">
                <div>
                  <label className="block text-xs font-medium text-slate-300 mb-1">
                    {['BUY', 'SELL'].includes(newType) ? 'Gross Consideration' : 'Amount'}
                  </label>
                  <input
                    type="number"
                    step="0.01"
                    placeholder={newQuantity && newUnitPrice ? (Number(newQuantity) * Number(newUnitPrice)).toFixed(2) : '0.00'}
                    value={newGrossAmount}
                    onChange={(e) => setNewGrossAmount(e.target.value)}
                    className="w-full bg-slate-950 border border-slate-800 rounded px-2.5 py-1.5 text-xs text-white focus:outline-none focus:border-emerald-500"
                  />
                </div>

                <div>
                  <label className="block text-xs font-medium text-slate-300 mb-1">Fee</label>
                  <input
                    type="number"
                    step="0.01"
                    value={newFee}
                    onChange={(e) => setNewFee(e.target.value)}
                    className="w-full bg-slate-950 border border-slate-800 rounded px-2.5 py-1.5 text-xs text-white focus:outline-none focus:border-emerald-500"
                  />
                </div>

                <div>
                  <label className="block text-xs font-medium text-slate-300 mb-1">Tax / Withholding</label>
                  <input
                    type="number"
                    step="0.01"
                    value={newTax}
                    onChange={(e) => setNewTax(e.target.value)}
                    className="w-full bg-slate-950 border border-slate-800 rounded px-2.5 py-1.5 text-xs text-white focus:outline-none focus:border-emerald-500"
                  />
                </div>

                <div>
                  <label className="block text-xs font-medium text-slate-300 mb-1">Currency</label>
                  <input
                    type="text"
                    maxLength={3}
                    value={newCurrency}
                    onChange={(e) => setNewCurrency(e.target.value.toUpperCase())}
                    className="w-full bg-slate-950 border border-slate-800 rounded px-2.5 py-1.5 text-xs text-white focus:outline-none focus:border-emerald-500"
                  />
                </div>
              </div>

              {/* Reference & Notes */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-medium text-slate-300 mb-1">External Reference ID</label>
                  <input
                    type="text"
                    placeholder="e.g. Broker Txn ID"
                    value={newRef}
                    onChange={(e) => setNewRef(e.target.value)}
                    className="w-full bg-slate-950 border border-slate-800 rounded px-2.5 py-1.5 text-xs text-white focus:outline-none focus:border-emerald-500"
                  />
                </div>
                <div>
                  <label className="block text-xs font-medium text-slate-300 mb-1">Notes</label>
                  <input
                    type="text"
                    placeholder="e.g. Monthly SIP or trade note"
                    value={newNotes}
                    onChange={(e) => setNewNotes(e.target.value)}
                    className="w-full bg-slate-950 border border-slate-800 rounded px-2.5 py-1.5 text-xs text-white focus:outline-none focus:border-emerald-500"
                  />
                </div>
              </div>

              {/* Live Preview Panel */}
              {preview && (
                <div className="p-3.5 bg-slate-950 rounded-lg border border-slate-800/80 text-xs space-y-2">
                  <div className="flex items-center gap-2 font-semibold text-slate-300">
                    <CheckCircle className="w-3.5 h-3.5 text-emerald-400" />
                    <span>Live Transaction Impact Preview</span>
                  </div>
                  <div className="grid grid-cols-3 gap-2 text-[11px] pt-1">
                    <div>
                      <span className="text-slate-500">Net Cash Impact:</span>
                      <p className="font-semibold text-white">{preview.net_cash_impact} {newCurrency}</p>
                    </div>
                    <div>
                      <span className="text-slate-500">Cost Basis Delta:</span>
                      <p className="font-semibold text-slate-300">{preview.estimated_cost_basis_impact} {newCurrency}</p>
                    </div>
                    <div>
                      <span className="text-slate-500">New Position Qty:</span>
                      <p className="font-semibold text-emerald-400">{preview.new_quantity_balance}</p>
                    </div>
                  </div>

                  {preview.warnings.length > 0 && (
                    <div className="p-2 bg-amber-500/10 border border-amber-500/20 rounded text-amber-400 text-[11px] space-y-1">
                      {preview.warnings.map((w, idx) => (
                        <p key={idx} className="flex items-center gap-1.5">
                          <AlertTriangle className="w-3.5 h-3.5 flex-shrink-0" />
                          <span>{w}</span>
                        </p>
                      ))}
                    </div>
                  )}
                </div>
              )}

              <div className="flex justify-end gap-2 pt-2">
                <button
                  type="button"
                  onClick={() => setShowAddModal(false)}
                  className="px-3 py-1.5 bg-slate-800 text-slate-300 hover:bg-slate-700 text-xs rounded"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-1.5 bg-emerald-500 hover:bg-emerald-600 text-slate-950 font-bold text-xs rounded"
                >
                  Confirm & Post Transaction
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Reversal Confirmation Modal */}
      {reverseModalTx && (
        <div className="fixed inset-0 bg-slate-950/80 backdrop-blur-sm flex items-center justify-center p-4 z-50">
          <div className="bg-slate-900 border border-slate-800 rounded-xl max-w-md w-full p-6 space-y-4">
            <h3 className="text-sm font-semibold text-white">Reverse Transaction #{reverseModalTx.id}</h3>
            <p className="text-xs text-slate-400 leading-relaxed">
              In accordance with financial ledger integrity, posted transactions are not deleted. A reversing compensating transaction will be created, restoring cash and position balances.
            </p>

            <form onSubmit={handleReverse} className="space-y-4">
              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">Reason for Reversal</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Entered incorrect quantity or date"
                  value={reverseReason}
                  onChange={(e) => setReverseReason(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded px-3 py-2 text-xs text-white focus:outline-none focus:border-emerald-500"
                />
              </div>

              <div className="flex justify-end gap-2 pt-2">
                <button
                  type="button"
                  onClick={() => setReverseModalTx(null)}
                  className="px-3 py-1.5 bg-slate-800 text-slate-300 hover:bg-slate-700 text-xs rounded"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-3.5 py-1.5 bg-rose-500 hover:bg-rose-600 text-white font-semibold text-xs rounded"
                >
                  Confirm Reversal
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
