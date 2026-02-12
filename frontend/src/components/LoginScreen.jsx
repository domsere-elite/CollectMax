import React, { useEffect, useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { useAuth } from "../auth/AuthProvider";

const LoginScreen = () => {
    const { session, authLoading, authError, setAuthError, signIn } = useAuth();
    const [email, setEmail] = useState("");
    const [password, setPassword] = useState("");
    const navigate = useNavigate();
    const location = useLocation();
    const redirectTo = location.state?.from || "/agent";

    useEffect(() => {
        if (!authLoading && session) {
            navigate(redirectTo, { replace: true });
        }
    }, [authLoading, navigate, redirectTo, session]);

    const handleSignIn = async (e) => {
        e.preventDefault();
        await signIn(email, password);
    };

    return (
        <div className="min-h-[70vh] flex items-center justify-center bg-white">
            <div className="w-full max-w-md bg-white border border-slate-200 rounded-2xl p-8 shadow-xl">
                <div className="text-center mb-6">
                    <div className="text-2xl font-bold text-slate-900 tracking-wider">CollectSecure</div>
                    <div className="text-sm text-slate-500 mt-1">Sign in to continue</div>
                </div>
                <form onSubmit={handleSignIn} className="space-y-4">
                    <input
                        type="email"
                        placeholder="Email"
                        value={email}
                        onChange={(e) => {
                            setEmail(e.target.value);
                            if (authError) setAuthError("");
                        }}
                        className="w-full px-3 py-2 rounded-md bg-white border border-slate-300 text-sm text-slate-900 placeholder:text-slate-400 focus:outline-none focus:border-blue-500/60"
                        required
                    />
                    <input
                        type="password"
                        placeholder="Password"
                        value={password}
                        onChange={(e) => {
                            setPassword(e.target.value);
                            if (authError) setAuthError("");
                        }}
                        className="w-full px-3 py-2 rounded-md bg-white border border-slate-300 text-sm text-slate-900 placeholder:text-slate-400 focus:outline-none focus:border-blue-500/60"
                        required
                    />
                    <button
                        type="submit"
                        disabled={authLoading}
                        className="w-full px-3 py-2 rounded-md bg-blue-600 hover:bg-blue-500 transition text-sm font-semibold text-white"
                    >
                        {authLoading ? "Signing in..." : "Sign in"}
                    </button>
                </form>
                {authError ? (
                    <div className="text-sm text-rose-600 mt-4 text-center">{authError}</div>
                ) : null}
            </div>
        </div>
    );
};

export default LoginScreen;
