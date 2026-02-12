import React from 'react';
import { CreditCard, PlusCircle, CheckCircle, XCircle, Clock, DollarSign, List, Shield, User } from 'lucide-react';
import PaymentPlanBuilder from '../PaymentPlanBuilder';

const TabsPanel = ({
    activeTab,
    setActiveTab,
    currentDebt,
    activePlan,
    isCreatingPlan,
    setIsCreatingPlan,
    planSchedule,
    transactions,
    handlePlanCreated,
    loadPaymentPlan,
    executeScheduledPayment,
    setStatusMsg,
    setActionInProgress,
    loadNextDebt
}) => {

    return (
        <div className="glass-panel rounded-2xl flex-1 flex flex-col overflow-hidden shadow-lg border border-slate-200/60 h-full">
            {/* Tab Navigation */}
            <div className="flex border-b border-slate-100 bg-white/50 backdrop-blur-sm px-2 pt-2">
                {[
                    { id: 'general', label: 'General', icon: User },
                    { id: 'financial', label: 'Financial', icon: CreditCard },
                    { id: 'compliance', label: 'Compliance', icon: Shield }
                ].map(tab => (
                    <button
                        key={tab.id}
                        onClick={() => setActiveTab(tab.id)}
                        className={`flex items-center gap-2 px-6 py-4 text-xs font-bold uppercase tracking-wider transition-all rounded-t-lg mb-[-1px] z-10 relative ${activeTab === tab.id
                            ? 'text-blue-600 border-x border-t border-slate-200 bg-white shadow-sm'
                            : 'text-slate-400 hover:text-slate-600 hover:bg-slate-50/50 border-transparent bg-transparent'
                            }`}
                    >
                        <tab.icon size={14} className={activeTab === tab.id ? 'text-blue-500' : 'text-slate-400'} />
                        {tab.label}
                    </button>
                ))}
            </div>

            <div className="p-6 overflow-y-auto custom-scrollbar bg-white/40 flex-1">
                {activeTab === 'general' && (
                    <div className="grid grid-cols-2 gap-8 animate-in fade-in duration-300">
                        <div className="space-y-6">
                            <div className="group">
                                <label className="text-[10px] text-slate-400 uppercase font-bold tracking-wider mb-1 block group-hover:text-blue-500 transition-colors">Account Number</label>
                                <div className="text-slate-900 font-mono text-base border-b border-slate-100 pb-1">{currentDebt.account}</div>
                            </div>
                            <div className="group">
                                <label className="text-[10px] text-slate-400 uppercase font-bold tracking-wider mb-1 block group-hover:text-blue-500 transition-colors">Client Ref</label>
                                <div className="text-slate-900 font-mono text-base border-b border-slate-100 pb-1">{currentDebt.clientRef}</div>
                            </div>
                            <div className="group">
                                <label className="text-[10px] text-slate-400 uppercase font-bold tracking-wider mb-1 block group-hover:text-blue-500 transition-colors">Current Creditor</label>
                                <div className="text-slate-900 font-medium text-base border-b border-slate-100 pb-1">{currentDebt.creditor}</div>
                            </div>
                        </div>
                        <div className="space-y-6">
                            <div className="group">
                                <label className="text-[10px] text-slate-400 uppercase font-bold tracking-wider mb-1 block group-hover:text-blue-500 transition-colors">Date Opened</label>
                                <div className="text-slate-900 font-mono text-base border-b border-slate-100 pb-1">{currentDebt.opened}</div>
                            </div>
                            <div className="group">
                                <label className="text-[10px] text-slate-400 uppercase font-bold tracking-wider mb-1 block group-hover:text-blue-500 transition-colors">Charge-off Date</label>
                                <div className="text-slate-900 font-mono text-base border-b border-slate-100 pb-1">{currentDebt.chargeOff}</div>
                            </div>
                            <div className="group">
                                <label className="text-[10px] text-slate-400 uppercase font-bold tracking-wider mb-1 block group-hover:text-blue-500 transition-colors">Status</label>
                                <div className="pt-1">
                                    <span className={`px-2 py-1 rounded text-xs font-bold border ${currentDebt.status === 'Active' ? 'bg-blue-50 text-blue-600 border-blue-100' :
                                        currentDebt.status === 'Paid' ? 'bg-emerald-50 text-emerald-600 border-emerald-100' :
                                            'bg-slate-50 text-slate-600 border-slate-100'
                                        }`}>
                                        {currentDebt.status || 'Active'}
                                    </span>
                                </div>
                            </div>
                        </div>
                    </div>
                )}

                {activeTab === 'financial' && (
                    <div className="space-y-8 animate-in fade-in duration-300">
                        {/* Financial Summary Cards */}
                        <div className="grid grid-cols-3 gap-4">
                            <div className="bg-white p-4 rounded-xl border border-slate-100 shadow-sm hover:shadow-md transition-all">
                                <div className="text-[10px] text-slate-400 uppercase font-bold tracking-wider mb-1">Principal</div>
                                <div className="text-xl text-slate-900 font-mono font-bold">${Number(currentDebt.principal || 0).toLocaleString(undefined, { minimumFractionDigits: 2 })}</div>
                            </div>
                            <div className="bg-white p-4 rounded-xl border border-slate-100 shadow-sm hover:shadow-md transition-all">
                                <div className="text-[10px] text-slate-400 uppercase font-bold tracking-wider mb-1">Fees/Costs</div>
                                <div className="text-xl text-slate-900 font-mono font-bold">${Number(currentDebt.fees || 0).toLocaleString(undefined, { minimumFractionDigits: 2 })}</div>
                            </div>
                            <div className="bg-white p-4 rounded-xl border border-slate-100 shadow-sm hover:shadow-md transition-all">
                                <div className="text-[10px] text-slate-400 uppercase font-bold tracking-wider mb-1">Interest</div>
                                <div className="text-xl text-slate-900 font-mono font-bold">$0.00</div>
                            </div>
                        </div>

                        {/* Plan Management Header */}
                        <div className="flex justify-between items-center bg-slate-50/50 p-4 rounded-xl border border-slate-100">
                            <div className="flex items-center gap-4">
                                <div className="p-3 bg-white rounded-full text-blue-600 shadow-sm border border-slate-100">
                                    <CreditCard size={20} />
                                </div>
                                <div>
                                    <div className="text-sm font-bold text-slate-900">Payment Options</div>
                                    <div className="text-xs text-slate-500">Configure settlements and recurring plans</div>
                                </div>
                            </div>
                            {!activePlan && !isCreatingPlan && (
                                <button
                                    onClick={() => setIsCreatingPlan(true)}
                                    className="px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white text-xs font-bold uppercase rounded-lg flex items-center gap-2 transition-all shadow-md active:scale-95"
                                >
                                    <PlusCircle size={14} /> New Plan
                                </button>
                            )}
                            {isCreatingPlan && (
                                <button
                                    onClick={() => setIsCreatingPlan(false)}
                                    className="px-4 py-2 bg-white border border-slate-200 text-slate-600 hover:bg-slate-50 text-xs font-bold uppercase rounded-lg transition-all shadow-sm active:scale-95"
                                >
                                    Cancel
                                </button>
                            )}
                        </div>

                        {isCreatingPlan && (
                            <div className="animate-in slide-in-from-top-4 duration-300">
                                <PaymentPlanBuilder
                                    debtId={currentDebt.id}
                                    totalDue={currentDebt.amountDue}
                                    debtor={currentDebt.rawDebtor}
                                    onPlanCreated={handlePlanCreated}
                                />
                            </div>
                        )}

                        {activePlan && !isCreatingPlan && (
                            <div className="bg-emerald-50/50 border border-emerald-100 rounded-2xl p-6 relative overflow-hidden">
                                <div className="flex justify-between items-start mb-6 relative z-10">
                                    <div>
                                        <div className="flex items-center gap-3">
                                            <div className="text-xs text-emerald-600 uppercase font-bold tracking-widest flex items-center gap-2">
                                                <div className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></div>
                                                Active Settlement Plan
                                            </div>
                                            <div className="px-2 py-0.5 bg-emerald-100 text-emerald-700 text-[10px] font-black rounded uppercase border border-emerald-200 shadow-sm">#PL-{activePlan.id}</div>
                                        </div>
                                        <div className="text-3xl font-bold text-slate-900 font-mono mt-2 tracking-tight">${Number(activePlan.total_settlement_amount).toFixed(2)}</div>
                                    </div>
                                    <div className="text-right">
                                        <div className="text-[10px] text-slate-500 uppercase font-bold tracking-wider mb-1">Frequency</div>
                                        <div className="text-sm text-slate-700 font-bold capitalize bg-white/50 px-3 py-1 rounded-lg border border-emerald-100">{activePlan.frequency}</div>
                                    </div>
                                </div>

                                <div className="space-y-3 max-h-64 overflow-y-auto custom-scrollbar pr-2 relative z-10">
                                    {planSchedule.map((inst, i) => (
                                        <div key={i} className="flex justify-between items-center p-3 bg-white rounded-xl border border-emerald-100/50 shadow-sm hover:shadow-md transition-all">
                                            <div className="flex items-center gap-4">
                                                <div className={`w-3 h-3 rounded-full border-2 border-white shadow-sm ring-1 ring-slate-100 ${inst.status === 'paid' ? 'bg-emerald-500' : inst.status === 'declined' ? 'bg-red-500' : 'bg-slate-300'}`}></div>
                                                <div className="text-sm font-medium text-slate-700">
                                                    {new Date(inst.due_date).toLocaleDateString(undefined, { month: 'short', day: 'numeric', year: 'numeric' })}
                                                </div>
                                            </div>
                                            <div className="flex items-center gap-6">
                                                <div className="text-sm font-mono font-bold text-slate-900">${Number(inst.amount).toFixed(2)}</div>
                                                <div className="flex items-center gap-2 min-w-[80px]">
                                                    {inst.status === 'paid' && <CheckCircle size={14} className="text-emerald-500" />}
                                                    {inst.status === 'declined' && <XCircle size={14} className="text-red-500" />}
                                                    {(inst.status === 'pending' || inst.status === 'retrying') && <Clock size={14} className={inst.status === 'retrying' ? 'text-amber-500' : 'text-slate-400'} />}
                                                    <div className={`text-[10px] font-bold uppercase ${inst.status === 'paid' ? 'text-emerald-600' : inst.status === 'declined' ? 'text-red-600' : inst.status === 'retrying' ? 'text-amber-600' : 'text-slate-400'}`}>
                                                        {inst.status}
                                                    </div>
                                                </div>
                                                {inst.status === 'pending' && (
                                                    <button
                                                        onClick={async () => {
                                                            if (!window.confirm("Run this payment now?")) return;
                                                            setActionInProgress('pay');
                                                            try {
                                                                await executeScheduledPayment(inst.id);
                                                                setStatusMsg({ type: 'success', text: "Payment Processed Early!" });
                                                                loadPaymentPlan(currentDebt.id);
                                                            } catch (e) {
                                                                setStatusMsg({ type: 'error', text: e.message });
                                                            } finally {
                                                                setActionInProgress(null);
                                                            }
                                                        }}
                                                        className="p-1.5 text-blue-600 hover:bg-blue-50 rounded-lg transition-all border border-transparent hover:border-blue-100"
                                                        title="Pay Early"
                                                    >
                                                        <DollarSign size={16} />
                                                    </button>
                                                )}
                                            </div>
                                        </div>
                                    ))}
                                </div>

                                {/* Decorative BG */}
                                <div className="absolute top-0 right-0 w-64 h-64 bg-emerald-100/30 rounded-full blur-3xl -translate-y-1/2 translate-x-1/2 pointer-events-none"></div>
                            </div>
                        )}

                        <div>
                            <h4 className="text-xs font-bold text-slate-400 uppercase tracking-widest mb-4 flex items-center gap-2">
                                <List size={14} /> Transaction History
                            </h4>
                            <div className="bg-white rounded-xl border border-slate-200 overflow-hidden shadow-sm">
                                <table className="w-full text-xs text-left text-slate-500">
                                    <thead className="bg-slate-50 text-slate-700 font-bold uppercase border-b border-slate-200">
                                        <tr>
                                            <th className="p-3">Date</th>
                                            <th className="p-3 text-right">Amount</th>
                                            <th className="p-3 text-center">Status</th>
                                        </tr>
                                    </thead>
                                    <tbody className="divide-y divide-slate-100">
                                        {transactions.length > 0 ? transactions.map(tx => (
                                            <tr key={tx.id} className="hover:bg-slate-50 transition-colors">
                                                <td className="p-3 font-mono">{new Date(tx.timestamp).toLocaleDateString()}</td>
                                                <td className="p-3 text-right font-bold text-slate-900 font-mono">${Number(tx.amount_paid).toFixed(2)}</td>
                                                <td className="p-3 text-center">
                                                    <span className="px-2 py-0.5 bg-emerald-50 text-emerald-600 rounded-full font-bold uppercase text-[9px] border border-emerald-100 shadow-sm">Processed</span>
                                                </td>
                                            </tr>
                                        )) : (
                                            <tr>
                                                <td colSpan="3" className="p-6 text-center text-slate-400 italic">No transactions found</td>
                                            </tr>
                                        )}
                                    </tbody>
                                </table>
                            </div>
                        </div>
                    </div>
                )}

                {activeTab === 'compliance' && (
                    <div className="space-y-4 animate-in fade-in duration-300">
                        <div className="flex items-center justify-between p-4 bg-white rounded-xl border border-slate-100 shadow-sm">
                            <span className="text-sm font-medium text-slate-700">Mini-Miranda Read?</span>
                            <span className="text-xs font-bold bg-red-50 text-red-600 px-3 py-1 rounded-lg border border-red-100">NO</span>
                        </div>
                        <div className="flex items-center justify-between p-4 bg-white rounded-xl border border-slate-100 shadow-sm">
                            <span className="text-sm font-medium text-slate-700">Right to Dispute?</span>
                            <span className="text-xs font-bold bg-slate-100 text-slate-600 px-3 py-1 rounded-lg border border-slate-200">PENDING</span>
                        </div>
                        <div className="p-4 bg-blue-50 border border-blue-100 rounded-xl text-xs text-blue-700 leading-relaxed">
                            <strong>Note:</strong> Ensure you read the Mini-Miranda at the beginning of every call. Failure to do so may result in compliance violations.
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
};

export default TabsPanel;
