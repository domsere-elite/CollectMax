import React, { useState, useEffect } from 'react';
import { fetchCampaignTemplates, registerCampaignTemplate } from '../../services/api';

const TemplateManager = () => {
    const [templates, setTemplates] = useState([]);
    const [loading, setLoading] = useState(true);
    const [showAddModal, setShowAddModal] = useState(false);
    const [newTemplate, setNewTemplate] = useState({ name: '', template_id: '', description: '' });

    useEffect(() => {
        fetchTemplates();
    }, []);

    const fetchTemplates = async () => {
        try {
            const data = await fetchCampaignTemplates();
            setTemplates(data);
        } catch (error) {
            console.error('Error fetching templates:', error);
        } finally {
            setLoading(false);
        }
    };

    const handleRegister = async (e) => {
        e.preventDefault();
        try {
            await registerCampaignTemplate(newTemplate);
            setShowAddModal(false);
            setNewTemplate({ name: '', template_id: '', description: '' });
            fetchTemplates();
        } catch (error) {
            console.error('Error registering template:', error);
        }
    };

    return (
        <div className="bg-gray-800 p-6 rounded-lg shadow-lg">
            <div className="flex justify-between items-center mb-6">
                <h2 className="text-2xl font-bold text-white">Email Templates</h2>
                <button
                    onClick={() => setShowAddModal(true)}
                    className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded transition"
                >
                    + Register SendGrid Template
                </button>
            </div>

            {loading ? (
                <div className="text-gray-400">Loading templates...</div>
            ) : (
                <div className="overflow-x-auto">
                    <table className="min-w-full text-left text-gray-300">
                        <thead className="bg-gray-700 text-gray-400 uppercase text-xs">
                            <tr>
                                <th className="px-6 py-3">Name</th>
                                <th className="px-6 py-3">SendGrid ID</th>
                                <th className="px-6 py-3">Description</th>
                                <th className="px-6 py-3">Actions</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-gray-700">
                            {templates.map((template) => (
                                <tr key={template.id} className="hover:bg-gray-750">
                                    <td className="px-6 py-4 font-medium text-white">{template.name}</td>
                                    <td className="px-6 py-4 font-mono text-sm text-blue-300">{template.template_id}</td>
                                    <td className="px-6 py-4">{template.description || '-'}</td>
                                    <td className="px-6 py-4">
                                        <button className="text-red-400 hover:text-red-300 text-sm">Remove</button>
                                    </td>
                                </tr>
                            ))}
                            {templates.length === 0 && (
                                <tr>
                                    <td colSpan="4" className="text-center py-6 text-gray-500">
                                        No templates registered yet.
                                    </td>
                                </tr>
                            )}
                        </tbody>
                    </table>
                </div>
            )}

            {/* Add Template Modal */}
            {showAddModal && (
                <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4">
                    <div className="bg-gray-800 rounded-lg p-6 w-full max-w-md border border-gray-700">
                        <h3 className="text-xl font-bold mb-4 text-white">Register Template</h3>
                        <form onSubmit={handleRegister}>
                            <div className="mb-4">
                                <label className="block text-gray-400 mb-1">Template Name</label>
                                <input
                                    type="text"
                                    className="w-full bg-gray-700 text-white rounded p-2 border border-gray-600"
                                    value={newTemplate.name}
                                    onChange={e => setNewTemplate({ ...newTemplate, name: e.target.value })}
                                    required
                                    placeholder="e.g. Validation Notice v1"
                                />
                            </div>
                            <div className="mb-4">
                                <label className="block text-gray-400 mb-1">SendGrid Template ID</label>
                                <input
                                    type="text"
                                    className="w-full bg-gray-700 text-white rounded p-2 border border-gray-600 font-mono"
                                    value={newTemplate.template_id}
                                    onChange={e => setNewTemplate({ ...newTemplate, template_id: e.target.value })}
                                    required
                                    placeholder="d-xxxxxxxx..."
                                />
                                <p className="text-xs text-gray-500 mt-1">Found in SendGrid Design Library</p>
                            </div>
                            <div className="mb-6">
                                <label className="block text-gray-400 mb-1">Description</label>
                                <textarea
                                    className="w-full bg-gray-700 text-white rounded p-2 border border-gray-600"
                                    value={newTemplate.description}
                                    onChange={e => setNewTemplate({ ...newTemplate, description: e.target.value })}
                                    placeholder="Optional notes..."
                                />
                            </div>
                            <div className="flex justify-end space-x-3">
                                <button
                                    type="button"
                                    onClick={() => setShowAddModal(false)}
                                    className="px-4 py-2 text-gray-300 hover:text-white"
                                >
                                    Cancel
                                </button>
                                <button
                                    type="submit"
                                    className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded"
                                >
                                    Register
                                </button>
                            </div>
                        </form>
                    </div>
                </div>
            )}
        </div>
    );
};

export default TemplateManager;
