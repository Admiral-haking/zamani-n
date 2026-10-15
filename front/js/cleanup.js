// ========================================
// ZAMANI CLEANUP - حذف داده‌های قدیمی
// ========================================

(function cleanup() {
    console.log('🧹 شروع پاکسازی داده‌های قدیمی...');

    // کلیدهای قدیمی که باید حذف شوند
    // (هویت کاربری zamaniCurrentUser/zamaniUserLoggedIn عمداً نگه داشته می‌شود
    //  تا سایت مادر بتواند وضعیت لاگین و قیمت‌های اختصاصی مشتری را بشناسد)
    const oldKeys = [
        'zamaniRegisteredUsers'
    ];

    let removedCount = 0;
    oldKeys.forEach(key => {
        if (localStorage.getItem(key) !== null) {
            localStorage.removeItem(key);
            removedCount++;
            console.log(`🗑️ حذف شد: ${key}`);
        }
    });

    // بررسی اینکه آیا کلیدهای JWT وجود دارند
    const hasAccess = localStorage.getItem('access_token') !== null;
    const hasRefresh = localStorage.getItem('refresh_token') !== null;
    
    console.log(`🔑 Access Token: ${hasAccess ? '✅ موجود' : '❌ وجود ندارد'}`);
    console.log(`🔑 Refresh Token: ${hasRefresh ? '✅ موجود' : '❌ وجود ندارد'}`);
    
    console.log(`✅ پاکسازی کامل شد. ${removedCount} آیتم حذف شد.`);

    // اگر توکن وجود ندارد و در صفحه داشبورد هستیم، هدایت به لاگین
    if (!hasAccess && !window.location.pathname.includes('log.html') && 
        !window.location.pathname.includes('index.html')) {
        console.warn('⛔ توکن یافت نشد، هدایت به صفحه لاگین');
        window.location.href = 'log.html';
    }

    return {
        removedCount,
        hasAccess,
        hasRefresh
    };
})();