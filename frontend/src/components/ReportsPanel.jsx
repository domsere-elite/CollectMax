import { useEffect, useState } from 'react';
import { fetchDailyMoneyReport, fetchLiquidationReport, fetchPortfolios } from '../services/api';

const ReportsPanel = () => {
    const today = new Date().toISOString().slice(0, 10);
    const [reportDate, setReportDate] = useState(today);
    const [dailyReport, setDailyReport] = useState(null);
    const [liquidation, setLiquidation] = useState([]);
    const [portfolios, setPortfolios] = useState([]);
    const [portfolioId, setPortfolioId] = useState('');
    const [loadingDaily, setLoadingDaily] = useState(true);
    const [loadingLiquidation, setLoadingLiquidation] = useState(true);

    const loadDaily = async (date) => {
        setLoadingDaily(true);
        try {
            const data = await fetchDailyMoneyReport(date);
            setDailyReport(data);
        } catch (e) {
            console.error(e);
        } finally {
            setLoadingDaily(false);
        }
    };

    const loadLiquidation = async (selectedId = null) => {
        setLoadingLiquidation(true);
        try {
            const data = await fetchLiquidationReport(selectedId || null);
            setLiquidation(Array.isArray(data) ? data : (data ? [data] : []));
        } catch (e) {
            console.error(e);
        } finally {
            setLoadingLiquidation(false);
        }
    };

    const loadPortfolios = async () => {
        try {
            const data = await fetchPortfolios();
            setPortfolios(Array.isArray(data) ? data : []);
        } catch (e) {
            console.error(e);
        }
    };

    useEffect(() => {
        loadDaily(reportDate);
    }, [reportDate]);

    useEffect(() => {
        loadLiquidation();
    }, []);

    useEffect(() => {
        loadPortfolios();
    }, []);

    useEffect(() => {
        loadLiquidation(portfolioId ? Number(portfolioId) : null);
    }, [portfolioId]);

    const handleExportCsv = () => {
        const headers = [
            'portfolio_id',
            'name',
            'face_value',
            'posted_total',
            'pending_total',
            'posted_liquidation',
            'total_liquidation'
        ];
        const rows = liquidation.map((row) => [
            row.portfolio_id,
            row.name,
            Number(row.face_value).toFixed(2),
            Number(row.posted_total).toFixed(2),
            Number(row.pending_total).toFixed(2),
            (row.posted_liquidation * 100).toFixed(4),
            (row.total_liquidation * 100).toFixed(4)
        ]);

        const csv = [headers.join(','), ...rows.map((r) => r.join(','))].join('\n');
        const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
        const url = URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        link.download = `liquidation_report_${new Date().toISOString().slice(0, 10)}.csv`;
        link.click();
        URL.revokeObjectURL(url);
    };

    const green = dailyReport?.green || { total: 0, count: 0 };
    const red = dailyReport?.red || { total: 0, count: 0 };
    const blue = dailyReport?.blue || { total: 0, count: 0 };

    return (
        <div className="space-y-6">
            <div className="bg-white p-6 rounded-lg border border-slate-200 shadow-sm">
                <div className="flex flex-wrap items-center justify-between gap-4 mb-6">
                    <div>
                        <h3 className="text-xl font-bold text-slate-900">Daily Money Report</h3>
                        <p className="text-sm text-slate-500">Green = new money collected today. Red/Blue = new money scheduled today.</p>
                    </div>
                    <div className="flex items-center gap-2">
                        <label className="text-[10px] uppercase tracking-wide text-slate-400">Report Date</label>
                        <input
                            type="date"
                            value={reportDate}
                            onChange={(e) => setReportDate(e.target.value)}
                            className="bg-slate-50 border border-slate-200 rounded px-2 py-1.5 text-sm text-slate-700 outline-none focus:border-blue-500/50"
                        />
                    </div>
                </div>

                {loadingDaily ? (
                    <div className="text-slate-400 text-sm">Loading daily report...</div>
                ) : (
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                        <div className="p-4 rounded-lg border border-emerald-100 bg-emerald-50">
                            <div className="text-[10px] uppercase tracking-widest text-emerald-600">Green (Collected)</div>
                            <div className="mt-2 flex items-baseline justify-between">
                                <div className="text-2xl font-bold text-emerald-800">${green.total.toFixed(2)}</div>
                                <div className="text-sm font-mono text-emerald-700">{green.count}</div>
                            </div>
                        </div>
                        <div className="p-4 rounded-lg border border-red-100 bg-red-50">
                            <div className="text-[10px] uppercase tracking-widest text-red-600">Red (Scheduled &lt;= Month End)</div>
                            <div className="mt-2 flex items-baseline justify-between">
                                <div className="text-2xl font-bold text-red-700">${red.total.toFixed(2)}</div>
                                <div className="text-sm font-mono text-red-600">{red.count}</div>
                            </div>
                        </div>
                        <div className="p-4 rounded-lg border border-blue-100 bg-blue-50">
                            <div className="text-[10px] uppercase tracking-widest text-blue-600">Blue (Scheduled &gt; Month End)</div>
                            <div className="mt-2 flex items-baseline justify-between">
                                <div className="text-2xl font-bold text-blue-700">${blue.total.toFixed(2)}</div>
                                <div className="text-sm font-mono text-blue-600">{blue.count}</div>
                            </div>
                        </div>
                    </div>
                )}
            </div>

            <div className="bg-white p-6 rounded-lg border border-slate-200 shadow-sm">
                <div className="flex flex-wrap items-center justify-between gap-3 mb-6">
                    <div>
                        <h3 className="text-xl font-bold text-slate-900">Liquidation by Portfolio</h3>
                        <p className="text-sm text-slate-500">Posted = collected. Total = posted + pending.</p>
                    </div>
                    <div className="flex flex-wrap items-center gap-2">
                        <select
                            value={portfolioId}
                            onChange={(e) => setPortfolioId(e.target.value)}
                            className="bg-slate-50 border border-slate-200 rounded px-3 py-2 text-sm text-slate-700 outline-none focus:border-blue-500/50"
                        >
                            <option value="">All Portfolios</option>
                            {portfolios.map((p) => (
                                <option key={p.id} value={p.id}>{p.name}</option>
                            ))}
                        </select>
                        <button
                            onClick={() => loadLiquidation(portfolioId ? Number(portfolioId) : null)}
                            className="px-3 py-1.5 bg-slate-100 hover:bg-slate-200 rounded text-slate-600 text-xs font-bold uppercase"
                        >
                            Refresh
                        </button>
                        <button
                            onClick={handleExportCsv}
                            className="px-3 py-1.5 bg-emerald-600 hover:bg-emerald-500 rounded text-white text-xs font-bold uppercase"
                            disabled={liquidation.length === 0}
                        >
                            Export CSV
                        </button>
                    </div>
                </div>

                {loadingLiquidation ? (
                    <div className="text-slate-400 text-sm">Loading liquidation report...</div>
                ) : (
                    <div className="overflow-x-auto">
                        <table className="w-full text-left text-sm border-separate border-spacing-y-2">
                            <thead>
                                <tr className="text-slate-400 uppercase text-[10px] tracking-widest px-4">
                                    <th className="pb-2 pl-4">Portfolio</th>
                                    <th className="pb-2">Face Value</th>
                                    <th className="pb-2">Posted</th>
                                    <th className="pb-2">Pending</th>
                                    <th className="pb-2">Posted %</th>
                                    <th className="pb-2 pr-4">Total %</th>
                                </tr>
                            </thead>
                            <tbody>
                                {liquidation.length === 0 ? (
                                    <tr><td colSpan="6" className="text-center py-10 text-slate-400">No portfolios found.</td></tr>
                                ) : liquidation.map((row) => (
                                    <tr key={row.portfolio_id} className="bg-white border border-slate-100 rounded-lg shadow-sm">
                                        <td className="py-3 pl-4 rounded-l-lg border-y border-l border-slate-100">
                                            <div className="font-medium text-slate-900">{row.name}</div>
                                        </td>
                                        <td className="py-3 border-y border-slate-100">
                                            <div className="font-mono text-slate-900">${Number(row.face_value).toFixed(2)}</div>
                                        </td>
                                        <td className="py-3 border-y border-slate-100">
                                            <div className="font-mono text-emerald-700">${Number(row.posted_total).toFixed(2)}</div>
                                        </td>
                                        <td className="py-3 border-y border-slate-100">
                                            <div className="font-mono text-slate-700">${Number(row.pending_total).toFixed(2)}</div>
                                        </td>
                                        <td className="py-3 border-y border-slate-100">
                                            <div className="font-mono text-emerald-800">{(row.posted_liquidation * 100).toFixed(2)}%</div>
                                        </td>
                                        <td className="py-3 pr-4 rounded-r-lg border-y border-r border-slate-100">
                                            <div className="font-mono text-slate-900">{(row.total_liquidation * 100).toFixed(2)}%</div>
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                )}
            </div>
        </div>
    );
};

export default ReportsPanel;
