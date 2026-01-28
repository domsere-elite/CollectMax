const API_URL = "http://localhost:8000";

export async function fetchWorkQueue() {
    const response = await fetch(`${API_URL}/api/v1/work-queue`);
    if (!response.ok) throw new Error("Failed to fetch work queue");
    return response.json();
}

export async function logInteraction(debtId, actionType, notes = "") {
    const response = await fetch(`${API_URL}/api/v1/interactions`, {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
        },
        body: JSON.stringify({
            debt_id: debtId,
            action_type: actionType,
            notes: notes,
        }),
    });

    if (!response.ok) {
        const err = await response.json();
        throw new Error(err.detail || "Failed to log interaction");
    }
    return response.json();
}

export async function uploadPortfolio(file) {
    const formData = new FormData();
    formData.append("file", file);

    const response = await fetch(`${API_URL}/api/v1/upload`, {
        method: "POST",
        body: formData,
    });

    if (!response.ok) throw new Error("Failed to upload portfolio");
    return response.json();
}

export async function processPayment(debtId, amount) {
    const response = await fetch(`${API_URL}/api/v1/payments`, {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
        },
        body: JSON.stringify({
            debt_id: debtId,
            amount_paid: amount,
        }),
    });

    if (!response.ok) throw new Error("Payment Failed");
    return response.json();
}

export async function searchDebts(searchType, query) {
    const response = await fetch(`${API_URL}/api/v1/search?search_type=${searchType}&query=${encodeURIComponent(query)}`);
    if (!response.ok) throw new Error("Search Failed");
    return response.json();
}

export async function fetchPaymentPlans(debtId) {
    const response = await fetch(`${API_URL}/api/v1/payment-plans/${debtId}`);
    if (!response.ok) throw new Error("Failed to fetch payment plans");
    return response.json();
}

export async function fetchPlanSchedule(planId) {
    const response = await fetch(`${API_URL}/api/v1/payment-plans/${planId}/schedule`);
    if (!response.ok) throw new Error("Failed to fetch plan schedule");
    return response.json();
}

export async function runOneOffPayment(debtId, amount) {
    const response = await fetch(`${API_URL}/api/v1/payments/one-off?debt_id=${debtId}&amount=${amount}`, {
        method: "POST"
    });
    if (!response.ok) {
        const err = await response.json();
        throw new Error(err.detail || "One-off Payment Failed");
    }
    return response.json();
}

export async function executeScheduledPayment(paymentId) {
    const response = await fetch(`${API_URL}/api/v1/payments/scheduled/${paymentId}/execute`, {
        method: "POST"
    });
    if (!response.ok) {
        const err = await response.json();
        throw new Error(err.detail || "Execution Failed");
    }
    return response.json();
}

export async function fetchAdminPayments(status = null, days = 0) {
    let url = `${API_URL}/api/v1/admin/payments?days=${days}`;
    if (status) url += `&status=${status}`;

    const response = await fetch(url);
    if (!response.ok) throw new Error("Failed to fetch admin payments");
    return response.json();
}

export async function fetchDebtPayments(debtId) {
    const response = await fetch(`${API_URL}/api/v1/payments/${debtId}`);
    if (!response.ok) throw new Error("Failed to fetch payments");
    return response.json();
}
