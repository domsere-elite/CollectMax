import React, { useState } from 'react';
import { uploadPortfolio } from '../services/api';
import PaymentManager from './PaymentManager';

const AdminDashboard = () => {
    const [uploadStatus, setUploadStatus] = useState("Idle");

    const handleFileUpload = async (e) => {
        const file = e.target.files[0];
        if (!file) return;

        setUploadStatus("Uploading...");
        try {
            await uploadPortfolio(file);
            setUploadStatus("Upload Complete!");
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
                </div>

                {/* Remittance Report (Simplified Mock) */}
                <div className="bg-white p-6 rounded-lg border border-slate-200 shadow-sm">
                    <h3 className="text-xl font-bold mb-4 text-slate-900">Remittance Report</h3>
                    <div className="space-y-4">
                        <div className="flex justify-between items-center p-3 bg-slate-50 rounded border border-slate-100">
                            <span className="text-sm text-slate-600">Total Collected Today</span>
                            <span className="font-mono font-bold text-slate-900 text-lg">$15,500.00</span>
                        </div>
                        <div className="flex justify-between items-center p-3 bg-emerald-50 rounded border border-emerald-100">
                            <span className="text-sm text-emerald-700">Client Net Share (70%)</span>
                            <span className="font-mono font-bold text-emerald-800 text-lg">$10,850.00</span>
                        </div>
                    </div>
                </div>
            </div>

            {/* Payment Management Module */}
            <PaymentManager />
        </div>
    );
};

export default AdminDashboard;
