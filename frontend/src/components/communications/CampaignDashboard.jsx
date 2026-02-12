import React, { useState, useEffect, useMemo } from 'react';
import { Link } from 'react-router-dom';
import { fetchCampaigns } from '../../services/api';

const CampaignDashboard = () => {
    const [campaigns, setCampaigns] = useState([]);
    const [loading, setLoading] = useState(false);

    useEffect(() => {
        const loadCampaigns = async () => {
            setLoading(true);
            try {
                const data = await fetchCampaigns();
                setCampaigns(data);
            } catch (error) {
                console.error('Failed to load campaigns:', error);
            } finally {
                setLoading(false);
            }
        };

        loadCampaigns();
    }, []);

    const stats = useMemo(() => {
        const totals = campaigns.reduce(
            (acc, c) => {
                acc.sent += Number(c.sent_count || 0);
                acc.failed += Number(c.failed_count || 0);
                acc.recipients += Number(c.total_recipients || 0);
                acc.delivered += Number(c.delivered_count || 0);
                acc.opened += Number(c.opened_count || 0);
                acc.clicked += Number(c.clicked_count || 0);
                return acc;
            },
            { sent: 0, failed: 0, recipients: 0, delivered: 0, opened: 0, clicked: 0 }
        );

        const openRate = totals.delivered ? Math.round((totals.opened / totals.delivered) * 100) : 0;
        const clickRate = totals.delivered ? Math.round((totals.clicked / totals.delivered) * 100) : 0;

        return {
            totalSent: totals.sent,
            totalRecipients: totals.recipients,
            openRate,
            clickRate,
        };
    }, [campaigns]);

    return (
        <div className="space-y-6">
            <div className="flex justify-between items-center">
                <h1 className="text-3xl font-bold text-white">Campaigns</h1>
                <div className="space-x-3">
                    <Link
                        to="/communications/templates"
                        className="bg-gray-700 hover:bg-gray-600 text-white px-4 py-2 rounded"
                    >
                        Manage Templates
                    </Link>
                    <Link
                        to="/communications/new"
                        className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded"
                    >
                        + New Campaign
                    </Link>
                </div>
            </div>

            {/* Stats Cards */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                <StatCard label="Total Sent" value={stats.totalSent} />
                <StatCard label="Total Recipients" value={stats.totalRecipients} />
                <StatCard label="Open Rate" value={`${stats.openRate}%`} />
                <StatCard label="Click Rate" value={`${stats.clickRate}%`} />
            </div>

            {/* Recent Campaigns Table */}
            <div className="bg-gray-800 rounded-lg shadow-lg overflow-hidden">
                <div className="p-4 border-b border-gray-700">
                    <h3 className="font-semibold text-gray-200">Recent Campaigns</h3>
                </div>
                <div className="overflow-x-auto">
                    <table className="min-w-full text-left text-gray-300">
                        <thead className="bg-gray-700 text-xs uppercase text-gray-400">
                            <tr>
                                <th className="px-6 py-3">Campaign Name</th>
                                <th className="px-6 py-3">Status</th>
                                <th className="px-6 py-3">Recipients</th>
                                <th className="px-6 py-3">Sent</th>
                                <th className="px-6 py-3">Failed</th>
                                <th className="px-6 py-3">Date</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-gray-700">
                    {loading ? (
                        <tr>
                            <td colSpan="6" className="text-center py-8 text-gray-500">
                                Loading campaigns...
                            </td>
                        </tr>
                    ) : campaigns.length === 0 ? (
                        <tr>
                            <td colSpan="6" className="text-center py-8 text-gray-500">
                                No campaigns found. Start your first one!
                            </td>
                        </tr>
                            ) : (
                                campaigns.map(c => (
                                    <tr key={c.id}>
                                        <td className="px-6 py-4">{c.name}</td>
                                        <td className="px-6 py-4">
                                            <span className={`px-2 py-1 rounded text-xs ${c.status === 'completed' ? 'bg-green-900 text-green-300' :
                                                    c.status === 'draft' ? 'bg-gray-600 text-gray-300' :
                                                        'bg-blue-900 text-blue-300'
                                                }`}>
                                                {c.status}
                                            </span>
                                        </td>
                                        <td className="px-6 py-4">{c.total_recipients}</td>
                                        <td className="px-6 py-4 text-green-400">{c.sent_count}</td>
                                        <td className="px-6 py-4 text-red-400">{c.failed_count}</td>
                                        <td className="px-6 py-4 text-gray-400">
                                            {new Date(c.created_at).toLocaleDateString()}
                                        </td>
                                    </tr>
                                ))
                            )}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    );
};

const StatCard = ({ label, value }) => (
    <div className="bg-gray-800 p-4 rounded-lg border border-gray-700">
        <p className="text-gray-400 text-sm">{label}</p>
        <p className="text-2xl font-bold text-white mt-1">{value}</p>
    </div>
);

export default CampaignDashboard;
