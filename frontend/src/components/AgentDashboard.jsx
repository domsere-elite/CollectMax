import React, { useState, useEffect } from 'react';
import { fetchWorkQueue, logInteraction, processPayment, searchDebts, fetchPaymentPlans, fetchPlanSchedule, executeScheduledPayment, fetchDebtPayments } from '../services/api';
import { Phone, Mail, CreditCard, AlertTriangle, CheckCircle, XCircle, Clock, Calendar, FileText, DollarSign, User, Shield, Briefcase, Activity, ChevronDown, Search, PlusCircle, List } from 'lucide-react';
import PaymentPlanBuilder from './PaymentPlanBuilder';

const AgentDashboard = () => {
    const [currentDebt, setCurrentDebt] = useState(null);
    const [loading, setLoading] = useState(true);
    const [statusMsg, setStatusMsg] = useState(null);
    const [activeTab, setActiveTab] = useState('general'); // general, financial, compliance

    // Compliance & Action State
    const [isTimezoneValid, setTimezoneValid] = useState(true);
    const [is7in7Warning, set7in7Warning] = useState(false);
    const [actionInProgress, setActionInProgress] = useState(null);

    // Search State
    const [searchType, setSearchType] = useState('name'); // 'name' or 'client_ref'
    const [searchQuery, setSearchQuery] = useState('');
    const [searchResults, setSearchResults] = useState(null);

    // Payment Plan State
    const [activePlan, setActivePlan] = useState(null);
    const [planSchedule, setPlanSchedule] = useState([]);
    const [isCreatingPlan, setIsCreatingPlan] = useState(false);
    const [transactions, setTransactions] = useState([]);

    useEffect(() => {
        // Don't auto-load - search-first workflow  
        setLoading(false);
    }, []);

    const loadNextDebt = async () => {
        try {
            setLoading(true);
            const queue = await fetchWorkQueue();
            if (queue && queue.length > 0) {
                const debt = queue[0];
                setCurrentDebt({
                    // ... (mapping)
                    id: debt.id,
                    debtorName: `${debt.debtor.first_name} ${debt.debtor.last_name}`,
                    email: debt.debtor.email,
                    phone: debt.debtor.phone,
                    dob: debt.debtor.dob || 'N/A',
                    address: `${debt.debtor.address_1} ${debt.debtor.address_2 || ''}`,
                    cityStateZip: `${debt.debtor.city}, ${debt.debtor.state} ${debt.debtor.zip_code}`,
                    zipCode: debt.debtor.zip_code,
                    account: debt.original_account_number,
                    clientRef: debt.client_reference_number || 'N/A',
                    creditor: debt.original_creditor || 'Unknown Creditor',
                    opened: debt.date_opened || 'N/A',
                    chargeOff: debt.charge_off_date || 'N/A',
                    amountDue: debt.amount_due,
                    principal: debt.principal_balance,
                    fees: debt.fees_costs,
                    last_payment_date: debt.last_payment_date || 'Never',
                    lastPayAmount: debt.last_payment_amount,
                    totalPaid: debt.total_paid_amount || 0,
                    status: debt.status,
                    rawDebtor: debt.debtor,
                    ssnHash: debt.debtor.ssn_hash ? `***-**-${debt.debtor.ssn_hash.substring(0, 4)}` : 'N/A'
                });
                loadPaymentPlan(debt.id);
            } else {
                setCurrentDebt(null);
                setActivePlan(null);
            }
        } catch (e) {
            console.error(e);
            setStatusMsg({ type: 'error', text: "Failed to load work queue" });
        } finally {
            setLoading(false);
        }
    };

    const handleCall = async () => {
        if (!isTimezoneValid) return;
        setActionInProgress('call');
        try {
            const result = await logInteraction(currentDebt.id, "Call", "Agent initiated call");
            let msg = "Call Logged";
            if (result.warning_flag === "WARNING") {
                set7in7Warning(true);
                msg += " (7-in-7 Warning)";
            }
            setStatusMsg({ type: 'success', text: msg });
        } catch (e) {
            setStatusMsg({ type: 'error', text: e.message });
            if (e.message.includes("Do Not Call")) setTimezoneValid(false);
        } finally {
            setActionInProgress(null);
        }
    };

    const handlePayment = async () => {
        setActionInProgress('pay');
        try {
            let result;
            if (activePlan) {
                // If there's an active plan, use one-off payment (use token)
                result = await runOneOffPayment(currentDebt.id, currentDebt.amountDue);
            } else {
                // Legacy / Direct payment
                result = await processPayment(currentDebt.id, currentDebt.amountDue);
            }
            setStatusMsg({ type: 'success', text: `Paid $${result.amount || result.amount_paid}` });
            // Reload debt to get updated balance
            loadNextDebt();
        } catch (e) {
            setStatusMsg({ type: 'error', text: e.message || "Payment Failed" });
        } finally {
            setActionInProgress(null);
        }
    };

    const loadPaymentPlan = async (debtId) => {
        try {
            const plans = await fetchPaymentPlans(debtId);
            if (plans && plans.length > 0) {
                setActivePlan(plans[0]);
                const schedule = await fetchPlanSchedule(plans[0].id);
                setPlanSchedule(schedule);
                setIsCreatingPlan(false);
            } else {
                setActivePlan(null);
                setPlanSchedule([]);
            }
            // Also fetch transaction history
            const history = await fetchDebtPayments(debtId);
            setTransactions(history);
        } catch (e) {
            console.error("Plan load failed", e);
        }
    };

    const handlePlanCreated = (plan) => {
        setStatusMsg({ type: 'success', text: "Payment Plan Activated!" });
        loadPaymentPlan(currentDebt.id);
    };

    const handleSearch = async (query) => {
        if (!query || query.trim().length < 2) {
            setSearchResults(null);
            return;
        }
        try {
            const results = await searchDebts(searchType, query);
            if (results && results.length > 0) {
                setSearchResults(results);
                setStatusMsg({ type: 'success', text: `Found ${results.length} result(s)` });
            } else {
                setSearchResults(null);
                setStatusMsg({ type: 'info', text: 'No results found' });
            }
        } catch (e) {
            setSearchResults(null);
            setStatusMsg({ type: 'error', text: 'Search failed' });
        }
    };

    if (loading) return <div className="flex justify-center items-center h-screen text-blue-400 font-mono">LOADING DATA STREAM...</div>;

    return (
        <div className="min-h-screen bg-white text-slate-700 font-sans p-2">

            {/* SEARCH BAR */}
            <div className="glass-panel p-3 rounded-xl mb-2 flex items-center gap-2">
                <Search size={18} className="text-slate-400" />
                <select
                    value={searchType}
                    onChange={(e) => setSearchType(e.target.value)}
                    className="bg-white border border-slate-200 rounded px-3 py-2 text-sm text-slate-700 focus:outline-none focus:border-blue-500/50"
                >
                    <option value="name">Name</option>
                    <option value="client_ref">Client Ref</option>
                </select>
                <input
                    type="text"
                    value={searchQuery}
                    onChange={(e) => {
                        setSearchQuery(e.target.value);
                        handleSearch(e.target.value);
                    }}
                    placeholder={searchType === 'name' ? 'Type to search by name...' : 'Type to search by client ref...'}
                    className="flex-1 bg-white border border-slate-200 rounded px-4 py-2 text-sm text-slate-700 focus:outline-none focus:border-blue-500/50"
                />
            </div>

            {/* SEARCH RESULTS DROPDOWN */}
            {searchResults && searchResults.length > 0 && (
                <div className="glass-panel p-3 rounded-xl mb-2">
                    <div className="text-xs text-slate-400 uppercase tracking-wider mb-2">
                        {searchResults.length} Results Found - Click to Load
                    </div>
                    <div className="space-y-1 max-h-64 overflow-y-auto custom-scrollbar">
                        {searchResults.map((result, idx) => (
                            <button
                                key={idx}
                                onClick={() => {
                                    const debt = result;
                                    setCurrentDebt({
                                        id: debt.id,
                                        debtorName: `${debt.debtor.first_name} ${debt.debtor.last_name}`,
                                        email: debt.debtor.email,
                                        phone: debt.debtor.phone,
                                        dob: debt.debtor.dob || 'N/A',
                                        address: `${debt.debtor.address_1} ${debt.debtor.address_2 || ''}`,
                                        cityStateZip: `${debt.debtor.city}, ${debt.debtor.state} ${debt.debtor.zip_code}`,
                                        zipCode: debt.debtor.zip_code,
                                        account: debt.original_account_number,
                                        clientRef: debt.client_reference_number || 'N/A',
                                        creditor: debt.original_creditor || 'Unknown Creditor',
                                        opened: debt.date_opened || 'N/A',
                                        chargeOff: debt.charge_off_date || 'N/A',
                                        amountDue: debt.amount_due,
                                        principal: debt.principal_balance,
                                        fees: debt.fees_costs,
                                        lastPayDate: debt.last_payment_date || 'Never',
                                        lastPayAmount: debt.last_payment_amount,
                                        totalPaid: debt.total_paid_amount || 0,
                                        status: debt.status,
                                        rawDebtor: debt.debtor,
                                        ssnHash: debt.debtor.ssn_hash ? `***-**-${debt.debtor.ssn_hash.substring(0, 4)}` : 'N/A'
                                    });
                                    loadPaymentPlan(debt.id);
                                    setSearchResults(null); // Close dropdown after selection
                                }}
                                className="w-full text-left p-3 bg-white hover:bg-slate-50 rounded border border-slate-100 transition-all flex justify-between items-center group"
                            >
                                <div className="flex-1">
                                    <div className="text-sm font-medium text-slate-900 group-hover:text-blue-600 transition-colors">
                                        {result.debtor.first_name} {result.debtor.last_name}
                                    </div>
                                    <div className="text-xs text-slate-400 font-mono mt-0.5">
                                        Ref: {result.client_reference_number || 'N/A'}
                                    </div>
                                </div>
                                <div className="text-right">
                                    <div className="text-sm font-bold text-red-600 font-mono">
                                        ${Number(result.amount_due || 0).toLocaleString()}
                                    </div>
                                    <div className="text-xs text-slate-500">
                                        {result.status}
                                    </div>
                                </div>
                            </button>
                        ))}
                    </div>
                    <button
                        onClick={() => setSearchResults(null)}
                        className="mt-2 text-xs text-slate-500 hover:text-slate-700 transition-colors"
                    >
                        Close Results
                    </button>
                </div>
            )}

            {/* TOP HEADER BAR */}
            {!currentDebt && (
                <div className="p-20 text-center">
                    <Search size={48} className="mx-auto text-gray-700 mb-4" />
                    <div className="text-gray-500 font-mono text-lg">Search for an account to begin</div>
                    <div className="text-gray-600 text-sm mt-2">Type a name or client reference above</div>
                </div>
            )}
            {currentDebt && (
                <>
                    {/* TOP HEADER BAR */}
                    <div className="glass-panel border-b border-slate-100 p-4 rounded-xl mb-2 flex justify-between items-center">
                        <div className="flex items-center gap-4">
                            <div className="w-10 h-10 rounded-full bg-gradient-to-br from-blue-500 to-indigo-600 flex items-center justify-center text-white font-bold text-lg">
                                {currentDebt.debtorName.charAt(0)}
                            </div>
                            <div>
                                <h1 className="text-xl font-bold text-slate-900 leading-tight flex items-center gap-2">
                                    {currentDebt.debtorName}
                                    <span className="text-[10px] bg-blue-50 text-blue-600 px-1.5 py-0.5 rounded border border-blue-100 uppercase tracking-wider">Primary</span>
                                    {activePlan && (
                                        <span className="text-[10px] bg-emerald-50 text-emerald-600 px-1.5 py-0.5 rounded border border-emerald-100 uppercase tracking-wider">Plan Active</span>
                                    )}
                                </h1>
                                <div className="text-xs text-slate-400 font-mono flex gap-3 mt-0.5">
                                    <span>ID: {currentDebt.id}</span>
                                    <span>•</span>
                                    <span>SSN: {currentDebt.ssnHash}</span>
                                </div>
                            </div>
                        </div>

                        <div className="flex gap-6 text-right">
                            <div className="text-xs">
                                <div className="text-slate-400 uppercase tracking-widest text-[10px]">Total Paid</div>
                                <div className="text-xl font-bold text-emerald-600 font-mono">${currentDebt.totalPaid.toLocaleString(undefined, { minimumFractionDigits: 2 })}</div>
                            </div>
                            <div className="text-xs">
                                <div className="text-slate-400 uppercase tracking-widest text-[10px]">Current Balance</div>
                                <div className="text-xl font-bold text-red-600 font-mono">${currentDebt.amountDue.toLocaleString(undefined, { minimumFractionDigits: 2 })}</div>
                            </div>
                            <div className="text-xs">
                                <div className="text-slate-400 uppercase tracking-widest text-[10px]">Local Time</div>
                                <div className={`text-lg font-bold font-mono flex items-center gap-1 ${!isTimezoneValid ? 'text-red-600' : 'text-emerald-600'}`}>
                                    {!isTimezoneValid ? <XCircle size={14} /> : <Clock size={14} />}
                                    04:32 PM (EST)
                                </div>
                            </div>
                        </div>
                    </div>

                    {/* MAIN 3-COLUMN GRID */}
                    <div className="grid grid-cols-12 gap-2 h-[calc(100vh-140px)]">

                        {/* COL 1: LEFT SIDEBAR */}
                        <div className="col-span-3 flex flex-col gap-2">
                            <div className="glass-panel p-4 rounded-xl flex-1 flex flex-col gap-4">
                                <h3 className="text-xs font-bold text-slate-400 uppercase tracking-widest mb-2 flex items-center gap-2">
                                    <User size={12} /> Contact Details
                                </h3>

                                <div className="space-y-4">
                                    <div className="group p-2 rounded hover:bg-white border border-transparent hover:border-slate-100 transition-colors">
                                        <label className="text-[10px] text-slate-400 uppercase">Primary Phone</label>
                                        <div className="flex justify-between items-center">
                                            <div className="font-mono text-slate-900 text-sm">{currentDebt.phone}</div>
                                            <button onClick={handleCall} disabled={!isTimezoneValid} className="p-1.5 bg-emerald-50 text-emerald-600 rounded hover:bg-emerald-600 hover:text-white transition-all disabled:opacity-50 disabled:cursor-not-allowed">
                                                <Phone size={14} />
                                            </button>
                                        </div>
                                    </div>

                                    <div className="group p-2 rounded hover:bg-white border border-transparent hover:border-slate-100 transition-colors">
                                        <label className="text-[10px] text-slate-400 uppercase">Email Address</label>
                                        <div className="flex justify-between items-center">
                                            <div className="font-mono text-slate-900 text-sm truncate w-32">{currentDebt.email}</div>
                                            <button className="p-1.5 bg-blue-50 text-blue-600 rounded hover:bg-blue-600 hover:text-white transition-all">
                                                <Mail size={14} />
                                            </button>
                                        </div>
                                    </div>

                                    <div className="group p-2 rounded hover:bg-white border border-transparent hover:border-slate-100 transition-colors">
                                        <label className="text-[10px] text-slate-400 uppercase">Mailing Address</label>
                                        <div className="text-sm text-slate-700 mt-0.5">
                                            {currentDebt.address}<br />
                                            {currentDebt.cityStateZip}
                                        </div>
                                    </div>
                                </div>

                                <div className="mt-auto border-t border-slate-100 pt-4">
                                    {is7in7Warning && (
                                        <div className="bg-amber-50 border border-amber-200 p-2 rounded text-xs text-amber-700 flex items-center gap-2 mb-2">
                                            <AlertTriangle size={12} /> Exceeds 7-in-7 Limit
                                        </div>
                                    )}
                                    {!isTimezoneValid ? (
                                        <div className="bg-red-50 border border-red-200 p-2 rounded text-xs text-red-700 flex items-center gap-2">
                                            <XCircle size={12} /> Outside Calling Hours
                                        </div>
                                    ) : (
                                        <div className="bg-emerald-50 border border-emerald-200 p-2 rounded text-xs text-emerald-700 flex items-center gap-2">
                                            <CheckCircle size={12} /> Compliant to Call
                                        </div>
                                    )}
                                </div>
                            </div>
                        </div>

                        {/* COL 2: CENTER */}
                        <div className="col-span-6 flex flex-col gap-2">
                            <div className="glass-panel rounded-xl flex-1 flex flex-col overflow-hidden">
                                <div className="flex border-b border-slate-100 bg-white">
                                    {['general', 'financial', 'compliance'].map(tab => (
                                        <button
                                            key={tab}
                                            onClick={() => setActiveTab(tab)}
                                            className={`px-6 py-3 text-xs font-bold uppercase tracking-wider transition-all ${activeTab === tab
                                                ? 'text-blue-600 border-b-2 border-blue-600 bg-white'
                                                : 'text-slate-400 hover:text-slate-600 hover:bg-white/5'
                                                }`}
                                        >
                                            {tab} Details
                                        </button>
                                    ))}
                                </div>

                                <div className="p-4 overflow-y-auto custom-scrollbar">
                                    {activeTab === 'general' && (
                                        <div className="grid grid-cols-2 gap-4">
                                            <div className="space-y-4">
                                                <div><label className="text-[10px] text-slate-400 uppercase">Account Number</label><div className="text-sm text-slate-900 font-mono">{currentDebt.account}</div></div>
                                                <div><label className="text-[10px] text-slate-400 uppercase">Client Ref</label><div className="text-sm text-slate-900 font-mono">{currentDebt.clientRef}</div></div>
                                                <div><label className="text-[10px] text-slate-400 uppercase">Creditor</label><div className="text-sm text-slate-900 font-medium">{currentDebt.creditor}</div></div>
                                            </div>
                                            <div className="space-y-4">
                                                <div><label className="text-[10px] text-slate-400 uppercase">Date Opened</label><div className="text-sm text-slate-900 font-mono">{currentDebt.opened}</div></div>
                                                <div><label className="text-[10px] text-slate-400 uppercase">Charge-off Date</label><div className="text-sm text-slate-900 font-mono">{currentDebt.chargeOff}</div></div>
                                                <div><label className="text-[10px] text-slate-400 uppercase">Status</label><div className="text-sm text-slate-900"><span className="bg-blue-50 text-blue-600 px-2 py-0.5 rounded text-xs border border-blue-100">Active</span></div></div>
                                            </div>
                                        </div>
                                    )}

                                    {activeTab === 'financial' && (
                                        <div className="space-y-6">
                                            {/* Plan Management Header */}
                                            <div className="flex justify-between items-center bg-white p-3 rounded-lg border border-slate-100">
                                                <div className="flex items-center gap-3">
                                                    <div className="p-2 bg-blue-50 rounded text-blue-600">
                                                        <CreditCard size={18} />
                                                    </div>
                                                    <div>
                                                        <div className="text-xs font-bold text-slate-900">Payment Options</div>
                                                        <div className="text-[10px] text-slate-500">Configure settlements and recurring plans</div>
                                                    </div>
                                                </div>
                                                {!activePlan && !isCreatingPlan && (
                                                    <button
                                                        onClick={() => setIsCreatingPlan(true)}
                                                        className="px-3 py-1.5 bg-blue-600 hover:bg-blue-500 text-white text-[10px] font-bold uppercase rounded flex items-center gap-2 transition-all"
                                                    >
                                                        <PlusCircle size={14} /> New Plan
                                                    </button>
                                                )}
                                                {isCreatingPlan && (
                                                    <button
                                                        onClick={() => setIsCreatingPlan(false)}
                                                        className="px-3 py-1.5 bg-slate-200 hover:bg-slate-300 text-slate-700 text-[10px] font-bold uppercase rounded transition-all"
                                                    >
                                                        Cancel
                                                    </button>
                                                )}
                                            </div>

                                            {isCreatingPlan && (
                                                <PaymentPlanBuilder
                                                    debtId={currentDebt.id}
                                                    totalDue={currentDebt.amountDue}
                                                    debtor={currentDebt.rawDebtor}
                                                    onPlanCreated={handlePlanCreated}
                                                />
                                            )}

                                            {activePlan && !isCreatingPlan && (
                                                <div className="bg-emerald-50 border border-emerald-100 rounded-xl p-4">
                                                    <div className="flex justify-between items-start mb-4">
                                                        <div>
                                                            <div className="flex items-center gap-2">
                                                                <div className="text-[10px] text-emerald-600 uppercase font-bold tracking-widest">Active Settlement Plan</div>
                                                                <div className="px-1.5 py-0.5 bg-emerald-100 text-emerald-700 text-[8px] font-black rounded uppercase border border-emerald-200">#PL-{activePlan.id}</div>
                                                            </div>
                                                            <div className="text-xl font-bold text-slate-900 font-mono mt-1">${Number(activePlan.total_settlement_amount).toFixed(2)}</div>
                                                        </div>
                                                        <div className="text-right">
                                                            <div className="text-[10px] text-slate-500 uppercase">Frequency</div>
                                                            <div className="text-xs text-slate-700 font-bold capitalize">{activePlan.frequency}</div>
                                                        </div>
                                                    </div>

                                                    <div className="space-y-2 max-h-48 overflow-y-auto custom-scrollbar pr-2">
                                                        {planSchedule.map((inst, i) => (
                                                            <div key={i} className="flex justify-between items-center p-2.5 bg-white rounded border border-slate-100">
                                                                <div className="flex items-center gap-3">
                                                                    <div className={`w-2 h-2 rounded-full ${inst.status === 'paid' ? 'bg-emerald-500' : inst.status === 'declined' ? 'bg-red-500' : 'bg-slate-300'}`}></div>
                                                                    <div className="text-xs text-slate-600">
                                                                        {new Date(inst.due_date).toLocaleDateString()}
                                                                    </div>
                                                                </div>
                                                                <div className="flex items-center gap-4">
                                                                    <div className="text-sm font-mono text-slate-900">${Number(inst.amount).toFixed(2)}</div>
                                                                    <div className="flex items-center gap-1.5">
                                                                        {inst.status === 'paid' && <CheckCircle size={10} className="text-emerald-500" />}
                                                                        {inst.status === 'declined' && <XCircle size={10} className="text-red-500" />}
                                                                        {inst.status === 'pending' && <Clock size={10} className="text-slate-400" />}
                                                                        <div className={`text-[10px] font-bold uppercase ${inst.status === 'paid' ? 'text-emerald-600' : inst.status === 'declined' ? 'text-red-600' : 'text-slate-400'}`}>
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
                                                                            className="p-1 text-blue-600 hover:bg-blue-50 rounded transition-all"
                                                                            title="Pay Early"
                                                                        >
                                                                            <DollarSign size={14} />
                                                                        </button>
                                                                    )}
                                                                </div>
                                                            </div>
                                                        ))}
                                                    </div>
                                                </div>
                                            )}

                                            <div className="grid grid-cols-3 gap-4">
                                                <div className="bg-white p-3 rounded border border-slate-100">
                                                    <div className="text-[10px] text-slate-500 uppercase">Principal</div>
                                                    <div className="text-lg text-slate-900 font-mono">${Number(currentDebt.principal || 0).toLocaleString(undefined, { minimumFractionDigits: 2 })}</div>
                                                </div>
                                                <div className="bg-white p-3 rounded border border-slate-100">
                                                    <div className="text-[10px] text-slate-500 uppercase">Fees/Costs</div>
                                                    <div className="text-lg text-slate-900 font-mono">${Number(currentDebt.fees || 0).toLocaleString(undefined, { minimumFractionDigits: 2 })}</div>
                                                </div>
                                                <div className="bg-white p-3 rounded border border-slate-100">
                                                    <div className="text-[10px] text-slate-500 uppercase">Interest</div>
                                                    <div className="text-lg text-slate-900 font-mono">$0.00</div>
                                                </div>
                                            </div>

                                            <div>
                                                <h4 className="text-xs font-bold text-slate-400 uppercase mb-2 flex items-center gap-2">
                                                    <List size={14} /> Transaction History
                                                </h4>
                                                <div className="bg-white rounded border border-slate-100 overflow-hidden">
                                                    <table className="w-full text-[10px] text-left text-slate-500">
                                                        <thead className="bg-slate-50 text-slate-700 font-bold uppercase">
                                                            <tr>
                                                                <th className="p-2">Date</th>
                                                                <th className="p-2 text-right">Amount</th>
                                                                <th className="p-2 text-center">Status</th>
                                                            </tr>
                                                        </thead>
                                                        <tbody className="divide-y divide-slate-100">
                                                            {transactions.length > 0 ? transactions.map(tx => (
                                                                <tr key={tx.id} className="hover:bg-slate-50 transition-colors">
                                                                    <td className="p-2 font-mono">{new Date(tx.timestamp).toLocaleDateString()}</td>
                                                                    <td className="p-2 text-right font-bold text-slate-900">${Number(tx.amount_paid).toFixed(2)}</td>
                                                                    <td className="p-2 text-center">
                                                                        <span className="px-1.5 py-0.5 bg-emerald-50 text-emerald-600 rounded-full font-bold uppercase text-[8px] border border-emerald-100">Processed</span>
                                                                    </td>
                                                                </tr>
                                                            )) : (
                                                                <tr>
                                                                    <td colSpan="3" className="p-4 text-center text-slate-400 italic">No transactions found</td>
                                                                </tr>
                                                            )}
                                                        </tbody>
                                                    </table>
                                                </div>
                                            </div>
                                        </div>
                                    )}

                                    {activeTab === 'compliance' && (
                                        <div className="space-y-3">
                                            <div className="flex items-center justify-between p-3 bg-white rounded border border-slate-100">
                                                <span className="text-sm text-slate-700">Mini-Miranda Read?</span>
                                                <span className="text-xs bg-red-50 text-red-600 px-2 py-0.5 rounded border border-red-100">NO</span>
                                            </div>
                                            <div className="flex items-center justify-between p-3 bg-white rounded border border-slate-100">
                                                <span className="text-sm text-slate-700">Right to Dispute?</span>
                                                <span className="text-xs bg-slate-100 text-slate-600 px-2 py-0.5 rounded border border-slate-200">PENDING</span>
                                            </div>
                                        </div>
                                    )}
                                </div>
                            </div>

                            <div className="glass-panel p-4 rounded-xl h-48 overflow-y-auto">
                                <h3 className="text-xs font-bold text-slate-400 uppercase tracking-widest mb-3 sticky top-0 bg-white/80 backdrop-blur-md py-1 z-10 flex justify-between">
                                    <span>Activity Timeline</span>
                                    <span className="text-[10px] bg-slate-100 px-1 rounded cursor-pointer">View All</span>
                                </h3>
                                {statusMsg && (
                                    <div className="text-xs p-2 mb-2 rounded bg-white border border-slate-100 flex items-center gap-2">
                                        <span className={statusMsg.type === 'success' ? 'text-emerald-500' : 'text-red-500'}>●</span>
                                        {statusMsg.text}
                                    </div>
                                )}
                                <div className="space-y-3 border-l border-slate-200 ml-1 pl-3">
                                    <div className="relative">
                                        <span className="absolute -left-[17px] top-1 w-2 h-2 rounded-full bg-blue-500 shadow-[0_0_10px_rgba(59,130,246,0.3)]"></span>
                                        <div className="text-xs text-slate-400 font-mono">Today, 09:30 AM</div>
                                        <div className="text-xs text-slate-700 mt-0.5">System: Account loaded.</div>
                                    </div>
                                </div>
                            </div>
                        </div>

                        {/* COL 3: ACTIONS & NOTES */}
                        <div className="col-span-3 flex flex-col gap-2">
                            <div className="glass-panel p-4 rounded-xl">
                                <h3 className="text-xs font-bold text-slate-400 uppercase tracking-widest mb-4">Quick Actions</h3>
                                <div className="grid grid-cols-2 gap-2 mb-4">
                                    <button className="flex flex-col items-center justify-center p-3 bg-white hover:bg-slate-100 rounded border border-slate-100 transition-all group">
                                        <Mail size={16} className="text-blue-500 mb-1 group-hover:scale-110 transition-transform" />
                                        <span className="text-[10px] uppercase font-bold text-slate-600">Email</span>
                                    </button>
                                    <button className="flex flex-col items-center justify-center p-3 bg-white hover:bg-slate-100 rounded border border-slate-100 transition-all group">
                                        <Shield size={16} className="text-purple-500 mb-1 group-hover:scale-110 transition-transform" />
                                        <span className="text-[10px] uppercase font-bold text-slate-600">Dispute</span>
                                    </button>
                                </div>
                                <button
                                    onClick={() => {
                                        setActiveTab('financial');
                                        setIsCreatingPlan(true);
                                    }}
                                    className="w-full py-3 bg-blue-50 hover:bg-blue-100 text-blue-600 font-bold rounded border border-blue-200 active:scale-95 transition-all flex items-center justify-center gap-2 mb-2"
                                >
                                    <PlusCircle size={16} />
                                    <span>Set Up Payment Plan</span>
                                </button>
                                <button
                                    onClick={handlePayment}
                                    disabled={actionInProgress}
                                    className="w-full py-3 bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-500 hover:to-teal-500 text-white font-bold rounded shadow-lg shadow-emerald-900/20 active:scale-95 transition-all flex items-center justify-center gap-2"
                                >
                                    <CreditCard size={16} />
                                    <span>Quick Pay Full</span>
                                </button>
                            </div>

                            <div className="glass-panel p-4 rounded-xl flex-1 flex flex-col">
                                <h3 className="text-xs font-bold text-slate-400 uppercase tracking-widest mb-2">Agent Notes</h3>
                                <textarea
                                    className="bg-white border border-slate-100 rounded p-3 h-full w-full text-xs text-slate-700 focus:outline-none focus:border-blue-500/50 resize-none"
                                    placeholder="Type session notes here..."
                                ></textarea>
                            </div>
                        </div>
                    </div>
                </>
            )}
        </div >
    );
};

export default AgentDashboard;
