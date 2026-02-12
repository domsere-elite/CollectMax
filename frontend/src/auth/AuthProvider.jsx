import React, { createContext, useContext, useEffect, useState } from "react";
import { supabase } from "../services/supabase";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
    const [session, setSession] = useState(null);
    const [authLoading, setAuthLoading] = useState(true);
    const [authError, setAuthError] = useState("");

    useEffect(() => {
        let mounted = true;

        supabase.auth.getSession().then(({ data }) => {
            if (!mounted) return;
            setSession(data.session || null);
            setAuthLoading(false);
        });

        const { data: listener } = supabase.auth.onAuthStateChange((_event, newSession) => {
            if (!mounted) return;
            setSession(newSession || null);
            if (!newSession) {
                localStorage.removeItem("agent.currentDebt");
            }
        });

        return () => {
            mounted = false;
            listener?.subscription?.unsubscribe();
        };
    }, []);

    const signIn = async (email, password) => {
        setAuthError("");
        setAuthLoading(true);
        const { error } = await supabase.auth.signInWithPassword({ email, password });
        if (error) {
            setAuthError(error.message || "Failed to sign in.");
        }
        setAuthLoading(false);
        return { error };
    };

    const signOut = async () => {
        setAuthError("");
        setAuthLoading(true);
        const { error } = await supabase.auth.signOut();
        if (error) {
            setAuthError(error.message || "Failed to sign out.");
        }
        setAuthLoading(false);
        return { error };
    };

    return (
        <AuthContext.Provider
            value={{ session, authLoading, authError, setAuthError, signIn, signOut }}
        >
            {children}
        </AuthContext.Provider>
    );
}

export function useAuth() {
    const context = useContext(AuthContext);
    if (!context) {
        throw new Error("useAuth must be used within an AuthProvider");
    }
    return context;
}
