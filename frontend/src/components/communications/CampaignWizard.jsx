import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
    fetchCampaignTemplates,
    fetchPortfolios,
    previewCampaignAudience,
    launchCampaign
} from '../../services/api';

const CampaignWizard = () => {
    const navigate = useNavigate();
    const [step, setStep] = useState(1);
    const [loading, setLoading] = useState(false);

    // Campaign State
    const [campaignName, setCampaignName] = useState('');
    const [subject, setSubject] = useState('');
    const [selectedTemplate, setSelectedTemplate] = useState('');
    const [filters, setFilters] = useState({
        min_balance: '',
        max_balance: '',
        portfolio_id: '',
        status: '',
        last_email_status: '',
        last_email_before: '',
        last_email_after: '',
        last_email_older_than_days: '',
        include_unemailed: false
    });

    // Data State
    const [templates, setTemplates] = useState([]);
    const [portfolios, setPortfolios] = useState([]);
    const [recipientCount, setRecipientCount] = useState(null);

    // Fetch templates and portfolios on mount
    useEffect(() => {
        fetchCampaignTemplates()
            .then(data => setTemplates(data))
            .catch(err => console.error(err));

        fetchPortfolios()
            .then(data => setPortfolios(data))
            .catch(err => console.error(err));
    }, []);

    // Step 1: Audience Preview
    const checkAudience = async () => {
        setLoading(true);
        try {
            const payload = buildFiltersPayload(filters);
            const data = await previewCampaignAudience(payload);
            setRecipientCount(data.recipient_count || 0);
        } catch (error) {
            console.error('Error checking audience:', error);
            alert('Failed to calculate audience size');
        } finally {
            setLoading(false);
        }
    };

    // Step 3: Launch Campaign
    const handleLaunch = async () => {
        if (!campaignName || !selectedTemplate) {
            alert('Please complete all fields');
            return;
        }

        setLoading(true);
        try {
            const payload = {
                name: campaignName,
                subject: subject,
                template_id: selectedTemplate,
                filters: buildFiltersPayload(filters)
            };

            await launchCampaign(payload);
            alert('Campaign Launched Successfully!');
            navigate('/communications');
        } catch (error) {
            console.error('Launch error:', error);
            alert('Failed to launch campaign');
        } finally {
            setLoading(false);
        }
    };

    const buildFiltersPayload = (raw) => {
        const payload = { ...raw };

        payload.min_balance = raw.min_balance ? Number(raw.min_balance) : null;
        payload.max_balance = raw.max_balance ? Number(raw.max_balance) : null;
        payload.portfolio_id = raw.portfolio_id ? Number(raw.portfolio_id) : null;
        payload.last_email_older_than_days = raw.last_email_older_than_days
            ? Number(raw.last_email_older_than_days)
            : null;

        if (!raw.last_email_before) payload.last_email_before = null;
        if (!raw.last_email_after) payload.last_email_after = null;
        if (!raw.last_email_status) payload.last_email_status = null;

        return payload;
    };

    return (
        <div className="max-w-4xl mx-auto glass-panel p-8 rounded-xl my-8">
            <h1 className="text-3xl font-bold text-slate-900 mb-8">Create New Campaign</h1>

            {/* Steps Indicator */}
            <div className="flex justify-between mb-8 border-b border-slate-100 pb-4">
                <StepIndicator num={1} label="Audience" active={step >= 1} />
                <StepIndicator num={2} label="Message" active={step >= 2} />
                <StepIndicator num={3} label="Review & Launch" active={step >= 3} />
            </div>

            {/* Step 1: Audience */}
            {step === 1 && (
                <div className="space-y-6">
                    <h2 className="text-xl font-semibold text-blue-400">Define Audience</h2>
                    <div className="grid grid-cols-2 gap-6">
                        <div>
                            <label className="block text-slate-500 mb-2 text-sm uppercase tracking-wide">Minimum Balance ($)</label>
                            <input
                                type="number"
                                className="w-full bg-white text-slate-900 rounded p-3 border border-slate-200 focus:outline-none focus:border-blue-500"
                                value={filters.min_balance}
                                onChange={e => setFilters({ ...filters, min_balance: e.target.value })}
                                placeholder="0.00"
                            />
                        </div>
                        <div>
                            <label className="block text-slate-500 mb-2 text-sm uppercase tracking-wide">Maximum Balance ($)</label>
                            <input
                                type="number"
                                className="w-full bg-white text-slate-900 rounded p-3 border border-slate-200 focus:outline-none focus:border-blue-500"
                                value={filters.max_balance}
                                onChange={e => setFilters({ ...filters, max_balance: e.target.value })}
                                placeholder="No limit"
                            />
                        </div>
                        <div>
                            <label className="block text-slate-500 mb-2 text-sm uppercase tracking-wide">Portfolio</label>
                            <select
                                className="w-full bg-white text-slate-900 rounded p-3 border border-slate-200 focus:outline-none focus:border-blue-500"
                                value={filters.portfolio_id}
                                onChange={e => setFilters({ ...filters, portfolio_id: e.target.value })}
                            >
                                <option value="">All Portfolios</option>
                                {portfolios.map(p => (
                                    <option key={p.id} value={p.id}>{p.name}</option>
                                ))}
                            </select>
                        </div>
                        <div>
                            <label className="block text-slate-500 mb-2 text-sm uppercase tracking-wide">Debt Status</label>
                            <select
                                className="w-full bg-white text-slate-900 rounded p-3 border border-slate-200 focus:outline-none focus:border-blue-500"
                                value={filters.status}
                                onChange={e => setFilters({ ...filters, status: e.target.value })}
                            >
                                <option value="">All Statuses</option>
                                <option value="New">New</option>
                                <option value="Open">Open</option>
                                <option value="Payment Plan">Payment Plan</option>
                            </select>
                        </div>
                        <div>
                            <label className="block text-slate-500 mb-2 text-sm uppercase tracking-wide">Last Email Status</label>
                            <select
                                className="w-full bg-white text-slate-900 rounded p-3 border border-slate-200 focus:outline-none focus:border-blue-500"
                                value={filters.last_email_status}
                                onChange={e => setFilters({ ...filters, last_email_status: e.target.value })}
                            >
                                <option value="">Any Status</option>
                                <option value="sent">Sent</option>
                                <option value="delivered">Delivered</option>
                                <option value="opened">Opened</option>
                                <option value="clicked">Clicked</option>
                                <option value="bounced">Bounced</option>
                                <option value="spam">Spam</option>
                                <option value="failed">Failed</option>
                            </select>
                        </div>
                        <div>
                            <label className="block text-slate-500 mb-2 text-sm uppercase tracking-wide">Last Email Before</label>
                            <input
                                type="date"
                                className="w-full bg-white text-slate-900 rounded p-3 border border-slate-200 focus:outline-none focus:border-blue-500"
                                value={filters.last_email_before}
                                onChange={e => setFilters({ ...filters, last_email_before: e.target.value })}
                            />
                        </div>
                        <div>
                            <label className="block text-slate-500 mb-2 text-sm uppercase tracking-wide">Last Email After</label>
                            <input
                                type="date"
                                className="w-full bg-white text-slate-900 rounded p-3 border border-slate-200 focus:outline-none focus:border-blue-500"
                                value={filters.last_email_after}
                                onChange={e => setFilters({ ...filters, last_email_after: e.target.value })}
                            />
                        </div>
                        <div>
                            <label className="block text-slate-500 mb-2 text-sm uppercase tracking-wide">Not Emailed in Last (Days)</label>
                            <input
                                type="number"
                                className="w-full bg-white text-slate-900 rounded p-3 border border-slate-200 focus:outline-none focus:border-blue-500"
                                value={filters.last_email_older_than_days}
                                onChange={e => setFilters({ ...filters, last_email_older_than_days: e.target.value })}
                                placeholder="30"
                            />
                        </div>
                        <div className="flex items-center gap-2 mt-8">
                            <input
                                type="checkbox"
                                checked={filters.include_unemailed}
                                onChange={e => setFilters({ ...filters, include_unemailed: e.target.checked })}
                                className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                            />
                            <span className="text-sm text-slate-600">Include never emailed</span>
                        </div>
                    </div>

                    <div className="bg-slate-50 p-4 rounded border border-slate-200 flex flex-wrap gap-4 justify-between items-center shadow-inner">
                        <span className="text-slate-500 font-medium">Estimated Recipients:</span>
                        <span className="text-2xl font-bold text-slate-900">
                            {recipientCount !== null ? recipientCount : '-'}
                        </span>
                        <button
                            onClick={checkAudience}
                            className="text-blue-600 hover:text-blue-500 underline text-sm font-semibold"
                        >
                            Refresh Calculate
                        </button>
                    </div>

                    <div className="flex justify-end">
                        <button
                            onClick={() => setStep(2)}
                            disabled={recipientCount === 0}
                            className="bg-blue-600 hover:bg-blue-700 text-white px-6 py-2 rounded disabled:opacity-50"
                        >
                            Next: Select Message
                        </button>
                    </div>
                </div>
            )}

            {step === 2 && (
                <div className="space-y-6">
                    <h2 className="text-xl font-semibold text-blue-600">Campaign Content</h2>

                    <div>
                        <label className="block text-slate-500 mb-2 text-sm uppercase tracking-wide">Internal Campaign Name</label>
                        <input
                            type="text"
                            className="w-full bg-white text-slate-900 rounded p-3 border border-slate-200 focus:outline-none focus:border-blue-500"
                            value={campaignName}
                            onChange={e => setCampaignName(e.target.value)}
                            placeholder="e.g. Feb 2026 Validation Blast"
                            required
                        />
                    </div>

                    <div>
                        <label className="block text-slate-500 mb-2 text-sm uppercase tracking-wide">Email Subject Line</label>
                        <input
                            type="text"
                            className="w-full bg-white text-slate-900 rounded p-3 border border-slate-200 focus:outline-none focus:border-blue-500"
                            value={subject}
                            onChange={e => setSubject(e.target.value)}
                            placeholder="Important Information Regarding Your Account"
                            required
                        />
                        <p className="text-xs text-slate-500 mt-1">Overrides SendGrid template subject if supported</p>
                    </div>

                    <div>
                        <label className="block text-slate-500 mb-2 text-sm uppercase tracking-wide">Select Template</label>
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                            {templates.map(t => (
                                <div
                                    key={t.id}
                                    onClick={() => setSelectedTemplate(t.template_id)}
                                    className={`p-4 rounded-xl border cursor-pointer transition-all ${selectedTemplate === t.template_id
                                        ? 'bg-blue-50 border-blue-500 ring-1 ring-blue-500 shadow-md'
                                        : 'bg-white border-slate-200 hover:bg-slate-50 hover:border-slate-300'
                                        }`}
                                >
                                    <h3 className="font-bold text-slate-900">{t.name}</h3>
                                    <p className="text-sm text-slate-500 mt-1">{t.description}</p>
                                    <p className="text-xs text-slate-400 mt-2 font-mono bg-slate-100 inline-block px-1 rounded">{t.template_id}</p>
                                </div>
                            ))}
                        </div>
                    </div>

                    <div className="flex justify-between mt-8">
                        <button onClick={() => setStep(1)} className="text-slate-500 hover:text-slate-800 font-medium px-4">Back</button>
                        <button
                            onClick={() => setStep(3)}
                            disabled={!selectedTemplate || !campaignName}
                            className="bg-blue-600 hover:bg-blue-700 text-white px-6 py-2 rounded disabled:opacity-50"
                        >
                            Next: Review
                        </button>
                    </div>
                </div>
            )}

            {step === 3 && (
                <div className="space-y-6">
                    <h2 className="text-xl font-semibold text-blue-600">Review & Launch</h2>

                    <div className="bg-slate-50 p-6 rounded-xl border border-slate-200 space-y-4">
                        <div className="flex justify-between border-b border-slate-200 pb-2">
                            <span className="text-slate-500">Audience Size</span>
                            <span className="text-slate-900 font-bold">{recipientCount} Debtors</span>
                        </div>
                        <div className="flex justify-between border-b border-slate-200 pb-2">
                            <span className="text-slate-500">Campaign Name</span>
                            <span className="text-slate-900">{campaignName}</span>
                        </div>
                        <div className="flex justify-between border-b border-slate-200 pb-2">
                            <span className="text-slate-500">Template ID</span>
                            <span className="font-mono text-blue-600 bg-blue-50 px-1 rounded">{selectedTemplate}</span>
                        </div>
                        <div className="flex justify-between">
                            <span className="text-slate-500">Subject</span>
                            <span className="text-slate-900 italic">{subject}</span>
                        </div>
                    </div>

                    <div className="bg-amber-50 border border-amber-200 p-4 rounded-lg text-amber-800 text-sm">
                        <strong className="block mb-1 text-amber-900 flex items-center gap-2"><div className="w-2 h-2 rounded-full bg-amber-500"></div> Warning</strong>
                        You are about to queue {recipientCount} emails. This action cannot be undone once started.
                    </div>

                    <div className="flex justify-between pt-4">
                        <button onClick={() => setStep(2)} className="text-slate-500 hover:text-slate-800 font-medium px-4">Back</button>
                        <button
                            onClick={handleLaunch}
                            disabled={loading}
                            className="bg-green-600 hover:bg-green-700 text-white px-8 py-3 rounded-lg font-bold shadow-lg transform transition hover:scale-105"
                        >
                            {loading ? 'Launching...' : '🚀 Launch Campaign'}
                        </button>
                    </div>
                </div>
            )}
        </div>
    );
};

const StepIndicator = ({ num, label, active }) => (
    <div className={`flex items-center space-x-2 ${active ? 'text-blue-600' : 'text-slate-400'}`}>
        <div className={`w-8 h-8 rounded-full flex items-center justify-center font-bold border-2 transition-all 
            ${active ? 'border-blue-600 bg-blue-600 text-white' : 'border-slate-300 bg-white text-slate-500'}`}>
            {num}
        </div>
        <span className="font-medium text-sm">{label}</span>
    </div>
);

export default CampaignWizard;
