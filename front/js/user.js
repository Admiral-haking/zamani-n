// ========================================
// ZAMANI USER MANAGER - نسخه نهایی
// ========================================

// گرفتن اطلاعات کاربر فعلی
async function getCurrentUser() {
    const response = await apiGet("accounts/me/");
    console.log("CURRENT USER:", response);

    if (response.success) {
        return response.data;
    }

    if (response.status === 401) {
        clearTokens();
        if (!window.location.pathname.includes('log.html') && 
            !window.location.pathname.includes('index.html')) {
            window.location.href = 'log.html';
        }
    }

    return null;
}

// ========================================
// محافظت صفحات
// ========================================

function checkAuth() {
    const token = getAccessToken();
    if (!token) {
        const protectedPages = ['dashbord.html', 'monshi.html', 'pakhsh.html', 'cart.html'];
        const currentPage = window.location.pathname.split('/').pop();
        
        if (protectedPages.includes(currentPage)) {
            console.warn('⛔ دسترسی غیرمجاز، هدایت به صفحه لاگین');
            window.location.href = 'log.html';
        }
        return false;
    }
    return true;
}

// ========================================
// خروج کاربر
// ========================================

function logout() {
    clearTokens();
    window.location.href = "log.html";
}

// ========================================
// دریافت نقش کاربر
// ========================================

async function getUserRole() {
    const user = await getCurrentUser();
    return user?.role || null;
}

// ========================================
// بررسی آیا کاربر لاگین کرده
// ========================================

function isAuthenticated() {
    return getAccessToken() !== null;
}

// ========================================
// دریافت اطلاعات کامل کاربر با کش
// ========================================

let cachedUser = null;
let userCacheTime = 0;
const CACHE_DURATION = 60000;

async function getCachedUser(forceRefresh = false) {
    const now = Date.now();
    
    if (!forceRefresh && cachedUser && (now - userCacheTime) < CACHE_DURATION) {
        return cachedUser;
    }

    const user = await getCurrentUser();
    if (user) {
        cachedUser = user;
        userCacheTime = now;
    }
    
    return user;
}

// ========================================
// به‌روزرسانی اطلاعات کاربر در هدر
// ========================================

async function updateUserUI() {
    const user = await getCachedUser();
    if (!user) return;

    const usernameElements = document.querySelectorAll('.username-display');
    usernameElements.forEach(el => {
        el.textContent = user.username;
    });

    const roleElements = document.querySelectorAll('.role-display');
    roleElements.forEach(el => {
        el.textContent = getRoleLabel(user.role);
    });

    const avatarElements = document.querySelectorAll('.user-avatar');
    avatarElements.forEach(el => {
        const initial = user.username?.charAt(0)?.toUpperCase() || 'U';
        if (el.tagName !== 'IMG') {
            el.textContent = initial;
        }
    });
}

function getRoleLabel(role) {
    const roles = {
        'CUSTOMER': 'مشتری',
        'DISTRIBUTOR': 'توزیع‌کننده',
        'SECRETARY': 'منشی',
        'ADMIN': 'مدیر',
        'OWNER': 'صاحب شرکت'
    };
    return roles[role] || role || 'کاربر';
}