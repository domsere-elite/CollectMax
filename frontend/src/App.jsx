import React from 'react';
import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom';
import AgentDashboard from './components/AgentDashboard';
import AdminDashboard from './components/AdminDashboard';

function App() {
    return (
        <Router>
            <div className="min-h-screen bg-gray-900 text-white font-sans">
                <nav className="p-4 bg-gray-800 border-b border-gray-700 flex justify-between items-center">
                    <div className="text-xl font-bold tracking-wider text-blue-500">CollectSecure</div>
                    <div className="space-x-4">
                        <Link to="/agent" className="hover:text-blue-400">Agent View</Link>
                        <Link to="/admin" className="hover:text-blue-400">Admin View</Link>
                    </div>
                </nav>

                <main className="p-6">
                    <Routes>
                        <Route path="/agent" element={<AgentDashboard />} />
                        <Route path="/admin" element={<AdminDashboard />} />
                        <Route path="/" element={
                            <div className="text-center mt-20">
                                <h1 className="text-4xl font-bold text-gray-200">Welcome to CollectSecure</h1>
                                <p className="mt-4 text-gray-400">Select a portal to begin.</p>
                            </div>
                        } />
                    </Routes>
                </main>
            </div>
        </Router>
    );
}

export default App;
