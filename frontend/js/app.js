/**
 * App Initialization & Navigation
 *
 * Handles page switching, sidebar navigation, user info display,
 * and initial data loading for both teacher and student dashboards.
 */

document.addEventListener('DOMContentLoaded', () => {
    // Require authentication
    if (!requireAuth()) return;

    const user = Auth.getUser();
    const role = user ? user.role : null;

    // ---- Set User Info in Sidebar ----
    const userAvatar = $('#user-avatar');
    const userName = $('#user-name');

    if (user && userAvatar && userName) {
        userAvatar.textContent = user.name.charAt(0).toUpperCase();
        userName.textContent = user.name;
    }

    // ---- Logout ----
    const logoutBtn = $('#logout-btn');
    if (logoutBtn) {
        logoutBtn.addEventListener('click', () => {
            logout();
        });
    }

    // ---- Mobile Menu ----
    const mobileMenuBtn = $('#mobile-menu-btn');
    const sidebar = $('#sidebar');
    if (mobileMenuBtn && sidebar) {
        mobileMenuBtn.addEventListener('click', () => {
            sidebar.classList.toggle('open');
        });
    }

    // ---- Page Navigation (Teacher) ----
    if (role === 'teacher') {
        const navItems = $$('.nav-item[data-page]');
        const pages = $$('.page-section');

        function switchPage(pageName) {
            // Hide all pages
            pages.forEach(p => p.style.display = 'none');

            // Show target page
            const targetPage = $(`#page-${pageName}`);
            if (targetPage) {
                targetPage.style.display = 'block';
            }

            // Update nav active state
            navItems.forEach(item => item.classList.remove('active'));
            const activeNav = $(`.nav-item[data-page="${pageName}"]`);
            if (activeNav) activeNav.classList.add('active');

            // Close mobile menu
            if (sidebar) sidebar.classList.remove('open');

            // Load data for the page
            loadPageData(pageName);
        }

        navItems.forEach(item => {
            item.addEventListener('click', (e) => {
                e.preventDefault();
                const page = item.dataset.page;
                switchPage(page);
                window.location.hash = page;
            });
        });

        // Handle hash-based routing
        const hash = window.location.hash.slice(1) || 'dashboard';
        switchPage(hash);

        // Load initial data
        if (typeof loadDashboard === 'function') {
            loadDashboard();
        }
    }

    // ---- Student Page ----
    if (role === 'student') {
        if (typeof loadStudentResults === 'function') {
            loadStudentResults();
        }
    }

    // ---- Modal Close ----
    const closeModal = $('#close-modal');
    const evalModal = $('#eval-modal');
    if (closeModal && evalModal) {
        closeModal.addEventListener('click', () => {
            evalModal.classList.remove('active');
        });
        evalModal.addEventListener('click', (e) => {
            if (e.target === evalModal) {
                evalModal.classList.remove('active');
            }
        });
    }
});

/**
 * Load data for a specific page.
 */
function loadPageData(pageName) {
    switch (pageName) {
        case 'dashboard':
            if (typeof loadDashboard === 'function') loadDashboard();
            break;
        case 'results':
            if (typeof loadTeacherResults === 'function') loadTeacherResults();
            break;
        case 'upload':
            // Upload page is initialized by upload.js
            break;
        case 'knowledge':
            if (typeof loadKnowledgeDocuments === 'function') loadKnowledgeDocuments();
            break;
    }
}
