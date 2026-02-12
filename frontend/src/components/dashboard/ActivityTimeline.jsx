import React, { useEffect, useState } from 'react';
import { fetchDebtInteractions } from '../../services/api';

const ActivityTimeline = ({ debtId, statusMsg }) => {
    const [interactions, setInteractions] = useState([]);
    const [loading, setLoading] = useState(false);

    const loadInteractions = async () => {
        if (!debtId) return;
        setLoading(true);
        try {
            const data = await fetchDebtInteractions(debtId);
            setInteractions(data || []);
        } catch (e) {
            console.error("Failed to load interactions", e);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        loadInteractions();
    }, [debtId, statusMsg]); // Reload when debt changes or a new action occurs (statusMsg update)

    return (
        <div className="glass-panel p-6 rounded-2xl h-48 overflow-y-auto custom-scrollbar shadow-lg border border-slate-200/60 relative">
            <h3 className="text-xs font-bold text-slate-400 uppercase tracking-widest mb-4 sticky top-0 bg-white/95 backdrop-blur-md py-2 z-10 flex justify-between items-center border-b border-slate-100">
                <span>Activity Timeline</span>
                <button
                    onClick={loadInteractions}
                    className="text-[10px] bg-slate-50 hover:bg-slate-100 px-2 py-1 rounded text-slate-500 font-bold transition-colors"
                >
                    Refresh
                </button>
            </h3>

            {statusMsg && (
                <div className={`text-xs p-3 mb-4 rounded-xl border flex items-center gap-3 animate-in slide-in-from-top-2 duration-300 ${statusMsg.type === 'success' ? 'bg-emerald-50 border-emerald-100 text-emerald-700' :
                        statusMsg.type === 'error' ? 'bg-red-50 border-red-100 text-red-700' :
                            'bg-blue-50 border-blue-100 text-blue-700'
                    }`}>
                    <span className={`w-2 h-2 rounded-full ${statusMsg.type === 'success' ? 'bg-emerald-500' :
                            statusMsg.type === 'error' ? 'bg-red-500' :
                                'bg-blue-500'
                        }`}></span>
                    <span className="font-medium">{statusMsg.text}</span>
                </div>
            )}

            <div className="space-y-4 border-l-2 border-slate-100 ml-2 pl-4 pb-2 relative">
                {loading && interactions.length === 0 && (
                    <div className="text-xs text-slate-400 italic pl-1">Loading history...</div>
                )}

                {!loading && interactions.length === 0 && (
                    <div className="text-xs text-slate-400 italic pl-1">No activity recorded yet.</div>
                )}

                {interactions.map((item, index) => (
                    <div key={item.id || index} className="relative group">
                        <span className={`absolute -left-[21px] top-1.5 w-3 h-3 rounded-full ring-4 ring-white shadow-sm z-10 transition-colors ${index === 0 ? 'bg-blue-500' : 'bg-slate-200 group-hover:bg-slate-300'
                            }`}></span>
                        <div className="text-[10px] text-slate-400 font-mono tracking-wide uppercase font-bold mb-0.5">
                            {new Date(item.created_at).toLocaleString([], { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })}
                        </div>
                        <div className={`text-sm p-2 rounded-lg inline-block border transition-colors ${index === 0 ? 'bg-blue-50 text-blue-900 border-blue-100' : 'bg-slate-50 text-slate-700 border-transparent group-hover:border-slate-200'
                            }`}>
                            <span className="font-bold mr-1">{item.action_type}:</span>
                            {item.notes}
                        </div>
                    </div>
                ))}
            </div>
        </div>
    );
};

export default ActivityTimeline;
