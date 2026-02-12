import React, { useEffect, useState } from 'react';
import { uploadPortfolio, fetchPortfolios, fetchIngestJob } from '../services/api';
import PaymentManager from './PaymentManager';
import ReportsPanel from './ReportsPanel';

const AdminDashboard = () => {
    const [uploadStatus, setUploadStatus] = useState("Idle");
    const [portfolios, setPortfolios] = useState([]);
    const [selectedPortfolio, setSelectedPortfolio] = useState("");
    const [ingestJob, setIngestJob] = useState(null);
    const [polling, setPolling] = useState(false);

    useEffect(() => {
        let mounted = true;
        fetchPortfolios()
            .then((data) => {
                if (!mounted) return;
                setPortfolios(data || []);
                if (data && data.length > 0) {
                    setSelectedPortfolio(String(data[0].id));
                }
            })
            .catch(() => {
                if (!mounted) return;
                setPortfolios([]);
            });
        return () => {
            mounted = false;
        };
    }, []);

    useEffect(() => {
        if (!ingestJob?.id || polling) return;
        if (ingestJob.status === "completed" || ingestJob.status === "failed") return;
        setPolling(true);
        const interval = setInterval(async () => {
            try {
                const job = await fetchIngestJob(ingestJob.id);
                setIngestJob(job);
                if (job.status === "completed" || job.status === "failed") {
                    clearInterval(interval);
                    setPolling(false);
                }
            } catch (e) {
                clearInterval(interval);
                setPolling(false);
            }
        }, 2000);

        return () => clearInterval(interval);
    }, [ingestJob, polling]);

    const handleFileUpload = async (e) => {
        const file = e.target.files[0];
        if (!file) return;
        if (!selectedPortfolio) {
            setUploadStatus("Select a portfolio first.");
            return;
        }

        setUploadStatus("Uploading...");
        try {
            const result = await uploadPortfolio(file, selectedPortfolio);
            if (result?.job_id) {
                setIngestJob({ id: result.job_id, status: "queued", filename: result.filename });
                setUploadStatus("Queued for processing...");
            } else {
                setUploadStatus("Upload Complete!");
            }
        } catch (err) {
            console.error(err);
            setUploadStatus("Error: " + err.message);
        }
    };

    return (
        <div className="max-w-6xl mx-auto space-y-8">
            <h2 className="text-2xl font-semibold mb-6 text-slate-900">Admin Control Panel</h2>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {/* Upload Portfolio */}
                <div className="bg-white p-6 rounded-lg border border-slate-200 shadow-sm">
                    <h3 className="text-xl font-bold mb-4 text-slate-900">Upload Portfolio</h3>
                    <label className="text-xs text-slate-500 uppercase font-semibold tracking-wider mb-2 block">Portfolio</label>
                    <select
                        value={selectedPortfolio}
                        onChange={(e) => setSelectedPortfolio(e.target.value)}
                        className="w-full mb-4 px-3 py-2 rounded-md border border-slate-300 text-sm text-slate-700"
                    >
                        {portfolios.length === 0 && (
                            <option value="">No portfolios available</option>
                        )}
                        {portfolios.map((p) => (
                            <option key={p.id} value={p.id}>{p.name}</option>
                        ))}
                    </select>
                    <div className="relative border-2 border-dashed border-slate-300 rounded-lg p-12 text-center hover:border-blue-500 hover:bg-slate-100/30 transition-all">
                        <input
                            type="file"
                            accept=".csv"
                            onChange={handleFileUpload}
                            className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
                        />
                        <p className="text-slate-600 pointer-events-none">Drag & Drop CSV here</p>
                        <p className="text-sm text-slate-400 mt-2 pointer-events-none">or click to browse</p>
                    </div>
                    <p className="mt-4 text-center text-sm text-blue-600 font-medium">{uploadStatus}</p>
                    {ingestJob && (
                        <div className="mt-4 p-3 rounded-md border border-slate-200 text-xs text-slate-600">
                            <div><strong>Status:</strong> {ingestJob.status}</div>
                            {ingestJob.filename ? <div><strong>File:</strong> {ingestJob.filename}</div> : null}
                            {typeof ingestJob.rows_processed !== "undefined" && (
                                <div><strong>Rows Processed:</strong> {ingestJob.rows_processed}</div>
                            )}
                            {ingestJob.error_message ? (
                                <div className="text-rose-600"><strong>Error:</strong> {ingestJob.error_message}</div>
                            ) : null}
                        </div>
                    )}
                </div>
            </div>

            <ReportsPanel />

            {/* Payment Management Module */}
            <PaymentManager />
        </div>
    );
};

export default AdminDashboard;
