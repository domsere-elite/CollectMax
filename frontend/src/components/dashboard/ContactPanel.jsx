import React from 'react';
import { User, Phone, Mail, AlertTriangle, XCircle, CheckCircle } from 'lucide-react';

const ContactPanel = ({
    currentDebt,
    handleCall,
    isTimezoneValid,
    is7in7Warning,
    isEditingEmail,
    emailDraft,
    setEmailDraft,
    handleSaveEmail,
    setIsEditingEmail,
    actionInProgress
}) => {
    return (
        <div className="glass-panel p-6 rounded-2xl flex-1 flex flex-col gap-6 shadow-lg h-full transition-all duration-300 hover:shadow-xl border border-slate-200/60">
            <h3 className="text-xs font-bold text-slate-400 uppercase tracking-widest flex items-center gap-2 pb-2 border-b border-slate-100/50">
                <User size={14} className="text-blue-500" /> Contact Details
            </h3>

            <div className="space-y-5">
                {/* Phone Section */}
                <div className="group rounded-xl p-3 hover:bg-slate-50/80 transition-all border border-transparent hover:border-slate-100">
                    <label className="text-[10px] text-slate-400 uppercase font-bold tracking-wider mb-1 block">Primary Phone</label>
                    <div className="flex justify-between items-center">
                        <div className="font-mono text-slate-900 text-base tracking-tight font-medium">{currentDebt.phone}</div>
                        <button
                            onClick={handleCall}
                            disabled={!isTimezoneValid}
                            className="p-2 bg-emerald-50 text-emerald-600 rounded-lg hover:bg-emerald-500 hover:text-white transition-all disabled:opacity-50 disabled:cursor-not-allowed shadow-sm hover:shadow-md active:scale-95"
                            title="Call Now"
                        >
                            <Phone size={16} />
                        </button>
                    </div>
                </div>

                {/* Email Section */}
                <div className="group rounded-xl p-3 hover:bg-slate-50/80 transition-all border border-transparent hover:border-slate-100">
                    <label className="text-[10px] text-slate-400 uppercase font-bold tracking-wider mb-1 block">Email Address</label>
                    <div className="flex justify-between items-center gap-3">
                        {isEditingEmail ? (
                            <input
                                type="email"
                                value={emailDraft}
                                onChange={(e) => setEmailDraft(e.target.value)}
                                className="flex-1 px-3 py-1.5 text-sm bg-white border border-slate-200 rounded-lg focus:outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20 transition-all shadow-sm"
                                autoFocus
                            />
                        ) : (
                            <div className="font-sans text-slate-700 text-sm truncate">{currentDebt.email}</div>
                        )}

                        {isEditingEmail ? (
                            <div className="flex gap-2">
                                <button
                                    onClick={handleSaveEmail}
                                    disabled={actionInProgress === 'update_email'}
                                    className="px-3 py-1.5 text-xs font-medium bg-emerald-500 text-white rounded-lg hover:bg-emerald-600 shadow-sm active:scale-95 transition-all"
                                >
                                    Save
                                </button>
                                <button
                                    onClick={() => {
                                        setEmailDraft(currentDebt.email || "");
                                        setIsEditingEmail(false);
                                    }}
                                    className="px-3 py-1.5 text-xs font-medium bg-white border border-slate-200 text-slate-500 rounded-lg hover:bg-slate-50 shadow-sm active:scale-95 transition-all"
                                >
                                    Cancel
                                </button>
                            </div>
                        ) : (
                            <button
                                onClick={() => setIsEditingEmail(true)}
                                className="p-2 bg-blue-50 text-blue-600 rounded-lg hover:bg-blue-500 hover:text-white transition-all shadow-sm hover:shadow-md active:scale-95"
                                title="Edit Email"
                            >
                                <Mail size={16} />
                            </button>
                        )}
                    </div>
                </div>

                {/* Address Section */}
                <div className="group rounded-xl p-3 hover:bg-slate-50/80 transition-all border border-transparent hover:border-slate-100">
                    <label className="text-[10px] text-slate-400 uppercase font-bold tracking-wider mb-1 block">Mailing Address</label>
                    <div className="text-sm text-slate-600 leading-relaxed font-medium">
                        {currentDebt.address}<br />
                        {currentDebt.cityStateZip}
                    </div>
                </div>
            </div>

            <div className="mt-auto border-t border-slate-100 pt-6 space-y-3">
                {is7in7Warning && (
                    <div className="bg-amber-50 border border-amber-200 p-3 rounded-xl text-xs text-amber-800 flex items-center gap-3 shadow-sm">
                        <div className="bg-amber-100 p-1.5 rounded-full text-amber-600">
                            <AlertTriangle size={14} />
                        </div>
                        <span className="font-medium">Exceeds 7-in-7 Call Limit</span>
                    </div>
                )}
                {!isTimezoneValid ? (
                    <div className="bg-red-50 border border-red-200 p-3 rounded-xl text-xs text-red-800 flex items-center gap-3 shadow-sm">
                        <div className="bg-red-100 p-1.5 rounded-full text-red-600">
                            <XCircle size={14} />
                        </div>
                        <span className="font-medium">Outside Calling Hours</span>
                    </div>
                ) : (
                    <div className="bg-emerald-50 border border-emerald-200 p-3 rounded-xl text-xs text-emerald-800 flex items-center gap-3 shadow-sm">
                        <div className="bg-emerald-100 p-1.5 rounded-full text-emerald-600">
                            <CheckCircle size={14} />
                        </div>
                        <span className="font-medium">Compliant to Call</span>
                    </div>
                )}
            </div>
        </div>
    );
};

export default ContactPanel;
