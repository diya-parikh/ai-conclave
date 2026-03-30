/**
 * Utility Functions
 *
 * Shared helpers for DOM manipulation, date formatting,
 * local storage, and toast notifications.
 */

// ---- Local Storage Helpers ----
const Storage = {
    get(key) {
        try {
            const item = localStorage.getItem(key);
            return item ? JSON.parse(item) : null;
        } catch {
            return null;
        }
    },
    set(key, value) {
        localStorage.setItem(key, JSON.stringify(value));
    },
    remove(key) {
        localStorage.removeItem(key);
    },
    clear() {
        localStorage.clear();
    },
};

// ---- Auth Storage ----
const Auth = {
    getToken() {
        return Storage.get('auth_token');
    },
    getUser() {
        return Storage.get('auth_user');
    },
    setAuth(token, user) {
        Storage.set('auth_token', token);
        Storage.set('auth_user', user);
    },
    clearAuth() {
        Storage.remove('auth_token');
        Storage.remove('auth_user');
    },
    isLoggedIn() {
        return !!this.getToken();
    },
    getRole() {
        const user = this.getUser();
        return user ? user.role : null;
    },
};

// ---- Date Formatting ----
function formatDate(dateString) {
    if (!dateString) return '—';
    const date = new Date(dateString);
    return date.toLocaleDateString('en-IN', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
    });
}

function formatDateTime(dateString) {
    if (!dateString) return '—';
    const date = new Date(dateString);
    return date.toLocaleDateString('en-IN', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
    });
}

function timeAgo(dateString) {
    if (!dateString) return '—';
    const now = new Date();
    const date = new Date(dateString);
    const diff = Math.floor((now - date) / 1000);

    if (diff < 60) return 'Just now';
    if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
    if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`;
    if (diff < 604800) return `${Math.floor(diff / 86400)}d ago`;
    return formatDate(dateString);
}

// ---- File Size Formatting ----
function formatFileSize(bytes) {
    if (!bytes) return '0 B';
    const units = ['B', 'KB', 'MB', 'GB'];
    let size = bytes;
    let unitIndex = 0;
    while (size >= 1024 && unitIndex < units.length - 1) {
        size /= 1024;
        unitIndex++;
    }
    return `${size.toFixed(1)} ${units[unitIndex]}`;
}

// ---- DOM Helpers ----
function $(selector) {
    return document.querySelector(selector);
}

function $$(selector) {
    return document.querySelectorAll(selector);
}

function createElement(tag, attrs = {}, children = []) {
    const el = document.createElement(tag);
    Object.entries(attrs).forEach(([key, val]) => {
        if (key === 'className') el.className = val;
        else if (key === 'innerHTML') el.innerHTML = val;
        else if (key === 'textContent') el.textContent = val;
        else if (key.startsWith('on')) el.addEventListener(key.slice(2).toLowerCase(), val);
        else el.setAttribute(key, val);
    });
    children.forEach(child => {
        if (typeof child === 'string') el.appendChild(document.createTextNode(child));
        else el.appendChild(child);
    });
    return el;
}

// ---- Toast Notifications ----
function showToast(message, type = 'info', duration = 4000) {
    const container = document.getElementById('toast-container');
    if (!container) return;

    const toast = createElement('div', {
        className: `toast toast-${type}`,
        innerHTML: `
            <span>${type === 'success' ? '✅' : type === 'error' ? '❌' : 'ℹ️'}</span>
            <span style="flex:1; font-size: 0.875rem;">${message}</span>
        `,
    });

    container.appendChild(toast);

    setTimeout(() => {
        toast.style.animation = 'slideOutRight 0.3s forwards';
        setTimeout(() => toast.remove(), 300);
    }, duration);
}

// ---- Grade Helpers ----
function getGradeClass(grade) {
    if (!grade) return 'grade-F';
    const letter = grade.charAt(0).toUpperCase();
    return `grade-${letter}`;
}

function getStatusBadge(status) {
    const statusMap = {
        uploaded: { class: 'badge-info', label: 'Uploaded' },
        processing: { class: 'badge-warning', label: 'Processing' },
        processed: { class: 'badge-primary', label: 'Processed' },
        evaluating: { class: 'badge-warning', label: 'Evaluating' },
        completed: { class: 'badge-success', label: 'Completed' },
        failed: { class: 'badge-danger', label: 'Failed' },
        pending: { class: 'badge-info', label: 'Pending' },
    };
    const config = statusMap[status] || { class: 'badge-info', label: status };
    return `<span class="badge ${config.class}">${config.label}</span>`;
}

// ---- Redirect Helpers ----
function requireAuth() {
    if (!Auth.isLoggedIn()) {
        window.location.href = 'index.html';
        return false;
    }
    return true;
}

function logout() {
    Auth.clearAuth();
    window.location.href = 'index.html';
}
