import React from 'react';
import { Mail, FileText, Shield, PlusCircle, CreditCard, ChevronRight } from 'lucide-react';

const QuickActionsPanel = ({
    setIsEmailModalOpen,
    setSelectedTemplate,
    setIsValidationModalOpen,
    setActiveTab,
    setIsCreatingPlan,
    handlePayment,
    actionInProgress
}) => {
    return (
        <div className="flex flex-col gap-6 h-full">
            {/* Action Buttons Grid */}
            <div className="glass-panel p-6 rounded-2xl shadow-lg border border-slate-200/60">
                <h3 className="text-xs font-bold text-slate-400 uppercase tracking-widest mb-4 flex items-center gap-2">
                    <span className="w-1.5 h-1.5 rounded-full bg-blue-500"></span> Quick Actions
                </h3>

                <div className="grid grid-cols-2 gap-3 mb-4">
                    <button
                        onClick={() => {
                            setIsEmailModalOpen(true);
                            setSelectedTemplate('');
                        }}
                        className="flex flex-col items-center justify-center p-4 bg-white hover:bg-slate-50 rounded-xl border border-slate-100 transition-all group hover:shadow-md active:scale-95"
                    >
                        <div className="p-2 bg-blue-50 rounded-full mb-2 group-hover:bg-blue-100 transition-colors">
                            <Mail size={18} className="text-blue-600" />
                        </div>
                        <span className="text-[10px] uppercase font-bold text-slate-600 tracking-wide">Email</span>
                    </button>

                    <button
                        onClick={() => setIsValidationModalOpen(true)}
                        className="flex flex-col items-center justify-center p-4 bg-white hover:bg-slate-50 rounded-xl border border-slate-100 transition-all group hover:shadow-md active:scale-95"
                    >
                        <div className="p-2 bg-emerald-50 rounded-full mb-2 group-hover:bg-emerald-100 transition-colors">
                            <FileText size={18} className="text-emerald-600" />
                        </div>
                        <span className="text-[10px] uppercase font-bold text-slate-600 tracking-wide">Validate</span>
                    </button>

                    <button className="flex flex-col items-center justify-center p-4 bg-white hover:bg-slate-50 rounded-xl border border-slate-100 transition-all group hover:shadow-md active:scale-95 col-span-2">
                        <div className="flex items-center gap-2">
                            <Shield size={16} className="text-purple-500" />
                            <span className="text-[10px] uppercase font-bold text-slate-600 tracking-wide">Log Dispute</span>
                        </div>
                    </button>
                </div>

                <div className="space-y-3">
                    <button
                        onClick={() => {
                            setActiveTab('financial');
                            setIsCreatingPlan(true);
                        }}
                        className="w-full py-3 bg-blue-50 hover:bg-blue-100 text-blue-600 font-bold rounded-xl border border-blue-200 active:scale-95 transition-all flex items-center justify-center gap-2 shadow-sm group"
                    >
                        <PlusCircle size={16} className="group-hover:scale-110 transition-transform" />
                        <span>Payment Plan</span>
                    </button>

                    <button
                        onClick={handlePayment}
                        disabled={actionInProgress}
                        className="w-full py-3 bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-500 hover:to-teal-500 text-white font-bold rounded-xl shadow-lg shadow-emerald-900/20 active:scale-95 transition-all flex items-center justify-center gap-2"
                    >
                        {actionInProgress ? (
                            <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin"></div>
                        ) : (
                            <>
                                <CreditCard size={16} />
                                <span>Quick Pay Full</span>
                            </>
                        )}
                    </button>
                </div>
            </div>

            {/* Notes Section */}
            <div className="glass-panel p-6 rounded-2xl flex-1 flex flex-col shadow-lg border border-slate-200/60 relative overflow-hidden group">
                <h3 className="text-xs font-bold text-slate-400 uppercase tracking-widest mb-3 flex justify-between items-center z-10 relative">
                    <span>Session Notes</span>
                    <span className="px-2 py-0.5 bg-slate-100 rounded text-[9px] text-slate-500 group-hover:bg-slate-200 transition-colors cursor-pointer">Auto-Saving</span>
                </h3>
                <textarea
                    className="bg-slate-50/50 border border-slate-100 rounded-xl p-4 h-full w-full text-xs text-slate-700 leading-relaxed focus:outline-none focus:border-blue-500/50 focus:bg-white resize-none transition-all placeholder:text-slate-300 z-10 relative"
                    placeholder="Type notes from this session..."
                ></textarea>

                {/* Decorative background element */}
                <div className="absolute -bottom-10 -right-10 w-32 h-32 bg-slate-100 rounded-full blur-2xl opacity-50 z-0 pointer-events-none"></div>
            </div>
        </div>
    );
};

export default QuickActionsPanel;
