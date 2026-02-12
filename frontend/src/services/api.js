import { supabase } from "./supabase";

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

async function apiFetch(path, options = {}) {
    const session = (await supabase.auth.getSession()).data.session;

    // DEBUG: Log session state
    console.log('[API] Request to:', path);
    console.log('[API] Session exists:', !!session);
    console.log('[API] Token exists:', !!session?.access_token);

    const headers = {
        ...(options.headers || {}),
    };

    if (session?.access_token) {
        headers.Authorization = `Bearer ${session.access_token}`;
        console.log('[API] Authorization header added');
    } else {
        console.warn('[API] No access token available - request will fail auth');
    }

    if (options.body && !(options.body instanceof FormData)) {
        headers["Content-Type"] = headers["Content-Type"] || "application/json";
    }

    console.log('[API] Request headers:', Object.keys(headers));
    console.log('[API] Request method:', options.method || 'GET');

    const response = await fetch(`${API_URL}${path}`, {
        ...options,
        headers,
    });

    console.log('[API] Response status:', response.status, response.statusText);

    if (!response.ok) {
        let errDetail = "Request failed";
        try {
            const err = await response.clone().json();
            errDetail = err.detail || err.message || errDetail;
            console.error('[API] Error response:', err);
        } catch (_) {
            errDetail = await response.text();
            console.error('[API] Error text:', errDetail);
        }
        throw new Error(errDetail);
    }

    const result = await response.json();
    // console.log('[API] Success response:', result); // Reduced logging for security
    return result;
}

export async function fetchWorkQueue() {
    return apiFetch("/api/v1/work-queue");
}

export async function fetchDebtDetails(debtId) {
    return apiFetch(`/api/v1/debts/${debtId}`);
}

export async function fetchDebtInteractions(debtId) {
    return apiFetch(`/api/v1/debts/${debtId}/interactions`);
}

export async function logInteraction(debtId, actionType, notes = "") {
    return apiFetch("/api/v1/interactions", {
        method: "POST",
        body: JSON.stringify({
            debt_id: debtId,
            action_type: actionType,
            notes: notes,
        }),
    });
}

export async function uploadPortfolio(file, portfolioId) {
    const formData = new FormData();
    formData.append("file", file);
    if (portfolioId) {
        formData.append("portfolio_id", String(portfolioId));
    }
    return apiFetch("/api/v1/upload", {
        method: "POST",
        body: formData,
    });
}

export async function processPayment(debtId, amount) {
    return apiFetch("/api/v1/payments", {
        method: "POST",
        body: JSON.stringify({
            debt_id: debtId,
            amount_paid: amount,
        }),
    });
}

export async function searchDebts(searchType, query) {
    return apiFetch(`/api/v1/search?search_type=${searchType}&query=${encodeURIComponent(query)}`);
}

export async function fetchPaymentPlans(debtId) {
    return apiFetch(`/api/v1/payment-plans/${debtId}`);
}

export async function fetchPlanSchedule(planId) {
    return apiFetch(`/api/v1/payment-plans/${planId}/schedule`);
}

export async function runOneOffPayment(debtId, amount) {
    return apiFetch(`/api/v1/payments/one-off?debt_id=${debtId}&amount=${amount}`, {
        method: "POST",
    });
}

export async function executeScheduledPayment(paymentId) {
    return apiFetch(`/api/v1/payments/scheduled/${paymentId}/execute`, {
        method: "POST",
    });
}

export async function fetchAdminPayments({ status = null, days = 0, startDate = null, endDate = null } = {}) {
    let url = `${API_URL}/api/v1/admin/payments?days=${days}`;
    if (status) url += `&status=${status}`;
    if (startDate) url += `&start_date=${encodeURIComponent(startDate)}`;
    if (endDate) url += `&end_date=${encodeURIComponent(endDate)}`;
    return apiFetch(url.replace(API_URL, ""));
}

export async function fetchDebtPayments(debtId) {
    return apiFetch(`/api/v1/payments/${debtId}`);
}

export async function fetchDailyMoneyReport(date = null) {
    let url = `${API_URL}/api/v1/reports/daily-money`;
    if (date) {
        url += `?date=${encodeURIComponent(date)}`;
    }
    return apiFetch(url.replace(API_URL, ""));
}

export async function fetchLiquidationReport(portfolioId = null) {
    let url = `${API_URL}/api/v1/reports/liquidation`;
    if (portfolioId) {
        url += `?portfolio_id=${encodeURIComponent(portfolioId)}`;
    }
    return apiFetch(url.replace(API_URL, ""));
}

export async function fetchPortfolios() {
    return apiFetch("/api/v1/portfolios");
}

export async function fetchIngestJob(jobId) {
    return apiFetch(`/api/v1/ingest/jobs/${jobId}`);
}

export async function fetchCampaignTemplates() {
    return apiFetch("/api/v1/campaigns/templates");
}

export async function registerCampaignTemplate(payload) {
    return apiFetch("/api/v1/campaigns/templates", {
        method: "POST",
        body: JSON.stringify(payload),
    });
}

export async function previewCampaignAudience(filters) {
    return apiFetch("/api/v1/campaigns/preview", {
        method: "POST",
        body: JSON.stringify(filters),
    });
}

export async function launchCampaign(payload) {
    return apiFetch("/api/v1/campaigns/launch", {
        method: "POST",
        body: JSON.stringify(payload),
    });
}

export async function fetchCampaigns() {
    return apiFetch("/api/v1/campaigns");
}

export async function sendAgentEmail(debtId, templateId) {
    return apiFetch("/api/v1/email/send", {
        method: "POST",
        body: JSON.stringify({
            debt_id: debtId,
            template_id: templateId,
        }),
    });
}

export async function updateDebtorEmail(debtId, email) {
    console.log('[updateDebtorEmail] Called with:', { debtId, email });
    return apiFetch(`/api/v1/debts/${debtId}/email`, {
        method: "PUT",
        body: JSON.stringify({ email }),
    });
}

export async function sendValidationNotice(debtId, pdfUrl) {
    return apiFetch("/api/v1/validation/send", {
        method: "POST",
        body: JSON.stringify({
            debt_id: debtId,
            pdf_url: pdfUrl,
        }),
    });
}
