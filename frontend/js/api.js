/**
 * API Client
 *
 * Fetch-based HTTP client for all backend API calls.
 * Automatically attaches JWT token and handles errors.
 */

const API_BASE_URL = 'http://localhost:8000/api/v1';

const api = {
    /**
     * Make an authenticated API request.
     * @param {string} endpoint - API endpoint path (e.g., '/auth/login')
     * @param {object} options - Fetch options
     * @returns {Promise<object>} Parsed JSON response
     */
    async request(endpoint, options = {}) {
        const url = `${API_BASE_URL}${endpoint}`;
        const token = Auth.getToken();

        const headers = {
            ...options.headers,
        };

        // Add auth header if token exists
        if (token) {
            headers['Authorization'] = `Bearer ${token}`;
        }

        // Add Content-Type for JSON requests (not FormData)
        if (options.body && !(options.body instanceof FormData)) {
            headers['Content-Type'] = 'application/json';
        }

        try {
            const response = await fetch(url, {
                ...options,
                headers,
            });

            // Handle auth errors
            if (response.status === 401) {
                Auth.clearAuth();
                window.location.href = 'index.html';
                throw new Error('Session expired. Please login again.');
            }

            // Parse response
            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.detail || `Request failed (${response.status})`);
            }

            return data;
        } catch (error) {
            if (error.name === 'TypeError' && error.message.includes('fetch')) {
                throw new Error('Unable to connect to server. Is the backend running?');
            }
            throw error;
        }
    },

    // ---- Auth ----
    async register(name, email, password, role) {
        return this.request('/auth/register', {
            method: 'POST',
            body: JSON.stringify({ name, email, password, role }),
        });
    },

    async login(email, password) {
        return this.request('/auth/login', {
            method: 'POST',
            body: JSON.stringify({ email, password }),
        });
    },

    // ---- Upload ----
    async uploadDocument(formData) {
        return this.request('/upload/', {
            method: 'POST',
            body: formData,
        });
    },

    // ---- Processing ----
    async processDocument(documentId) {
        return this.request('/process/', {
            method: 'POST',
            body: JSON.stringify({ document_id: documentId }),
        });
    },

    // ---- Evaluation ----
    async evaluateDocument(documentId, maxMarks = 10) {
        return this.request('/evaluate/', {
            method: 'POST',
            body: JSON.stringify({
                document_id: documentId,
                max_marks_per_question: maxMarks,
            }),
        });
    },

    // ---- Results ----
    async getResults() {
        return this.request('/results/');
    },

    async getMyResults() {
        return this.request('/results/my-results');
    },

    async getEvaluationDetail(evaluationId) {
        return this.request(`/results/${evaluationId}`);
    },

    async getDashboardStats() {
        return this.request('/results/dashboard');
    },

    // ---- Knowledge Base ----
    async ingestKnowledge(formData) {
        return this.request('/knowledge/ingest', {
            method: 'POST',
            body: formData,
        });
    },

    async getKnowledgeDocuments() {
        return this.request('/knowledge/');
    },
};
