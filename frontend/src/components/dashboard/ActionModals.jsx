import React from 'react';

const ActionModals = ({
    isEmailModalOpen,
    setIsEmailModalOpen,
    templatesLoading,
    templates,
    selectedTemplate,
    setSelectedTemplate,
    currentDebt,
    handleSendEmail,
    actionInProgress,
    isValidationModalOpen,
    setIsValidationModalOpen,
    validationUrl,
    setValidationUrl,
    handleSendValidationNotice
}) => {
    return (
        <>
            {isEmailModalOpen && (
                <div className="fixed inset-0 bg-slate-900/60 backdrop-blur-sm flex items-center justify-center z-50 animate-in fade-in duration-200">
                    <div className="bg-white rounded-2xl shadow-2xl w-full max-w-xl p-8 border border-slate-100 scale-100 animate-in zoom-in-95 duration-200">
                        <div className="flex items-center justify-between mb-6 border-b border-slate-100 pb-4">
                            <div>
                                <div className="text-xl font-bold text-slate-900">Send Email</div>
                                <div className="text-xs text-slate-500 mt-1">Select a predefined template</div>
                            </div>
                            <button
                                onClick={() => setIsEmailModalOpen(false)}
                                className="text-slate-400 hover:text-slate-600 p-2 hover:bg-slate-50 rounded-full transition-all"
                            >
                                ✕
                            </button>
                        </div>

                        <div className="border border-slate-200 rounded-xl max-h-72 overflow-y-auto custom-scrollbar mb-6">
                            {templatesLoading ? (
                                <div className="p-8 text-center text-sm text-slate-500 italic">Loading templates...</div>
                            ) : templates.length === 0 ? (
                                <div className="p-8 text-center text-sm text-slate-500 italic">No templates available.</div>
                            ) : (
                                <div className="divide-y divide-slate-100">
                                    {templates.map((template) => (
                                        <button
                                            key={template.id || template.template_id}
                                            onClick={() => setSelectedTemplate(template.template_id)}
                                            className={`w-full text-left p-4 hover:bg-slate-50 transition-all ${selectedTemplate === template.template_id ? 'bg-blue-50 border-l-4 border-blue-500' : 'border-l-4 border-transparent'}`}
                                        >
                                            <div className="text-sm font-bold text-slate-900">{template.name}</div>
                                            <div className="text-xs text-slate-500 mt-1">{template.description || 'No description provided'}</div>
                                        </button>
                                    ))}
                                </div>
                            )}
                        </div>

                        <div className="flex items-center justify-between pt-2">
                            <div className="text-xs font-mono text-slate-500 bg-slate-50 px-2 py-1 rounded border border-slate-100">
                                To: {currentDebt?.email || 'N/A'}
                            </div>
                            <div className="flex gap-3">
                                <button
                                    onClick={() => setIsEmailModalOpen(false)}
                                    className="px-4 py-2 text-sm font-bold rounded-xl border border-slate-200 text-slate-600 hover:bg-slate-50 transition-all"
                                >
                                    Cancel
                                </button>
                                <button
                                    onClick={handleSendEmail}
                                    disabled={!selectedTemplate || actionInProgress === 'email'}
                                    className="px-6 py-2 text-sm font-bold rounded-xl bg-blue-600 text-white hover:bg-blue-500 disabled:opacity-60 shadow-lg shadow-blue-500/20 transition-all active:scale-95"
                                >
                                    {actionInProgress === 'email' ? 'Sending...' : 'Send Email'}
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            )}

            {isValidationModalOpen && (
                <div className="fixed inset-0 bg-slate-900/60 backdrop-blur-sm flex items-center justify-center z-50 animate-in fade-in duration-200">
                    <div className="bg-white rounded-2xl shadow-2xl w-full max-w-lg p-8 border border-slate-100 scale-100 animate-in zoom-in-95 duration-200">
                        <div className="flex items-center justify-between mb-6 border-b border-slate-100 pb-4">
                            <div>
                                <div className="text-xl font-bold text-slate-900">Send Validation Notice</div>
                                <div className="text-xs text-slate-500 mt-1">Provide a link to the PDF document</div>
                            </div>
                            <button
                                onClick={() => setIsValidationModalOpen(false)}
                                className="text-slate-400 hover:text-slate-600 p-2 hover:bg-slate-50 rounded-full transition-all"
                            >
                                ✕
                            </button>
                        </div>

                        <div className="space-y-4 mb-8">
                            <div>
                                <label className="text-xs font-bold uppercase text-slate-500 mb-2 block tracking-wider">PDF URL</label>
                                <input
                                    type="url"
                                    value={validationUrl}
                                    onChange={(e) => setValidationUrl(e.target.value)}
                                    placeholder="https://.../validation-notice.pdf"
                                    className="w-full px-4 py-3 rounded-xl bg-slate-50 border border-slate-200 text-sm text-slate-900 placeholder:text-slate-400 focus:outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-500/10 transition-all"
                                    autoFocus
                                />
                            </div>
                            <p className="text-xs text-slate-400 italic">
                                The system will generate a secure validation email containing this link.
                            </p>
                        </div>

                        <div className="flex items-center justify-between pt-2">
                            <div className="text-xs font-mono text-slate-500 bg-slate-50 px-2 py-1 rounded border border-slate-100">
                                To: {currentDebt?.email || 'N/A'}
                            </div>
                            <div className="flex gap-3">
                                <button
                                    onClick={() => setIsValidationModalOpen(false)}
                                    className="px-4 py-2 text-sm font-bold rounded-xl border border-slate-200 text-slate-600 hover:bg-slate-50 transition-all"
                                >
                                    Cancel
                                </button>
                                <button
                                    onClick={handleSendValidationNotice}
                                    disabled={actionInProgress === 'validation'}
                                    className="px-6 py-2 text-sm font-bold rounded-xl bg-emerald-600 text-white hover:bg-emerald-500 disabled:opacity-60 shadow-lg shadow-emerald-500/20 transition-all active:scale-95"
                                >
                                    {actionInProgress === 'validation' ? 'Sending...' : 'Send Notice'}
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            )}
        </>
    );
};

export default ActionModals;
