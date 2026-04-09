let currentMode = 'login';

function toggleAuthMode(mode) {
    currentMode = mode;
    document.getElementById('btn-login').classList.toggle('active', mode === 'login');
    document.getElementById('btn-register').classList.toggle('active', mode === 'register');
    
    document.getElementById('group-name').style.display = mode === 'register' ? 'block' : 'none';
    document.getElementById('group-role').style.display = mode === 'register' ? 'block' : 'none';
    
    document.getElementById('submit-btn').textContent = mode === 'login' ? 'Sign In' : 'Create Account';
    document.getElementById('auth-error').textContent = '';
    
    // Clear inputs if switching
    if(mode === 'login') {
        document.getElementById('name').removeAttribute('required');
    } else {
        document.getElementById('name').setAttribute('required', 'true');
    }
}

async function handleAuth(event) {
    event.preventDefault();
    const errorEl = document.getElementById('auth-error');
    const btn = document.getElementById('submit-btn');
    
    errorEl.textContent = '';
    btn.disabled = true;
    btn.textContent = 'Processing...';

    const email = document.getElementById('email').value;
    const password = document.getElementById('password').value;

    try {
        let response;
        if (currentMode === 'login') {
            response = await api.post('/auth/login', { email, password });
        } else {
            const name = document.getElementById('name').value;
            const role = document.querySelector('input[name="role"]:checked').value;
            response = await api.post('/auth/register', { name, email, password, role });
        }

        // Store auth state
        localStorage.setItem('token', response.access_token);
        localStorage.setItem('user', JSON.stringify(response.user));

        // Redirect based on role
        if (response.user.role === 'teacher') {
            window.location.href = 'teacher.html';
        } else {
            window.location.href = 'student.html';
        }

    } catch (error) {
        errorEl.textContent = error.message || 'Authentication failed. Please try again.';
        btn.disabled = false;
        btn.textContent = currentMode === 'login' ? 'Sign In' : 'Create Account';
    }
}

// Check if already logged in
window.onload = () => {
    const userStr = localStorage.getItem('user');
    if (userStr) {
        const user = JSON.parse(userStr);
        window.location.href = user.role === 'teacher' ? 'teacher.html' : 'student.html';
    }
};
