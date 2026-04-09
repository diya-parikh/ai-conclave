// API Configuration and Utility Functions
const API_BASE = 'http://localhost:8000/api/v1';

// Setup Axios-like fetch wrapper
const api = {
    async request(endpoint, options = {}) {
        const token = localStorage.getItem('token');
        const headers = {
            'Accept': 'application/json',
            ...(options.headers || {})
        };

        if (token) {
            headers['Authorization'] = `Bearer ${token}`;
        }

        if (!(options.body instanceof FormData)) {
            headers['Content-Type'] = 'application/json';
            if (options.body && typeof options.body === 'object') {
                options.body = JSON.stringify(options.body);
            }
        }

        try {
            const response = await fetch(`${API_BASE}${endpoint}`, {
                ...options,
                headers
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.detail || data.message || 'API Request Failed');
            }

            return data;
        } catch (error) {
            console.error('API Error:', error);
            throw error;
        }
    },

    get(endpoint) { return this.request(endpoint, { method: 'GET' }); },
    post(endpoint, body) { return this.request(endpoint, { method: 'POST', body }); },
    upload(endpoint, formData) { return this.request(endpoint, { method: 'POST', body: formData }); }
};

function logout() {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    window.location.href = '/';
}

// Redirect if unauthenticated or wrong role
function checkAuth(requiredRole = null) {
    const token = localStorage.getItem('token');
    const userStr = localStorage.getItem('user');

    if (!token || !userStr) {
        window.location.href = '/';
        return null;
    }

    const user = JSON.parse(userStr);
    
    if (requiredRole && user.role !== requiredRole) {
        window.location.href = user.role === 'teacher' ? 'teacher.html' : 'student.html';
        return null;
    }

    // Update UI elements if present
    const nameEl = document.getElementById('display-name');
    const roleEl = document.getElementById('display-role');
    if(nameEl) nameEl.textContent = user.name;
    if(roleEl) roleEl.textContent = user.role;

    return user;
}
