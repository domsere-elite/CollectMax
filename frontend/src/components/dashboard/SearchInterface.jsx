import React from 'react';
import { Search } from 'lucide-react';

const SearchInterface = ({
    searchType,
    setSearchType,
    searchQuery,
    setSearchQuery,
    handleSearch,
    searchResults,
    setSearchResults,
    onSelectDebt
}) => {
    return (
        <div className="relative mb-6 z-30">
            {/* SEARCH BAR */}
            <div className="glass-panel p-2 rounded-2xl flex items-center gap-3 shadow-lg hover:shadow-xl transition-all border border-slate-200/50">
                <div className="pl-3 text-slate-400">
                    <Search size={20} />
                </div>
                <div className="h-6 w-px bg-slate-200"></div>
                <select
                    value={searchType}
                    onChange={(e) => setSearchType(e.target.value)}
                    className="bg-transparent text-sm font-semibold text-slate-600 focus:outline-none cursor-pointer hover:text-blue-600 transition-colors py-2"
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
                    placeholder={searchType === 'name' ? 'Search debtor by name...' : 'Search by client reference number...'}
                    className="flex-1 bg-transparent px-2 py-3 text-sm text-slate-700 placeholder:text-slate-400 focus:outline-none font-medium"
                />
            </div>

            {/* SEARCH RESULTS DROPDOWN */}
            {searchResults && searchResults.length > 0 && (
                <div className="absolute top-full left-0 right-0 mt-2 glass-panel p-2 rounded-xl shadow-2xl border border-slate-200 z-50 animate-in fade-in slide-in-from-top-2 duration-200">
                    <div className="px-3 py-2 flex justify-between items-center border-b border-slate-100 mb-1">
                        <span className="text-xs font-bold text-slate-400 uppercase tracking-widest">{searchResults.length} Matches Found</span>
                        <button
                            onClick={() => setSearchResults(null)}
                            className="text-xs text-slate-400 hover:text-slate-600 transition-colors font-medium px-2 py-1 rounded hover:bg-slate-50"
                        >
                            Close
                        </button>
                    </div>
                    <div className="space-y-1 max-h-80 overflow-y-auto custom-scrollbar p-1">
                        {searchResults.map((result, idx) => (
                            <button
                                key={idx}
                                onClick={() => onSelectDebt(result)}
                                className="w-full text-left p-3 hover:bg-blue-50/50 rounded-lg border border-transparent hover:border-blue-100 transition-all flex justify-between items-center group"
                            >
                                <div className="flex-1">
                                    <div className="text-sm font-bold text-slate-800 group-hover:text-blue-700 transition-colors">
                                        {result.debtor.first_name} {result.debtor.last_name}
                                    </div>
                                    <div className="text-xs text-slate-400 font-mono mt-1 flex items-center gap-2">
                                        <span className="bg-slate-100 px-1.5 rounded text-slate-500">Ref: {result.client_reference_number || 'N/A'}</span>
                                    </div>
                                </div>
                                <div className="text-right">
                                    <div className="text-sm font-bold text-slate-900 font-mono group-hover:text-blue-700">
                                        ${Number(result.amount_due || 0).toLocaleString()}
                                    </div>
                                    <div className={`text-[10px] font-bold uppercase mt-1 px-2 py-0.5 rounded-full inline-block ${result.status === 'Open' ? 'bg-emerald-100 text-emerald-700' : 'bg-slate-100 text-slate-500'
                                        }`}>
                                        {result.status}
                                    </div>
                                </div>
                            </button>
                        ))}
                    </div>
                </div>
            )}
        </div>
    );
};

export default SearchInterface;
