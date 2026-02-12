import React, { useState, useEffect } from 'react';
import {
    fetchWorkQueue, fetchDebtDetails, logInteraction, processPayment,
    searchDebts, fetchPaymentPlans, fetchPlanSchedule, executeScheduledPayment,
    fetchDebtPayments, runOneOffPayment, fetchCampaignTemplates, sendAgentEmail,
    updateDebtorEmail, sendValidationNotice
} from '../services/api';
import { Search } from 'lucide-react';

// Sub-components
import SearchInterface from './dashboard/SearchInterface';
import DebtHeader from './dashboard/DebtHeader';
import ContactPanel from './dashboard/ContactPanel';
import TabsPanel from './dashboard/TabsPanel';
import QuickActionsPanel from './dashboard/QuickActionsPanel';
import ActivityTimeline from './dashboard/ActivityTimeline';
import ActionModals from './dashboard/ActionModals';

const AgentDashboard = () => {
    const defaultAgentTemplate = {
        name: "Agent Email Template",
        template_id: "d-2292ad4d40954a3a878f9389f638ceb1",
        description: "Primary agent email template"
    };

    // State Declarations
    const [currentDebt, setCurrentDebt] = useState(null);
    const [loading, setLoading] = useState(true);
    const [statusMsg, setStatusMsg] = useState(null);
    const [activeTab, setActiveTab] = useState('general');

    // Compliance & Action State
    const [isTimezoneValid, setTimezoneValid] = useState(true);
    const [is7in7Warning, set7in7Warning] = useState(false);
    const [actionInProgress, setActionInProgress] = useState(null);

    // Search State
    const [searchType, setSearchType] = useState('name');
    const [searchQuery, setSearchQuery] = useState('');
    const [searchResults, setSearchResults] = useState(null);

    // Payment Plan State
    const [activePlan, setActivePlan] = useState(null);
    const [planSchedule, setPlanSchedule] = useState([]);
    const [isCreatingPlan, setIsCreatingPlan] = useState(false);
    const [transactions, setTransactions] = useState([]);

    // Email Template State
    const [isEmailModalOpen, setIsEmailModalOpen] = useState(false);
    const [templates, setTemplates] = useState([]);
    const [templatesLoading, setTemplatesLoading] = useState(false);
    const [selectedTemplate, setSelectedTemplate] = useState("");

    // Email Edit State
    const [isEditingEmail, setIsEditingEmail] = useState(false);
    const [emailDraft, setEmailDraft] = useState("");

    // Validation Notice State
    const [isValidationModalOpen, setIsValidationModalOpen] = useState(false);
    const [validationUrl, setValidationUrl] = useState("");

    // Effects
    useEffect(() => {
        const savedDebtId = localStorage.getItem('agent.currentDebtId');
        localStorage.removeItem('agent.currentDebt'); // Cleanup

        if (savedDebtId) {
            fetchDebtDetails(savedDebtId).then(debt => {
                mapAndSetDebt(debt);
            }).catch(e => {
                console.warn('Failed to restore current debt', e);
                setLoading(false);
            });
        } else {
            setLoading(false);
        }
    }, []);

    useEffect(() => {
        if (currentDebt) {
            localStorage.setItem('agent.currentDebtId', currentDebt.id);
        } else {
            localStorage.removeItem('agent.currentDebtId');
        }
    }, [currentDebt]);

    useEffect(() => {
        setEmailDraft(currentDebt?.email || "");
        setIsEditingEmail(false);
    }, [currentDebt]);

    useEffect(() => {
        if (!isValidationModalOpen) return;
        setValidationUrl("");
    }, [isValidationModalOpen]);

    useEffect(() => {
        if (!isEmailModalOpen) return;
        loadTemplates(); // Extracted function below
    }, [isEmailModalOpen]);

    // Restored helper functions
    const mapAndSetDebt = (debt) => {
        const mapped = {
            id: debt.id,
            debtorName: `${debt.debtor.first_name} ${debt.debtor.last_name}`,
            email: debt.debtor.email,
            phone: debt.debtor.phone,
            dob: debt.debtor.dob || 'N/A',
            address: `${debt.debtor.address_1} ${debt.debtor.address_2 || ''}`,
            cityStateZip: `${debt.debtor.city}, ${debt.debtor.state} ${debt.debtor.zip_code}`,
            zipCode: debt.debtor.zip_code,
            account: debt.original_account_number,
            clientRef: debt.client_reference_number || 'N/A',
            creditor: debt.current_creditor || debt.original_creditor || 'Unknown Creditor',
            opened: debt.date_opened || 'N/A',
            chargeOff: debt.charge_off_date || 'N/A',
            amountDue: debt.amount_due,
            principal: debt.principal_balance,
            fees: debt.fees_costs,
            last_payment_date: debt.last_payment_date || 'Never',
            lastPayAmount: debt.last_payment_amount,
            totalPaid: debt.total_paid_amount || 0,
            status: debt.status,
            rawDebtor: debt.debtor,
            ssnHash: debt.debtor.ssn_hash ? `***-**-${debt.debtor.ssn_hash.substring(0, 4)}` : 'N/A'
        };
        setCurrentDebt(mapped);
        loadPaymentPlan(debt.id);
        setLoading(false);
    };

    const loadTemplates = async () => {
        setTemplatesLoading(true);
        try {
            const data = await fetchCampaignTemplates();
            const list = data || [];
            const hasDefault = list.some((item) => item.template_id === defaultAgentTemplate.template_id);
            const merged = hasDefault ? list : [defaultAgentTemplate, ...list];
            setTemplates(merged);
            if (!selectedTemplate && merged.length > 0) {
                setSelectedTemplate(defaultAgentTemplate.template_id);
            }
        } catch (e) {
            console.error(e);
            setTemplates([defaultAgentTemplate]);
            setStatusMsg({ type: 'error', text: 'Failed to load templates' });
        } finally {
            setTemplatesLoading(false);
        }
    };

    const loadNextDebt = async () => {
        try {
            setLoading(true);
            const queue = await fetchWorkQueue();
            if (queue && queue.length > 0) {
                mapAndSetDebt(queue[0]);
            } else {
                setCurrentDebt(null);
                setActivePlan(null);
                setLoading(false);
            }
        } catch (e) {
            console.error(e);
            setStatusMsg({ type: 'error', text: "Failed to load work queue" });
            setLoading(false);
        }
    };

    const loadPaymentPlan = async (debtId) => {
        try {
            const plans = await fetchPaymentPlans(debtId);
            if (plans && plans.length > 0) {
                setActivePlan(plans[0]);
                const schedule = await fetchPlanSchedule(plans[0].id);
                setPlanSchedule(schedule);
                setIsCreatingPlan(false);
            } else {
                setActivePlan(null);
                setPlanSchedule([]);
            }
            const history = await fetchDebtPayments(debtId);
            setTransactions(history);
        } catch (e) {
            console.error("Plan load failed", e);
        }
    };

    const handleSearch = async (query) => {
        if (!query || query.trim().length < 2) {
            setSearchResults(null);
            return;
        }
        try {
            const results = await searchDebts(searchType, query);
            if (results && results.length > 0) {
                setSearchResults(results);
            } else {
                setSearchResults(null);
            }
        } catch (e) {
            setSearchResults(null);
        }
    };

    const handleSelectDebt = (debt) => {
        mapAndSetDebt(debt);
        setSearchResults(null);
        setSearchQuery("");
    };

    // Actions
    const handleCall = async () => {
        if (!isTimezoneValid) return;
        setActionInProgress('call');
        try {
            const result = await logInteraction(currentDebt.id, "Call", "Agent initiated call");
            let msg = "Call Logged";
            if (result.warning_flag === "WARNING") {
                set7in7Warning(true);
                msg += " (7-in-7 Warning)";
            }
            setStatusMsg({ type: 'success', text: msg });
        } catch (e) {
            setStatusMsg({ type: 'error', text: e.message });
            if (e.message.includes("Do Not Call")) setTimezoneValid(false);
        } finally {
            setActionInProgress(null);
        }
    };

    const handlePayment = async () => {
        setActionInProgress('pay');
        try {
            let result;
            if (activePlan) {
                result = await runOneOffPayment(currentDebt.id, currentDebt.amountDue);
            } else {
                result = await processPayment(currentDebt.id, currentDebt.amountDue);
            }
            setStatusMsg({ type: 'success', text: `Paid $${result.amount || result.amount_paid}` });
            loadNextDebt();
        } catch (e) {
            setStatusMsg({ type: 'error', text: e.message || "Payment Failed" });
        } finally {
            setActionInProgress(null);
        }
    };

    const handleSendEmail = async () => {
        if (!currentDebt?.id) return;
        if (!selectedTemplate) return;
        setActionInProgress('email');
        try {
            await sendAgentEmail(currentDebt.id, selectedTemplate);
            setStatusMsg({ type: 'success', text: 'Email sent' });
            setIsEmailModalOpen(false);
            setSelectedTemplate('');
        } catch (e) {
            setStatusMsg({ type: 'error', text: e.message || 'Email failed' });
        } finally {
            setActionInProgress(null);
        }
    };

    const handleSaveEmail = async () => {
        if (!currentDebt?.id) return;
        const trimmed = emailDraft.trim();
        if (!trimmed) return;
        setActionInProgress('update_email');
        try {
            const result = await updateDebtorEmail(currentDebt.id, trimmed);
            setCurrentDebt({ ...currentDebt, email: result.email });
            setStatusMsg({ type: 'success', text: 'Email updated' });
            setIsEditingEmail(false);
        } catch (e) {
            setStatusMsg({ type: 'error', text: e.message || 'Email update failed' });
        } finally {
            setActionInProgress(null);
        }
    };

    const handleSendValidationNotice = async () => {
        if (!currentDebt?.id) return;
        const trimmed = validationUrl.trim();
        if (!trimmed) return;
        setActionInProgress('validation');
        try {
            await sendValidationNotice(currentDebt.id, trimmed);
            setStatusMsg({ type: 'success', text: 'Validation notice sent' });
            setIsValidationModalOpen(false);
        } catch (e) {
            setStatusMsg({ type: 'error', text: e.message || 'Validation notice failed' });
        } finally {
            setActionInProgress(null);
        }
    };

    if (loading) return <div className="flex justify-center items-center h-screen text-slate-400 font-mono animate-pulse">LOADING DATA STREAM...</div>;

    return (
        <div className="min-h-screen bg-slate-50 text-slate-700 font-sans p-6">
            <div className="max-w-[1600px] mx-auto">
                <SearchInterface
                    searchType={searchType}
                    setSearchType={setSearchType}
                    searchQuery={searchQuery}
                    setSearchQuery={setSearchQuery}
                    handleSearch={handleSearch}
                    searchResults={searchResults}
                    setSearchResults={setSearchResults}
                    onSelectDebt={handleSelectDebt}
                />

                {!currentDebt ? (
                    <div className="p-32 text-centerglass-panel rounded-3xl border-2 border-dashed border-slate-200">
                        <div className="p-12 text-center">
                            <div className="w-20 h-20 bg-slate-100 rounded-full flex items-center justify-center mx-auto mb-6">
                                <Search size={32} className="text-slate-400" />
                            </div>
                            <h2 className="text-xl font-bold text-slate-700 mb-2">Ready to Collect</h2>
                            <div className="text-slate-500 font-medium">Search for an account or load the work queue to begin</div>
                        </div>
                    </div>
                ) : (
                    <div className="animate-in fade-in slide-in-from-bottom-4 duration-500">
                        <DebtHeader
                            currentDebt={currentDebt}
                            isTimezoneValid={isTimezoneValid}
                            activePlan={activePlan}
                        />

                        {/* MAIN GRID LAYOUT */}
                        <div className="grid grid-cols-12 gap-6 h-[calc(100vh-220px)] min-h-[600px]">

                            {/* COL 1: LEFT SIDEBAR (Contact) */}
                            <div className="col-span-3 flex flex-col h-full">
                                <ContactPanel
                                    currentDebt={currentDebt}
                                    handleCall={handleCall}
                                    isTimezoneValid={isTimezoneValid}
                                    is7in7Warning={is7in7Warning}
                                    isEditingEmail={isEditingEmail}
                                    emailDraft={emailDraft}
                                    setEmailDraft={setEmailDraft}
                                    handleSaveEmail={handleSaveEmail}
                                    setIsEditingEmail={setIsEditingEmail}
                                    actionInProgress={actionInProgress}
                                />
                            </div>

                            {/* COL 2: CENTER (Tabs & Timeline) */}
                            <div className="col-span-6 flex flex-col gap-6 h-full">
                                <div className="flex-1 overflow-hidden min-h-0">
                                    <TabsPanel
                                        activeTab={activeTab}
                                        setActiveTab={setActiveTab}
                                        currentDebt={currentDebt}
                                        activePlan={activePlan}
                                        isCreatingPlan={isCreatingPlan}
                                        setIsCreatingPlan={setIsCreatingPlan}
                                        planSchedule={planSchedule}
                                        transactions={transactions}
                                        handlePlanCreated={(plan) => { setStatusMsg({ type: 'success', text: "Payment Plan Activated!" }); loadPaymentPlan(currentDebt.id); }}
                                        loadPaymentPlan={loadPaymentPlan}
                                        executeScheduledPayment={executeScheduledPayment}
                                        setStatusMsg={setStatusMsg}
                                        setActionInProgress={setActionInProgress}
                                        loadNextDebt={loadNextDebt}
                                    />
                                </div>
                                <div className="h-48 shrink-0">
                                    <ActivityTimeline statusMsg={statusMsg} debtId={currentDebt?.id} />
                                </div>
                            </div>

                            {/* COL 3: RIGHT SIDEBAR (Actions) */}
                            <div className="col-span-3 flex flex-col h-full">
                                <QuickActionsPanel
                                    setIsEmailModalOpen={setIsEmailModalOpen}
                                    setSelectedTemplate={setSelectedTemplate}
                                    setIsValidationModalOpen={setIsValidationModalOpen}
                                    setActiveTab={setActiveTab}
                                    setIsCreatingPlan={setIsCreatingPlan}
                                    handlePayment={handlePayment}
                                    actionInProgress={actionInProgress}
                                />
                            </div>
                        </div>
                    </div>
                )}

                <ActionModals
                    isEmailModalOpen={isEmailModalOpen}
                    setIsEmailModalOpen={setIsEmailModalOpen}
                    templatesLoading={templatesLoading}
                    templates={templates}
                    selectedTemplate={selectedTemplate}
                    setSelectedTemplate={setSelectedTemplate}
                    currentDebt={currentDebt}
                    handleSendEmail={handleSendEmail}
                    actionInProgress={actionInProgress}
                    isValidationModalOpen={isValidationModalOpen}
                    setIsValidationModalOpen={setIsValidationModalOpen}
                    validationUrl={validationUrl}
                    setValidationUrl={setValidationUrl}
                    handleSendValidationNotice={handleSendValidationNotice}
                />
            </div>
        </div>
    );
};

export default AgentDashboard;
