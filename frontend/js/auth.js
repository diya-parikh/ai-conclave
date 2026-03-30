/**
 * Auth Page Logic
 *
 * Handles login and registration for both teacher and student roles.
 * Redirects to appropriate dashboard after successful auth.
 */

document.addEventListener('DOMContentLoaded', () => {
    // If already logged in, redirect to dashboard
    if (Auth.isLoggedIn()) {
        const role = Auth.getRole();
        window.location.href = role === 'teacher' ? 'teacher.html' : 'student.html';
        return;
    }

    let isLoginMode = true;
    let selectedRole = 'teacher';

    // ---- Role Toggle ----
    const toggleTeacher = $('#toggle-teacher');
    const toggleStudent = $('#toggle-student');

    toggleTeacher.addEventListener('click', () => {
        selectedRole = 'teacher';
        toggleTeacher.classList.add('active');
        toggleStudent.classList.remove('active');
    });

    toggleStudent.addEventListener('click', () => {
        selectedRole = 'student';
        toggleStudent.classList.add('active');
        toggleTeacher.classList.remove('active');
    });

    // ---- Auth Mode Toggle ----
    const loginForm = $('#login-form');
    const registerForm = $('#register-form');
    const modeLink = $('#auth-mode-link');
    const modeText = $('#auth-mode-text');

    modeLink.addEventListener('click', (e) => {
        e.preventDefault();
        isLoginMode = !isLoginMode;

        if (isLoginMode) {
            loginForm.style.display = 'block';
            registerForm.style.display = 'none';
            modeText.textContent = "Don't have an account?";
            modeLink.textContent = 'Create one';
        } else {
            loginForm.style.display = 'none';
            registerForm.style.display = 'block';
            modeText.textContent = 'Already have an account?';
            modeLink.textContent = 'Sign in';
        }
    });

    // ---- Login ----
    loginForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const email = $('#login-email').value.trim();
        const password = $('#login-password').value;
        const btn = $('#login-btn');

        btn.disabled = true;
        btn.innerHTML = '<div class="spinner"></div> Signing in...';

        try {
            const data = await api.login(email, password);
            Auth.setAuth(data.access_token, data.user);
            showToast(`Welcome back, ${data.user.name}!`, 'success');

            setTimeout(() => {
                window.location.href = data.user.role === 'teacher' ? 'teacher.html' : 'student.html';
            }, 500);
        } catch (error) {
            showToast(error.message, 'error');
            btn.disabled = false;
            btn.textContent = 'Sign In';
        }
    });

    // ---- Register ----
    registerForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const name = $('#register-name').value.trim();
        const email = $('#register-email').value.trim();
        const password = $('#register-password').value;
        const btn = $('#register-btn');

        btn.disabled = true;
        btn.innerHTML = '<div class="spinner"></div> Creating account...';

        try {
            const data = await api.register(name, email, password, selectedRole);
            Auth.setAuth(data.access_token, data.user);
            showToast(`Welcome, ${data.user.name}! Account created.`, 'success');

            setTimeout(() => {
                window.location.href = data.user.role === 'teacher' ? 'teacher.html' : 'student.html';
            }, 500);
        } catch (error) {
            showToast(error.message, 'error');
            btn.disabled = false;
            btn.textContent = 'Create Account';
        }
    });
});
