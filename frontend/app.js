/**
 * NGX Alpha Labs - Frontend Application Engine
 */

//const API_BASE_URL = "https://ainow-backend-2.onrender.com" //"http://localhost:8000/api";

// ❌ REMOVE THIS:
// const API_BASE_URL = "http://localhost:8000/api";

// ✅ REPLACE WITH THIS (Right at line 5 in app.js):
const API_BASE_URL = window.location.hostname === "localhost" || window.location.hostname === "127.0.0.1"
    ? "http://localhost:8000/api"
    : "https://ainow-backend-2.onrender.com/api";

// LocalStorage Auth Management
let currentUser = JSON.parse(localStorage.getItem('ngx_user')) || {
    name: "Luky Seun",
    email: "seun@firm.com",
    role: "Senior Equity Strategist"
};

// Initialize Application
document.addEventListener('DOMContentLoaded', () => {
    updateAuthUI();
    initializeCharts();
    fetchMarketSummary();
});

// ==========================================
// AUTHENTICATION UI & API HANDLERS
// ==========================================

function updateAuthUI() {
    const guestGroup = document.getElementById('auth-guest-group');
    const userGroup = document.getElementById('auth-user-group');
    const nameDisplay = document.getElementById('header-user-name');
    const roleDisplay = document.getElementById('header-user-role');
    const avatarImg = document.getElementById('header-avatar');

    if (currentUser) {
        if (guestGroup) guestGroup.classList.add('hidden');
        if (userGroup) {
            userGroup.classList.remove('hidden');
            userGroup.classList.add('flex');
        }
        if (nameDisplay) nameDisplay.innerText = currentUser.name;
        if (roleDisplay) roleDisplay.innerText = currentUser.role || 'Quant Analyst';
        if (avatarImg) avatarImg.src = `https://ui-avatars.com/api/?name=${encodeURIComponent(currentUser.name)}&background=10B981&color=fff`;
    } else {
        if (guestGroup) guestGroup.classList.remove('hidden');
        if (userGroup) {
            userGroup.classList.add('hidden');
            userGroup.classList.remove('flex');
        }
    }
}

async function handleLogin(event) {
    event.preventDefault();
    const email = document.getElementById('login-email').value;
    const password = document.getElementById('login-password').value;

    try {
        const response = await fetch(`${API_BASE_URL}/login`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email, password })
        });
        const data = await response.json();

        if (response.ok) {
            currentUser = data.user;
            localStorage.setItem('ngx_user', JSON.stringify(currentUser));
            updateAuthUI();
            closeLoginModal();
            showToast('Authentication Granted', `Welcome back, ${currentUser.name}`);
        } else {
            showToast('Authentication Error', data.detail || 'Failed to authenticate');
        }
    } catch (err) {
        // Fallback demo mode if backend server is not running
        currentUser = {
            name: email.split('@')[0].toUpperCase(),
            email: email,
            role: "Quantitative Analyst"
        };
        localStorage.setItem('ngx_user', JSON.stringify(currentUser));
        updateAuthUI();
        closeLoginModal();
        showToast('Offline Mode', `Authenticated locally as ${currentUser.name}`);
    }
}

async function handleSignup(event) {
    event.preventDefault();
    const name = document.getElementById('signup-name').value;
    const email = document.getElementById('signup-email').value;
    const password = document.getElementById('signup-password').value;

    try {
        const response = await fetch(`${API_BASE_URL}/signup`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ full_name: name, email, password })
        });
        const data = await response.json();

        if (response.ok) {
            currentUser = data.user;
            localStorage.setItem('ngx_user', JSON.stringify(currentUser));
            updateAuthUI();
            closeSignupModal();
            showToast('Account Created', `Institutional gateway unlocked for ${name}`);
        } else {
            showToast('Registration Error', data.detail || 'Sign up failed');
        }
    } catch (err) {
        currentUser = { name, email, role: "Registered Quant Member" };
        localStorage.setItem('ngx_user', JSON.stringify(currentUser));
        updateAuthUI();
        closeSignupModal();
        showToast('Account Created', `Registered locally as ${name}`);
    }
}

function handleLogout() {
    currentUser = null;
    localStorage.removeItem('ngx_user');
    updateAuthUI();
    showToast('Signed Out', 'You have been disconnected from the gateway.');
}

