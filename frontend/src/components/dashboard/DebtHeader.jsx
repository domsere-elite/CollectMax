import React from 'react';
import { Clock, XCircle, CheckCircle } from 'lucide-react';

const DebtHeader = ({ currentDebt, isTimezoneValid, activePlan }) => {
    return (
        <div className="glass-panel border-b border-slate-100 p-6 rounded-2xl mb-6 flex justify-between items-center shadow-lg hover:shadow-xl transition-shadow duration-300">
            <div className="flex items-center gap-6">
                <div className="w-14 h-14 rounded-full bg-gradient-to-br from-blue-500 to-indigo-600 flex items-center justify-center text-white font-bold text-2xl shadow-blue-500/20 shadow-lg">
                    {currentDebt.debtorName.charAt(0)}
                </div>
                <div>
                    <h1 className="text-2xl font-bold text-slate-900 leading-tight flex items-center gap-3">
                        {currentDebt.debtorName}
                        <span className="text-[10px] bg-blue-50 text-blue-600 px-2 py-0.5 rounded-full border border-blue-100 uppercase tracking-wider font-bold shadow-sm">Primary</span>
                        {activePlan && (
                            <span className="text-[10px] bg-emerald-50 text-emerald-600 px-2 py-0.5 rounded-full border border-emerald-100 uppercase tracking-wider font-bold shadow-sm">Plan Active</span>
                        )}
                    </h1>
                    <div className="text-xs text-slate-400 font-mono flex gap-4 mt-1.5 items-center">
                        <span className="bg-slate-50 px-2 py-0.5 rounded border border-slate-100 text-slate-500">ID: {currentDebt.id}</span>
                        <span className="w-1 h-1 bg-slate-200 rounded-full"></span>
                        <span className="bg-slate-50 px-2 py-0.5 rounded border border-slate-100 text-slate-500">SSN: {currentDebt.ssnHash}</span>
                    </div>
                </div>
            </div>

            <div className="flex gap-8 text-right">
                <div>
                    <div className="text-[10px] text-slate-400 uppercase tracking-widest font-bold mb-1">Total Paid</div>
                    <div className="text-2xl font-bold text-emerald-600 font-mono tracking-tight">${currentDebt.totalPaid.toLocaleString(undefined, { minimumFractionDigits: 2 })}</div>
                </div>
                <div>
                    <div className="text-[10px] text-slate-400 uppercase tracking-widest font-bold mb-1">Current Balance</div>
                    <div className="text-2xl font-bold text-red-600 font-mono tracking-tight">${currentDebt.amountDue.toLocaleString(undefined, { minimumFractionDigits: 2 })}</div>
                </div>
                <div>
                    <div className="text-[10px] text-slate-400 uppercase tracking-widest font-bold mb-1">Local Time</div>
                    <div className={`text-xl font-bold font-mono flex items-center gap-2 ${!isTimezoneValid ? 'text-red-500' : 'text-slate-700'}`}>
                        {!isTimezoneValid ? <XCircle size={16} className="text-red-500" /> : <Clock size={16} className="text-emerald-500" />}
                        04:32 PM <span className="text-xs text-slate-400 font-sans font-normal ml-1">(EST)</span>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default DebtHeader;
