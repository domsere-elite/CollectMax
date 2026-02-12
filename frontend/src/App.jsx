import React from "react";
import { BrowserRouter as Router, Routes, Route, Link, Navigate, useLocation } from "react-router-dom";
import AgentDashboard from "./components/AgentDashboard";
import AdminDashboard from "./components/AdminDashboard";
import AuthPanel from "./components/AuthPanel";
import LoginScreen from "./components/LoginScreen";
import { useAuth } from "./auth/AuthProvider";

import CampaignDashboard from "./components/communications/CampaignDashboard";
import CampaignWizard from "./components/communications/CampaignWizard";
import TemplateManager from "./components/communications/TemplateManager";

const RequireAuth = ({ children }) => {
    const { session, authLoading } = useAuth();
    const location = useLocation();

    if (authLoading) {
        return (
            <div className="text-center mt-20 text-slate-300">
                Checking session...
            </div>
        );
    }

    if (!session) {
        return <Navigate to="/login" replace state={{ from: location.pathname }} />;
    }

    return children;
};

function App() {
    const { session } = useAuth();

    return (
        <Router>
            <div className="min-h-screen bg-gray-900 text-white font-sans">
                <nav className="p-4 bg-gray-800 border-b border-gray-700 flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
                    <div className="flex items-center justify-between gap-6">
                        <div className="text-xl font-bold tracking-wider text-blue-500">CollectSecure</div>
                        <div className="space-x-4 text-sm">
                            {session ? (
                                <>
                                    <Link to="/agent" className="hover:text-blue-400">Agent View</Link>
                                    <Link to="/admin" className="hover:text-blue-400">Admin View</Link>
                                    <Link to="/communications" className="hover:text-blue-400">Campaigns</Link>
                                </>
                            ) : (
                                <Link to="/login" className="hover:text-blue-400">Sign in</Link>
                            )}
                        </div>
                    </div>
                    <AuthPanel />
                </nav>

                <main className="p-6">
                    <Routes>
                        <Route path="/login" element={<LoginScreen />} />
                        <Route path="/agent" element={<RequireAuth><AgentDashboard /></RequireAuth>} />
                        <Route path="/admin" element={<RequireAuth><AdminDashboard /></RequireAuth>} />
                        <Route path="/communications" element={<RequireAuth><CampaignDashboard /></RequireAuth>} />
                        <Route path="/communications/new" element={<RequireAuth><CampaignWizard /></RequireAuth>} />
                        <Route path="/communications/templates" element={<RequireAuth><TemplateManager /></RequireAuth>} />
                        <Route path="/" element={session ? (
                            <div className="text-center mt-20">
                                <h1 className="text-4xl font-bold text-gray-200">Welcome to CollectSecure</h1>
                                <p className="mt-4 text-gray-400">Select a portal to begin.</p>
                            </div>
                        ) : (
                            <Navigate to="/login" replace />
                        )} />
                    </Routes>
                </main>
            </div>
        </Router>
    );
}

export default App;