// Modal Toggle Functions
function openLoginModal() {
    document.getElementById('login-modal')?.classList.remove('hidden');
    document.getElementById('signup-modal')?.classList.add('hidden');
}
function closeLoginModal() { document.getElementById('login-modal')?.classList.add('hidden'); }
function openSignupModal() {
    document.getElementById('signup-modal')?.classList.remove('hidden');
    document.getElementById('login-modal')?.classList.add('hidden');
}
function closeSignupModal() { document.getElementById('signup-modal')?.classList.add('hidden'); }
function switchToSignup() { closeLoginModal(); openSignupModal(); }
function switchToLogin() { closeSignupModal(); openLoginModal(); }

// ==========================================
// API INSPECTOR & DATA FETCHING
// ==========================================

async function testEndpoint(method, endpoint) {
    const titleEl = document.getElementById('inspector-endpoint-title');
    const jsonEl = document.getElementById('inspector-json');
    if (titleEl) titleEl.innerText = `${method} ${endpoint}`;

    try {
        let payload = {};
        if (endpoint === '/signup') payload = { full_name: "Test Analyst", email: "test@firm.com", password: "password123" };
        if (endpoint === '/login') payload = { email: "seun@firm.com", password: "password123" };
        if (endpoint === '/predict') payload = { symbol: "MTNN" };

        const response = await fetch(`${API_BASE_URL}${endpoint}`, {
            method: method,
            headers: { 'Content-Type': 'application/json' },
            body: method === 'POST' ? JSON.stringify(payload) : null
        });

        const data = await response.json();
        if (jsonEl) jsonEl.innerText = JSON.stringify(data, null, 2);
        showToast('API Response', `Successfully invoked ${endpoint}`);
    } catch (err) {
        if (jsonEl) jsonEl.innerText = JSON.stringify({ error: "Backend server unreachable. Ensure main.py is running on port 8000." }, null, 2);
    }
}

async function fetchMarketSummary() {
    try {
        const res = await fetch(`${API_BASE_URL}/market-summary`);
        if (res.ok) {
            const data = await res.json();
            const statusEl = document.getElementById('api-status');
            if (statusEl) statusEl.innerHTML = `● REST Gateway Online (${data.asi} ASI)`;
        }
    } catch (e) {
        // Backend offline fallback UI
    }
}

// ==========================================
// CHARTS & NOTIFICATION TOASTS
// ==========================================

function initializeCharts() {
    const candleEl = document.querySelector("#candlestick-chart");
    if (candleEl) {
        const candleOptions = {
            series: [{
                data: [
                    { x: new Date('2026-07-18'), y: [233, 235, 228, 229] },
                    { x: new Date('2026-07-19'), y: [229, 233, 228, 231] },
                    { x: new Date('2026-07-20'), y: [231, 237, 230, 235] },
                    { x: new Date('2026-07-21'), y: [235, 238, 232, 236] },
                    { x: new Date('2026-07-22'), y: [236, 240, 234, 238] }
                ]
            }],
            chart: { type: 'candlestick', height: 280, toolbar: { show: false }, background: 'transparent' },
            theme: { mode: 'dark' }
        };
        new ApexCharts(candleEl, candleOptions).render();
    }

    const growthEl = document.querySelector("#portfolio-growth-chart");
    if (growthEl) {
        const growthOptions = {
            series: [{ name: 'NAV (M)', data: [420, 435, 448, 465, 482.5] }],
            chart: { type: 'area', height: 280, toolbar: { show: false }, background: 'transparent' },
            colors: ['#10B981'],
            theme: { mode: 'dark' }
        };
        new ApexCharts(growthEl, growthOptions).render();
    }
}

function showToast(title, message) {
    const container = document.getElementById('toast-container');
    if (!container) return;

    const toast = document.createElement('div');
    toast.className = 'glass p-4 rounded-xl shadow-xl border border-gray-700 flex items-start space-x-3 pointer-events-auto toast-enter max-w-sm';
    toast.innerHTML = `
        <div class="text-ngx-accent mt-0.5"><i class="fas fa-info-circle text-lg"></i></div>
        <div class="flex-1">
            <h4 class="text-xs font-bold text-white">${title}</h4>
            <p class="text-xs text-gray-300 mt-0.5">${message}</p>
        </div>
        <button onclick="this.parentElement.remove()" class="text-gray-500 hover:text-white"><i class="fas fa-times text-xs"></i></button>
    `;
    container.appendChild(toast);
    setTimeout(() => {
        toast.classList.remove('toast-enter');
        toast.classList.add('toast-exit');
        setTimeout(() => toast.remove(), 300);
    }, 3500);
}

function openApiInspector() { document.getElementById('api-inspector-modal')?.classList.remove('hidden'); }
function closeApiInspector() { document.getElementById('api-inspector-modal')?.classList.add('hidden'); }
function toggleTheme() {
    document.documentElement.classList.toggle('dark');
    document.documentElement.classList.toggle('light');
}