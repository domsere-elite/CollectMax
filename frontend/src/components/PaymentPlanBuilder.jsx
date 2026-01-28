import React, { useState, useEffect } from 'react';
import { Calendar, DollarSign, Clock, CheckCircle, AlertCircle, ChevronRight, CreditCard } from 'lucide-react';

const PaymentPlanBuilder = ({ debtId, totalDue, debtor, onPlanCreated }) => {
    const [settlementAmount, setSettlementAmount] = useState(totalDue);
    const [settlementPercentage, setSettlementPercentage] = useState(100);
    const [downPayment, setDownPayment] = useState(0);
    const [installments, setInstallments] = useState(12);
    const [frequency, setFrequency] = useState('monthly');
    const [startDate, setStartDate] = useState(new Date().toISOString().split('T')[0]);
    const [isSettlement, setIsSettlement] = useState(false);

    // Effect to reset settlement fields when toggle changes
    useEffect(() => {
        if (!isSettlement) {
            setSettlementAmount(totalDue);
            setSettlementPercentage(100);
        }
    }, [isSettlement, totalDue]);

    // Card Info State
    const [cardNumber, setCardNumber] = useState('');
    const [expiry, setExpiry] = useState('');
    const [cvv, setCvv] = useState('');
    const [cardholderName, setCardholderName] = useState(debtor ? `${debtor.first_name} ${debtor.last_name}` : '');

    // Billing Address State - Auto-populate from debtor
    const [billingAddress, setBillingAddress] = useState(debtor?.address_1 || '');
    const [billingCity, setBillingCity] = useState(debtor?.city || '');
    const [billingState, setBillingState] = useState(debtor?.state || '');
    const [billingZip, setBillingZip] = useState(debtor?.zip_code || '');

    // Sync state when debtor prop changes (account switching)
    useEffect(() => {
        if (debtor) {
            setCardholderName(`${debtor.first_name} ${debtor.last_name}`);
            setBillingAddress(debtor.address_1 || '');
            setBillingCity(debtor.city || '');
            setBillingState(debtor.state || '');
            setBillingZip(debtor.zip_code || '');
            // Clear sensitive fields for new account
            setCardNumber('');
            setExpiry('');
            setCvv('');
            setError(null);
        }
    }, [debtor]);

    const [preview, setPreview] = useState([]);
    const [loading, setLoading] = useState(false);
    const [saving, setSaving] = useState(false);
    const [error, setError] = useState(null);

    // Calculate settlement amount based on percentage
    const handlePercentageChange = (pct) => {
        setSettlementPercentage(pct);
        const amt = (totalDue * (pct / 100)).toFixed(2);
        setSettlementAmount(amt);
    };

    // Calculate percentage based on amount
    const handleAmountChange = (amt) => {
        setSettlementAmount(amt);
        const pct = ((amt / totalDue) * 100).toFixed(1);
        setSettlementPercentage(pct);
    };

    const fetchPreview = async () => {
        setLoading(true);
        setError(null);
        try {
            const params = new URLSearchParams({
                total_amount: settlementAmount,
                down_payment: downPayment,
                installments: installments,
                frequency: frequency,
                start_date: startDate
            });
            const response = await fetch(`http://localhost:8000/api/v1/payment-plans/preview?${params}`);
            if (!response.ok) throw new Error("Failed to load preview");
            const data = await response.json();
            setPreview(data);
        } catch (e) {
            setError(e.message);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        const timer = setTimeout(() => {
            fetchPreview();
        }, 500);
        return () => clearTimeout(timer);
    }, [settlementAmount, downPayment, installments, frequency, startDate]);

    const [activationStep, setActivationStep] = useState('form'); // 'form', 'success'
    const [activationResult, setActivationResult] = useState(null);

    const handleSavePlan = async () => {
        setSaving(true);
        setError(null);
        try {
            const response = await fetch('http://localhost:8000/api/v1/payment-plans', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    debt_id: debtId,
                    total_settlement_amount: parseFloat(settlementAmount),
                    down_payment_amount: parseFloat(downPayment),
                    installment_count: parseInt(installments),
                    frequency: frequency,
                    start_date: startDate,
                    is_settlement: isSettlement,
                    card_number: cardNumber,
                    card_expiry: expiry,
                    card_cvv: cvv,
                    cardholder_name: cardholderName,
                    billing_address: billingAddress,
                    billing_city: billingCity,
                    billing_state: billingState,
                    billing_zip: billingZip
                })
            });
            if (!response.ok) {
                const errData = await response.json();
                throw new Error(errData.detail || "Failed to save payment plan");
            }
            const plan = await response.json();
            setActivationResult(plan);
            setActivationStep('success');
            // We delay the final callback so agent can see the success screen
            setTimeout(() => {
                onPlanCreated(plan);
            }, 3000);
        } catch (e) {
            setError(e.message);
        } finally {
            setSaving(false);
        }
    };

    if (activationStep === 'success') {
        return (
            <div className="bg-white border border-slate-200 rounded-xl overflow-hidden shadow-sm p-10 flex flex-col items-center justify-center text-center animate-in zoom-in-95 duration-500">
                <div className="w-20 h-20 bg-emerald-50 rounded-full flex items-center justify-center mb-6">
                    <CheckCircle size={48} className="text-emerald-500" />
                </div>
                <h2 className="text-2xl font-bold text-slate-900 mb-2">Activation Successful!</h2>
                <p className="text-slate-500 mb-8 max-w-xs mx-auto">The payment plan has been activated and the card has been tokenized securely.</p>

                {activationResult?.down_payment_status === 'approved' && (
                    <div className="w-full bg-slate-50 rounded-xl p-6 border border-slate-100 mb-4 animate-in slide-in-from-bottom-2 duration-700 delay-200">
                        <div className="text-[10px] text-slate-400 uppercase font-black tracking-tighter mb-1">Down Payment Processed</div>
                        <div className="text-3xl font-black text-slate-900 font-mono mb-2">${Number(downPayment).toFixed(2)}</div>
                        <div className="flex justify-center gap-4 text-[10px]">
                            <div className="text-emerald-600 font-bold uppercase py-0.5 px-2 bg-emerald-50 rounded">Approved</div>
                            <div className="text-slate-400 font-mono italic">Ref: {activationResult.dp_reference}</div>
                        </div>
                    </div>
                )}

                <div className="text-[10px] text-slate-400 font-medium">Redirecting to account dash...</div>
            </div>
        );
    }

    return (
        <div className="bg-white border border-slate-200 rounded-xl overflow-hidden shadow-sm animate-in fade-in slide-in-from-bottom-4 duration-500">
            <div className="bg-white rounded-lg p-3 border border-slate-200 flex flex-col h-[180px]">
                <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2">
                    <CreditCard size={16} className="text-blue-500" />
                    Secure Payment Arrangement
                </h3>
            </div>

            <div className="p-6">
                <div className="grid grid-cols-2 gap-8">
                    {/* LEFT: Plan Configuration */}
                    <div className="space-y-6">
                        <div className="space-y-4">
                            <div className="flex justify-between items-center border-b border-slate-100 pb-2">
                                <h4 className="text-[10px] text-slate-400 uppercase font-black tracking-widest ">Plan Type</h4>
                                <div className="flex bg-white p-0.5 rounded-md border border-slate-200 scale-90 origin-right">
                                    <button
                                        onClick={() => setIsSettlement(false)}
                                        className={`px-3 py-1 text-[9px] uppercase font-black rounded-sm transition-all ${!isSettlement ? 'bg-blue-600 text-white' : 'text-slate-500 hover:text-slate-700'}`}
                                    >
                                        Full
                                    </button>
                                    <button
                                        onClick={() => setIsSettlement(true)}
                                        className={`px-3 py-1 text-[9px] uppercase font-black rounded-sm transition-all ${isSettlement ? 'bg-blue-600 text-white' : 'text-slate-500 hover:text-slate-700'}`}
                                    >
                                        Settle
                                    </button>
                                </div>
                            </div>

                            <div className={`grid grid-cols-2 gap-4 transition-all duration-300 ${!isSettlement ? 'opacity-40 grayscale pointer-events-none' : ''}`}>
                                <div className="space-y-1.5">
                                    <label className="text-[10px] text-slate-500 uppercase font-bold">Settlement Amount</label>
                                    <div className="relative">
                                        <DollarSign size={14} className="absolute left-3 top-2.5 text-slate-400" />
                                        <input
                                            type="number"
                                            value={settlementAmount}
                                            onChange={(e) => handleAmountChange(e.target.value)}
                                            className="w-full bg-white border border-slate-200 rounded px-8 py-2 text-sm text-slate-900 focus:outline-none focus:border-blue-500/50"
                                        />
                                    </div>
                                </div>
                                <div className="space-y-1.5">
                                    <label className="text-[10px] text-slate-500 uppercase font-bold">Percentage (%)</label>
                                    <input
                                        type="number"
                                        value={settlementPercentage}
                                        onChange={(e) => handlePercentageChange(e.target.value)}
                                        className="w-full bg-white border border-slate-200 rounded px-3 py-2 text-sm text-slate-900 focus:outline-none focus:border-blue-500/50"
                                    />
                                </div>
                            </div>

                            <div className="space-y-4">
                                <h4 className="text-[10px] text-slate-400 uppercase font-black tracking-widest border-b border-slate-100 pb-2">Payment Terms</h4>
                                <div className="grid grid-cols-2 gap-4">
                                    <div className="space-y-1.5">
                                        <label className="text-[10px] text-slate-500 uppercase font-bold text-blue-600/80">Down Payment</label>
                                        <div className="relative">
                                            <DollarSign size={14} className="absolute left-3 top-2.5 text-slate-400" />
                                            <input
                                                type="number"
                                                value={downPayment}
                                                onChange={(e) => setDownPayment(e.target.value)}
                                                className="w-full bg-white border border-slate-200 rounded px-8 py-2 text-sm text-slate-900 focus:outline-none focus:border-blue-500/50"
                                            />
                                        </div>
                                    </div>
                                    <div className="space-y-1.5">
                                        <label className="text-[10px] text-slate-500 uppercase font-bold">First Payment Date</label>
                                        <input
                                            type="date"
                                            value={startDate}
                                            onChange={(e) => setStartDate(e.target.value)}
                                            className="w-full bg-white border border-slate-200 rounded px-3 py-2 text-sm text-slate-900 focus:outline-none focus:border-blue-500/50 transition-all cursor-pointer"
                                        />
                                    </div>
                                </div>

                                <div className="grid grid-cols-2 gap-4">
                                    <div className="space-y-1.5">
                                        <label className="text-[10px] text-slate-500 uppercase font-bold">Frequency</label>
                                        <select
                                            value={frequency}
                                            onChange={(e) => setFrequency(e.target.value)}
                                            className="w-full bg-white border border-slate-200 rounded px-3 py-2 text-sm text-slate-900 focus:outline-none focus:border-blue-500/50"
                                        >
                                            <option value="weekly">Weekly</option>
                                            <option value="bi-weekly">Bi-Weekly</option>
                                            <option value="monthly">Monthly</option>
                                        </select>
                                    </div>
                                    <div className="space-y-1.5">
                                        <label className="text-[10px] text-slate-500 uppercase font-bold">Installments</label>
                                        <input
                                            type="number"
                                            value={installments}
                                            onChange={(e) => setInstallments(e.target.value)}
                                            className="w-full bg-white border border-slate-200 rounded px-3 py-2 text-sm text-slate-900 focus:outline-none focus:border-blue-500/50"
                                        />
                                    </div>
                                </div>
                            </div>

                            <div className="space-y-4 pt-2">
                                <h4 className="text-[10px] text-slate-400 uppercase font-black tracking-widest border-b border-slate-100 pb-2">Schedule Preview</h4>
                                <div className="bg-white rounded-lg p-3 border border-slate-200 flex flex-col h-[180px]">
                                    <div className="flex justify-between items-center mb-2">
                                        <label className="text-[10px] text-slate-600 uppercase font-bold">Installment Stream</label>
                                        {loading && <Clock size={12} className="animate-spin text-blue-500" />}
                                    </div>

                                    <div className="flex-1 overflow-y-auto custom-scrollbar pr-2 space-y-1.5">
                                        {preview && Array.isArray(preview) && preview.map((pay, i) => (
                                            <div key={i} className="flex justify-between items-center p-2 bg-white rounded border border-slate-200 hover:border-slate-300 transition-colors">
                                                <div className="flex flex-col">
                                                    <div className="text-[10px] text-slate-500">
                                                        <span className="opacity-30 mr-2">#{i + 1}</span>
                                                        {pay?.due_date ? new Date(pay.due_date).toLocaleDateString() : 'N/A'}
                                                    </div>
                                                    {pay?.type && (
                                                        <div className={`text-[8px] uppercase font-black ${pay.type === 'Down Payment' ? 'text-blue-600' : 'text-slate-400'}`}>
                                                            {pay.type}
                                                        </div>
                                                    )}
                                                </div>
                                                <div className="text-xs font-mono text-slate-900">${Number(pay?.amount || 0).toFixed(2)}</div>
                                            </div>
                                        ))}
                                        {(!preview || preview.length === 0) && !loading && (
                                            <div className="h-full flex items-center justify-center text-[10px] text-slate-400 italic">
                                                Configure a plan to see preview
                                            </div>
                                        )}
                                    </div>

                                    <div className="mt-3 pt-2 border-t border-slate-200 flex justify-between items-center">
                                        <span className="text-[10px] text-slate-500">Plan Total:</span>
                                        <span className="text-xs text-blue-600 font-bold">${Number(settlementAmount || 0).toFixed(2)}</span>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>

                    {/* RIGHT: Card & Billing Info */}
                    <div className="space-y-6">
                        <div className="space-y-4">
                            <h4 className="text-[10px] text-slate-400 uppercase font-black tracking-widest border-b border-slate-100 pb-2">Card Information</h4>
                            <div className="space-y-3">
                                <div className="space-y-1.5">
                                    <label className="text-[10px] text-slate-500 uppercase font-bold">Cardholder Name</label>
                                    <input
                                        type="text"
                                        placeholder="Name as it appears on card"
                                        value={cardholderName}
                                        onChange={(e) => setCardholderName(e.target.value)}
                                        className="w-full bg-white border border-slate-200 rounded px-3 py-2 text-sm text-slate-900 focus:outline-none focus:border-blue-500/50"
                                    />
                                </div>
                                <div className="space-y-1.5">
                                    <label className="text-[10px] text-slate-500 uppercase font-bold">Card Number</label>
                                    <div className="relative">
                                        <CreditCard size={14} className="absolute left-3 top-2.5 text-slate-400" />
                                        <input
                                            type="text"
                                            placeholder="XXXX XXXX XXXX XXXX"
                                            value={cardNumber}
                                            onChange={(e) => setCardNumber(e.target.value)}
                                            className="w-full bg-white border border-slate-200 rounded px-8 py-2 text-sm text-slate-900 focus:outline-none focus:border-blue-500/50 font-mono"
                                        />
                                    </div>
                                </div>
                                <div className="grid grid-cols-2 gap-4">
                                    <div className="space-y-1.5">
                                        <label className="text-[10px] text-slate-500 uppercase font-bold">Expiry (MMYY)</label>
                                        <input
                                            type="text"
                                            placeholder="MMYY"
                                            maxLength="4"
                                            value={expiry}
                                            onChange={(e) => setExpiry(e.target.value)}
                                            className="w-full bg-white border border-slate-200 rounded px-3 py-2 text-sm text-slate-900 focus:outline-none focus:border-blue-500/50 font-mono"
                                        />
                                    </div>
                                    <div className="space-y-1.5">
                                        <label className="text-[10px] text-slate-500 uppercase font-bold">CVV</label>
                                        <input
                                            type="text"
                                            placeholder="123"
                                            maxLength="4"
                                            value={cvv}
                                            onChange={(e) => setCvv(e.target.value)}
                                            className="w-full bg-white border border-slate-200 rounded px-3 py-2 text-sm text-slate-900 focus:outline-none focus:border-blue-500/50 font-mono"
                                        />
                                    </div>
                                </div>
                            </div>
                        </div>

                        <div className="space-y-4">
                            <h4 className="text-[10px] text-slate-400 uppercase font-black tracking-widest border-b border-slate-100 pb-2">Billing Address</h4>
                            <div className="space-y-3">
                                <div className="space-y-1.5">
                                    <label className="text-[10px] text-slate-500 uppercase font-bold">Street Address</label>
                                    <input
                                        type="text"
                                        placeholder="1234 Main St"
                                        value={billingAddress}
                                        onChange={(e) => setBillingAddress(e.target.value)}
                                        className="w-full bg-white border border-slate-200 rounded px-3 py-2 text-sm text-slate-900 focus:outline-none focus:border-blue-500/50"
                                    />
                                </div>
                                <div className="grid grid-cols-2 gap-4">
                                    <div className="space-y-1.5">
                                        <label className="text-[10px] text-slate-500 uppercase font-bold">City</label>
                                        <input
                                            type="text"
                                            placeholder="City"
                                            value={billingCity}
                                            onChange={(e) => setBillingCity(e.target.value)}
                                            className="w-full bg-white border border-slate-200 rounded px-3 py-2 text-sm text-slate-900 focus:outline-none focus:border-blue-500/50"
                                        />
                                    </div>
                                    <div className="grid grid-cols-2 gap-2">
                                        <div className="space-y-1.5">
                                            <label className="text-[10px] text-slate-500 uppercase font-bold">State</label>
                                            <input
                                                type="text"
                                                placeholder="ST"
                                                maxLength="2"
                                                value={billingState}
                                                onChange={(e) => setBillingState(e.target.value)}
                                                className="w-full bg-white border border-slate-200 rounded px-2 py-2 text-sm text-slate-900 focus:outline-none focus:border-blue-500/50 text-center uppercase"
                                            />
                                        </div>
                                        <div className="space-y-1.5">
                                            <label className="text-[10px] text-slate-500 uppercase font-bold">ZIP</label>
                                            <input
                                                type="text"
                                                placeholder="12345"
                                                value={billingZip}
                                                onChange={(e) => setBillingZip(e.target.value)}
                                                className="w-full bg-white border border-slate-200 rounded px-2 py-2 text-sm text-slate-900 focus:outline-none focus:border-blue-500/50 text-center"
                                            />
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>

                        <div className="pt-4">
                            <button
                                onClick={handleSavePlan}
                                disabled={saving || !cardNumber}
                                className="w-full mt-6 py-4 bg-blue-600 hover:bg-blue-500 disabled:bg-slate-300 text-white font-bold rounded-xl shadow-lg active:scale-[0.98] transition-all flex items-center justify-center gap-2"
                            >
                                {saving ? (
                                    <>
                                        <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin"></div>
                                        <span>Processing...</span>
                                    </>
                                ) : (
                                    <>
                                        <CheckCircle size={20} />
                                        <span>{downPayment > 0 ? `Run Down Payment ($${Number(downPayment).toFixed(2)}) & Activate` : 'Activate Payment Plan'}</span>
                                    </>
                                )}
                            </button>

                            {error && (
                                <div className="p-3 mt-4 bg-red-50/10 border border-red-200 rounded-lg text-[10px] text-red-600 flex items-center gap-2 animate-shake">
                                    <AlertCircle size={14} /> {error}
                                </div>
                            )}
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default PaymentPlanBuilder;
