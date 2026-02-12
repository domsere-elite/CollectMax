import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../auth/AuthProvider";

const AuthPanel = () => {
    const { session, authLoading, authError, setAuthError, signIn, signOut } = useAuth();
    const [email, setEmail] = useState("");
    const [password, setPassword] = useState("");
    const navigate = useNavigate();

    const handleSignIn = async (e) => {
        e.preventDefault();
        await signIn(email, password);
    };

    const handleSignOut = async () => {
        const { error } = await signOut();
        if (!error) {
            navigate("/login", { replace: true });
        }
    };

    return (
        <div className="flex flex-col sm:flex-row sm:items-center gap-3">
            {session ? (
                <div className="flex items-center gap-3">
                    <span className="text-sm text-slate-300">Signed in as</span>
                    <span className="text-sm font-semibold text-white">{session.user?.email}</span>
                    <button
                        type="button"
                        onClick={handleSignOut}
                        disabled={authLoading}
                        className="px-3 py-1 rounded-md bg-slate-700/70 hover:bg-slate-600 transition"
                    >
                        Sign out
                    </button>
                </div>
            ) : (
                <form onSubmit={handleSignIn} className="flex flex-wrap items-center gap-2">
                    <input
                        type="email"
                        placeholder="email"
                        value={email}
                        onChange={(e) => {
                            setEmail(e.target.value);
                            if (authError) setAuthError("");
                        }}
                        className="px-3 py-2 rounded-md bg-slate-800 border border-slate-700 text-sm text-white placeholder:text-slate-500"
                        required
                    />
                    <input
                        type="password"
                        placeholder="password"
                        value={password}
                        onChange={(e) => {
                            setPassword(e.target.value);
                            if (authError) setAuthError("");
                        }}
                        className="px-3 py-2 rounded-md bg-slate-800 border border-slate-700 text-sm text-white placeholder:text-slate-500"
                        required
                    />
                    <button
                        type="submit"
                        disabled={authLoading}
                        className="px-3 py-2 rounded-md bg-blue-600 hover:bg-blue-500 transition text-sm font-semibold"
                    >
                        Sign in
                    </button>
                </form>
            )}
            {authError ? <span className="text-sm text-rose-400">{authError}</span> : null}
        </div>
    );
};

export default AuthPanel;
