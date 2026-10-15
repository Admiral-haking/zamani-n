// ========================================
// ZAMANI API CONFIG - نسخه نهایی
// ========================================

function _detectApiBase() {
    const hostname = window.location.hostname || '';
    const isLocal = window.location.protocol === 'file:' || hostname === 'localhost' || hostname === '127.0.0.1';
    if (isLocal) return 'http://127.0.0.1:8000/api';
    return window.location.origin + '/api';
}

const API_URL = _detectApiBase();

// ========================================
// TOKEN MANAGEMENT
// ========================================

function getAccessToken() {
    return localStorage.getItem("access_token");
}

function getRefreshToken() {
    return localStorage.getItem("refresh_token");
}

function saveTokens(access, refresh = null) {
    localStorage.setItem("access_token", access);
    if (refresh) {
        localStorage.setItem("refresh_token", refresh);
    }
}

function clearTokens() {
    localStorage.removeItem("access_token");
    localStorage.removeItem("refresh_token");
}

// ========================================
// REFRESH TOKEN
// ========================================

async function refreshAccessToken() {
    const refresh = getRefreshToken();
    if (!refresh) {
        console.warn('❌ No refresh token available');
        return false;
    }

    try {
        const response = await fetch(`${API_URL}/accounts/refresh/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ refresh: refresh })
        });

        const data = await response.json();

        if (response.ok && data.access) {
            saveTokens(data.access, refresh);
            console.log('✅ Token refreshed successfully');
            return true;
        } else {
            console.error('❌ Refresh token failed:', data);
            clearTokens();
            if (!window.location.pathname.includes('log.html') && 
                !window.location.pathname.includes('index.html')) {
                window.location.href = 'log.html';
            }
            return false;
        }
    } catch (error) {
        console.error('❌ Refresh token error:', error);
        clearTokens();
        if (!window.location.pathname.includes('log.html') && 
            !window.location.pathname.includes('index.html')) {
            window.location.href = 'log.html';
        }
        return false;
    }
}

// ========================================
// API REQUEST
// ========================================

async function apiRequest(endpoint, options = {}) {
    let token = getAccessToken();
    
    const headers = { ...options.headers };

    // برای آپلود فایل (FormData) هدر Content-Type را مرورگر خودش تعیین می‌کند
    if (!(options.body instanceof FormData)) {
        headers["Content-Type"] = "application/json";
    }

    if (token) {
        headers["Authorization"] = `Bearer ${token}`;
    }

    try {
        const cleanEndpoint = endpoint.startsWith('/') ? endpoint : `/${endpoint}`;
        const url = `${API_URL}${cleanEndpoint}`;
        
        const response = await fetch(url, {
            ...options,
            headers
        });

        // اگر 401 بود، سعی کن توکن رو Refresh کنی
        if (response.status === 401) {
            console.warn('⚠️ Token expired, attempting refresh...');
            const refreshed = await refreshAccessToken();
            
            if (refreshed) {
                token = getAccessToken();
                headers["Authorization"] = `Bearer ${token}`;
                
                const retryResponse = await fetch(url, {
                    ...options,
                    headers
                });

                if (retryResponse.status === 204) {
                    return { success: true, status: 204, data: null };
                }

                const data = await retryResponse.json();
                return {
                    success: retryResponse.ok,
                    status: retryResponse.status,
                    data: data
                };
            } else {
                clearTokens();
                if (!window.location.pathname.includes('log.html') && 
                    !window.location.pathname.includes('index.html')) {
                    window.location.href = 'log.html';
                }
                return {
                    success: false,
                    status: 401,
                    data: { detail: 'Session expired. Please login again.' }
                };
            }
        }

        if (response.status === 204) {
            return { success: true, status: 204, data: null };
        }

        const data = await response.json();
        return {
            success: response.ok,
            status: response.status,
            data: data
        };

    } catch (error) {
        console.error("API Error:", error);
        return {
            success: false,
            status: 0,
            data: null,
            error: error.message
        };
    }
}

// ========================================
// GET
// ========================================

async function apiGet(endpoint) {
    return await apiRequest(endpoint, {
        method: "GET"
    });
}

// ========================================
// POST
// ========================================

async function apiPost(endpoint, body = {}) {
    return await apiRequest(endpoint, {
        method: "POST",
        body: JSON.stringify(body)
    });
}

// ========================================
// UPLOAD (Multipart / FormData)
// ========================================

async function apiUpload(endpoint, formData) {
    return await apiRequest(endpoint, {
        method: "POST",
        body: formData
    });
}

// ========================================
// PUT
// ========================================

async function apiPut(endpoint, body = {}) {
    return await apiRequest(endpoint, {
        method: "PUT",
        body: JSON.stringify(body)
    });
}

// ========================================
// PATCH
// ========================================

async function apiPatch(endpoint, body = {}) {
    return await apiRequest(endpoint, {
        method: "PATCH",
        body: JSON.stringify(body)
    });
}

// ========================================
// DELETE
// ========================================

async function apiDelete(endpoint) {
    return await apiRequest(endpoint, {
        method: "DELETE"
    });
}
