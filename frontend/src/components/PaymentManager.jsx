import React, { useState, useEffect } from 'react';
import { fetchAdminPayments, executeScheduledPayment } from '../services/api';
import { RefreshCw, CheckCircle, XCircle, Clock, Search, Filter } from 'lucide-react';

const PaymentManager = () => {
    const [payments, setPayments] = useState([]);
    const [loading, setLoading] = useState(true);
    const today = new Date().toISOString().slice(0, 10);
    const [statusFilter, setStatusFilter] = useState('');
    const [startDate, setStartDate] = useState(today);
    const [endDate, setEndDate] = useState(today);
    const [actionMsg, setActionMsg] = useState(null);

    const summary = payments.reduce(
        (acc, payment) => {
            const status = payment.status || 'pending';
            const amount = Number(payment.amount || 0);
            if (!acc[status]) {
                acc[status] = { count: 0, total: 0 };
            }
            acc[status].count += 1;
            acc[status].total += amount;
            return acc;
        },
        {}
    );

    const getSummary = (key) => summary[key] || { count: 0, total: 0 };
    const pendingSummary = getSummary('pending');
    const postedSummary = getSummary('paid');
    const declinedSummary = getSummary('declined');
    const retryingSummary = getSummary('retrying');

    const loadPayments = async () => {
        setLoading(true);
        try {
            const data = await fetchAdminPayments({
                status: statusFilter || null,
                startDate,
                endDate
            });
            setPayments(data);
        } catch (e) {
            console.error(e);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        loadPayments();
    }, [statusFilter, startDate, endDate]);

    const handleRerun = async (paymentId) => {
        try {
            setActionMsg({ type: 'info', text: "Rerunning payment..." });
            await executeScheduledPayment(paymentId);
            setActionMsg({ type: 'success', text: "Payment Successful!" });
            loadPayments();
        } catch (e) {
            setActionMsg({ type: 'error', text: e.message });
        }
    };

    return (
        <div className="glass-panel p-6 rounded-xl border border-slate-200 shadow-sm bg-white">
            <div className="flex justify-between items-center mb-6">
                <div>
                    <h3 className="text-xl font-bold text-slate-900">Payment Management</h3>
                    <p className="text-sm text-slate-500">Monitor and rerun daily scheduled payments</p>
                </div>

                <div className="flex flex-wrap gap-3 items-center">
                    <div className="flex items-center gap-2">
                        <label className="text-[10px] uppercase tracking-wide text-slate-400">From</label>
                        <input
                            type="date"
                            value={startDate}
                            onChange={(e) => setStartDate(e.target.value)}
                            className="bg-slate-50 border border-slate-200 rounded px-2 py-1.5 text-sm text-slate-700 outline-none focus:border-blue-500/50"
                        />
                    </div>
                    <div className="flex items-center gap-2">
                        <label className="text-[10px] uppercase tracking-wide text-slate-400">To</label>
                        <input
                            type="date"
                            value={endDate}
                            onChange={(e) => setEndDate(e.target.value)}
                            className="bg-slate-50 border border-slate-200 rounded px-2 py-1.5 text-sm text-slate-700 outline-none focus:border-blue-500/50"
                        />
                    </div>

                    <select
                        value={statusFilter}
                        onChange={(e) => setStatusFilter(e.target.value)}
                        className="bg-slate-50 border border-slate-200 rounded px-3 py-2 text-sm text-slate-700 outline-none focus:border-blue-500/50"
                    >
                        <option value="">All</option>
                        <option value="pending">Pending</option>
                        <option value="paid">Posted</option>
                        <option value="declined">Declined</option>
                        <option value="retrying">Retrying</option>
                    </select>

                    <button
                        onClick={loadPayments}
                        className="p-2 bg-slate-100 hover:bg-slate-200 rounded text-slate-600 transition-all"
                    >
                        <RefreshCw size={18} />
                    </button>
                </div>
            </div>

            {actionMsg && (
                <div className={`p-3 rounded mb-4 text-sm flex items-center gap-2 ${actionMsg.type === 'success' ? 'bg-emerald-50 text-emerald-700 border border-emerald-100' :
                        actionMsg.type === 'error' ? 'bg-red-50 text-red-700 border border-red-100' :
                            'bg-blue-50 text-blue-700 border border-blue-100'
                    }`}>
                    {actionMsg.text}
                </div>
            )}

            <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
                <div className="p-4 rounded-lg border border-slate-200 bg-slate-50">
                    <div className="text-[10px] uppercase tracking-widest text-slate-400">Pending</div>
                    <div className="mt-2 flex items-baseline justify-between">
                        <div className="text-2xl font-bold text-slate-900">${pendingSummary.total.toFixed(2)}</div>
                        <div className="text-sm font-mono text-slate-600">{pendingSummary.count}</div>
                    </div>
                </div>
                <div className="p-4 rounded-lg border border-emerald-100 bg-emerald-50">
                    <div className="text-[10px] uppercase tracking-widest text-emerald-600">Posted</div>
                    <div className="mt-2 flex items-baseline justify-between">
                        <div className="text-2xl font-bold text-emerald-800">${postedSummary.total.toFixed(2)}</div>
                        <div className="text-sm font-mono text-emerald-700">{postedSummary.count}</div>
                    </div>
                </div>
                <div className="p-4 rounded-lg border border-red-100 bg-red-50">
                    <div className="text-[10px] uppercase tracking-widest text-red-600">Declined</div>
                    <div className="mt-2 flex items-baseline justify-between">
                        <div className="text-2xl font-bold text-red-700">${declinedSummary.total.toFixed(2)}</div>
                        <div className="text-sm font-mono text-red-600">{declinedSummary.count}</div>
                    </div>
                </div>
                <div className="p-4 rounded-lg border border-amber-100 bg-amber-50">
                    <div className="text-[10px] uppercase tracking-widest text-amber-600">Retrying</div>
                    <div className="mt-2 flex items-baseline justify-between">
                        <div className="text-2xl font-bold text-amber-700">${retryingSummary.total.toFixed(2)}</div>
                        <div className="text-sm font-mono text-amber-600">{retryingSummary.count}</div>
                    </div>
                </div>
            </div>

            <div className="overflow-x-auto">
                <table className="w-full text-left text-sm border-separate border-spacing-y-2">
                    <thead>
                        <tr className="text-slate-400 uppercase text-[10px] tracking-widest px-4">
                            <th className="pb-2 pl-4">Date</th>
                            <th className="pb-2">Debtor</th>
                            <th className="pb-2">Amount</th>
                            <th className="pb-2">Status</th>
                            <th className="pb-2 pr-4 text-right">Actions</th>
                        </tr>
                    </thead>
                    <tbody>
                        {loading ? (
                            <tr><td colSpan="5" className="text-center py-10 text-slate-400 font-mono">LOADING DATA STREAM...</td></tr>
                        ) : payments.length === 0 ? (
                            <tr><td colSpan="5" className="text-center py-10 text-slate-400">No payments found for this criteria.</td></tr>
                        ) : payments.map((p) => (
                            <tr key={p.id} className="bg-white border border-slate-100 rounded-lg hover:shadow-md transition-all shadow-sm">
                                <td className="py-4 pl-4 rounded-l-lg border-y border-l border-slate-100">
                                    <div className="font-medium text-slate-900">{new Date(p.due_date).toLocaleDateString()}</div>
                                    <div className="text-[10px] text-slate-400 uppercase">{p.frequency}</div>
                                </td>
                                <td className="py-4 border-y border-slate-100">
                                    <div className="font-medium text-slate-900">{p.first_name} {p.last_name}</div>
                                    <div className="text-xs text-slate-400 font-mono">Ref: {p.client_reference_number}</div>
                                </td>
                                <td className="py-4 border-y border-slate-100">
                                    <div className="text-lg font-bold text-slate-900 font-mono">${Number(p.amount).toFixed(2)}</div>
                                </td>
                                <td className="py-4 border-y border-slate-100">
                                    <span className={`inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-medium border ${p.status === 'paid' ? 'bg-emerald-50 text-emerald-700 border-emerald-100' :
                                            p.status === 'declined' ? 'bg-red-50 text-red-700 border-red-100' :
                                                p.status === 'retrying' ? 'bg-amber-50 text-amber-700 border-amber-100' :
                                                    'bg-slate-50 text-slate-700 border-slate-200'
                                        }`}>
                                        {p.status === 'paid' && <CheckCircle size={12} />}
                                        {p.status === 'declined' && <XCircle size={12} />}
                                        {(p.status === 'pending' || p.status === 'retrying') && <Clock size={12} />}
                                        <span className="capitalize">{p.status === 'paid' ? 'posted' : p.status}</span>
                                    </span>
                                    {p.last_result && (
                                        <div className="text-[10px] text-slate-400 mt-1">{p.last_result}</div>
                                    )}
                                    {p.next_attempt_at && p.status === 'retrying' && (
                                        <div className="text-[10px] text-amber-600 mt-1">Next retry {new Date(p.next_attempt_at).toLocaleString()}</div>
                                    )}
                                </td>
                                <td className="py-4 pr-4 text-right rounded-r-lg border-y border-r border-slate-100">
                                    {p.status === 'declined' && (
                                        <button
                                            onClick={() => handleRerun(p.id)}
                                            className="px-3 py-1.5 bg-blue-600 hover:bg-blue-500 text-white text-[10px] font-bold uppercase rounded-lg shadow-sm active:scale-95 transition-all flex items-center gap-1.5 ml-auto"
                                        >
                                            <RefreshCw size={12} /> Rerun
                                        </button>
                                    )}
                                    {p.status === 'pending' && (
                                        <button
                                            onClick={() => handleRerun(p.id)}
                                            className="px-3 py-1.5 bg-emerald-600 hover:bg-emerald-500 text-white text-[10px] font-bold uppercase rounded-lg shadow-sm active:scale-95 transition-all flex items-center gap-1.5 ml-auto"
                                        >
                                            Run Now
                                        </button>
                                    )}
                                </td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>
        </div>
    );
};

export default PaymentManager;
